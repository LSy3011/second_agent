import argparse
from difflib import SequenceMatcher

from config import NEO4J_PASSWORD, NEO4J_URL, NEO4J_USER


class MemoryOptimizer:
    def __init__(self, uri, user, password):
        from neo4j import GraphDatabase

        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def list_entities(self, limit=500):
        query = """
        MATCH (n)
        WITH n, labels(n) AS labels
        WHERE size(labels) > 0
        RETURN coalesce(n.id, n.name, n.title, n.text, toString(id(n))) AS entity_id,
               labels[0] AS label,
               elementId(n) AS element_id
        LIMIT $limit
        """
        with self.driver.session() as session:
            records = session.run(query, limit=limit)
            return [
                {
                    "id": record["entity_id"],
                    "label": record["label"],
                    "element_id": record["element_id"],
                }
                for record in records
                if record["entity_id"]
            ]

    @staticmethod
    def _normalize(value):
        return "".join(ch.lower() for ch in str(value) if ch.isalnum())

    def find_similar_entities(self, threshold=0.86, limit=500, max_pairs=20):
        entities = self.list_entities(limit=limit)
        candidates = []

        for idx, left in enumerate(entities):
            left_norm = self._normalize(left["id"])
            if not left_norm:
                continue
            for right in entities[idx + 1:]:
                right_norm = self._normalize(right["id"])
                if not right_norm or left_norm == right_norm:
                    continue
                score = SequenceMatcher(None, left_norm, right_norm).ratio()
                if score >= threshold:
                    candidates.append(
                        {
                            "left": left,
                            "right": right,
                            "score": round(score, 4),
                        }
                    )

        candidates.sort(key=lambda item: item["score"], reverse=True)
        return candidates[:max_pairs]

    def merge_pair(self, left_element_id, right_element_id):
        query = """
        MATCH (left), (right)
        WHERE elementId(left) = $left_element_id
          AND elementId(right) = $right_element_id
        WITH [left, right] AS nodes
        CALL apoc.refactor.mergeNodes(nodes, {properties: 'combine', mergeRels: true})
        YIELD node
        RETURN coalesce(node.id, node.name, node.title, toString(id(node))) AS merged_id,
               labels(node) AS labels
        """
        with self.driver.session() as session:
            record = session.run(
                query,
                left_element_id=left_element_id,
                right_element_id=right_element_id,
            ).single()
            return dict(record) if record else None

    def merge_similar_entities(self, threshold=0.86, limit=500, max_pairs=20, execute=False):
        candidates = self.find_similar_entities(
            threshold=threshold,
            limit=limit,
            max_pairs=max_pairs,
        )

        result = {
            "mode": "execute" if execute else "dry_run",
            "threshold": threshold,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "merged": [],
        }

        if not execute:
            return result

        for candidate in candidates:
            merged = self.merge_pair(
                candidate["left"]["element_id"],
                candidate["right"]["element_id"],
            )
            result["merged"].append(
                {
                    "left": candidate["left"]["id"],
                    "right": candidate["right"]["id"],
                    "score": candidate["score"],
                    "merged": merged,
                }
            )
        return result

    def analyze_paths(self, start_node, end_node):
        query = """
        MATCH (a), (b)
        WHERE coalesce(a.id, a.name, a.title, toString(id(a))) = $start
          AND coalesce(b.id, b.name, b.title, toString(id(b))) = $end
        MATCH p = shortestPath((a)-[*..3]-(b))
        RETURN [node IN nodes(p) | coalesce(node.id, node.name, node.title, toString(id(node)))] AS nodes,
               [rel IN relationships(p) | type(rel)] AS rels
        LIMIT 1
        """
        with self.driver.session() as session:
            record = session.run(query, start=start_node, end=end_node).single()
            if not record:
                return {
                    "start": start_node,
                    "end": end_node,
                    "path_found": False,
                    "message": "未找到 3 跳内路径",
                }
            return {
                "start": start_node,
                "end": end_node,
                "path_found": True,
                "nodes": record["nodes"],
                "relationships": record["rels"],
            }


def main():
    parser = argparse.ArgumentParser(description="Neo4j memory graph optimizer")
    parser.add_argument("--threshold", type=float, default=0.86)
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--max-pairs", type=int, default=20)
    parser.add_argument("--execute", action="store_true", help="真正执行 APOC mergeNodes；默认只 dry-run")
    parser.add_argument("--path", nargs=2, metavar=("START", "END"), help="分析两个实体之间的最短路径")
    args = parser.parse_args()

    optimizer = MemoryOptimizer(NEO4J_URL, NEO4J_USER, NEO4J_PASSWORD)
    try:
        if args.path:
            print(optimizer.analyze_paths(args.path[0], args.path[1]))
            return

        result = optimizer.merge_similar_entities(
            threshold=args.threshold,
            limit=args.limit,
            max_pairs=args.max_pairs,
            execute=args.execute,
        )
        print(result)
    finally:
        optimizer.close()


if __name__ == "__main__":
    main()
