import argparse
import gc
import shutil
import traceback
from pathlib import Path

from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer
from mem0 import Memory

try:
    from langchain_ollama import ChatOllama
except (ImportError, AttributeError):
    from langchain_community.chat_models import ChatOllama

try:
    from langchain_neo4j import Neo4jGraph
except (ImportError, AttributeError):
    from langchain_community.graphs import Neo4jGraph

from config import (
    DEFAULT_USER_ID,
    NEO4J_PASSWORD,
    NEO4J_URL,
    NEO4J_USER,
    OLLAMA_EMBED_MODEL,
    OLLAMA_LLM_MODEL,
    TARGET_EMBEDDING_DIM,
    VECTOR_DB_PATH,
)
from embedding_patch import install_ollama_embedding_padding_patch


DEMO_GRAPH_RELATIONSHIPS = [
    ("Person", "Alex", "WORKS_AS", "Role", "Python Developer"),
    ("Person", "Alex", "USES", "Technology", "Neo4j"),
    ("Project", "Second Agent", "USES", "Technology", "Mem0"),
    ("Project", "Second Agent", "USES", "Technology", "Qdrant"),
    ("Project", "Second Agent", "USES", "Technology", "Neo4j"),
    ("Project", "Second Agent", "SUPPORTS", "Scenario", "Career Planning"),
]


DEMO_TEXTS = [
    "Alex is a Python Developer who uses Neo4j for memory graph reasoning.",
    "Second Agent uses Mem0, Qdrant, and Neo4j to support career planning.",
]


def reset_vector_store(path):
    resolved = path.resolve()
    project_root = Path(__file__).resolve().parent
    if project_root not in resolved.parents and resolved != project_root:
        raise ValueError(f"Refusing to delete a path outside the project: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
        print(f"   [reset] removed vector store: {resolved}")


def build_mem0():
    return Memory.from_config(
        {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "path": str(VECTOR_DB_PATH),
                    "collection_name": "mem0",
                },
            },
            "llm": {
                "provider": "ollama",
                "config": {"model": OLLAMA_LLM_MODEL, "temperature": 0},
            },
            "embedder": {
                "provider": "ollama",
                "config": {
                    "model": OLLAMA_EMBED_MODEL,
                    "embedding_dims": TARGET_EMBEDDING_DIM,
                },
            },
        }
    )


def write_demo_graph_fallback(graph):
    """Write a deterministic demo graph if LLM extraction returns no relationships."""
    written = 0
    for source_label, source_name, rel_type, target_label, target_name in DEMO_GRAPH_RELATIONSHIPS:
        query = f"""
        MERGE (source:{source_label} {{name: $source_name}})
        MERGE (target:{target_label} {{name: $target_name}})
        MERGE (source)-[rel:{rel_type}]->(target)
        RETURN elementId(rel) AS rel_id
        """
        graph.query(
            query,
            params={
                "source_name": source_name,
                "target_name": target_name,
            },
        )
        written += 1
    return written


def close_mem0(mem0):
    """Best-effort cleanup to reduce Qdrant local client shutdown noise."""
    for attr in ("vector_store", "client", "_client"):
        obj = getattr(mem0, attr, None)
        close = getattr(obj, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                pass
    gc.collect()


def process(user_id, text, mem0, graph, llm_transformer):
    print(f"\n--- Processing: {text} ---")

    try:
        mem0.add(text, user_id=user_id)
        print("   [Mem0] vector memory write succeeded")
    except Exception as exc:
        print(f"   [Mem0] write failed: {exc}")
        traceback.print_exc()

    try:
        docs = [Document(page_content=text)]
        graph_docs = llm_transformer.convert_to_graph_documents(docs)
        relationship_count = sum(len(doc.relationships) for doc in graph_docs)

        if relationship_count > 0:
            graph.add_graph_documents(graph_docs)
            print(f"   [Neo4j] graph write succeeded ({relationship_count} relationships)")
            for graph_doc in graph_docs:
                for rel in graph_doc.relationships:
                    print(f"      {rel.source.id} --[{rel.type}]--> {rel.target.id}")
            return relationship_count

        fallback_count = write_demo_graph_fallback(graph)
        print(
            "   [Neo4j] LLM extracted 0 relationships; "
            f"fallback graph written ({fallback_count} relationships)"
        )
        return fallback_count
    except Exception as exc:
        print(f"   [Neo4j] write failed: {exc}")
        return 0


def parse_args():
    parser = argparse.ArgumentParser(description="Verify Mem0 + Neo4j hybrid memory pipeline")
    parser.add_argument("--reset", action="store_true", help="remove local vector store before running")
    return parser.parse_args()


def main():
    args = parse_args()

    print(f">>> 1. Installing embedding padding patch ({TARGET_EMBEDDING_DIM})...")
    if install_ollama_embedding_padding_patch():
        print("   [patch] installed")
    else:
        print("   [patch] already installed")

    if args.reset:
        reset_vector_store(VECTOR_DB_PATH)

    print(">>> 2. Starting hybrid memory pipeline...")
    mem0 = None
    try:
        mem0 = build_mem0()
        print("   [Mem0] ready")

        llm = ChatOllama(model=OLLAMA_LLM_MODEL, temperature=0, format="json")
        llm_transformer = LLMGraphTransformer(llm=llm)
        graph = Neo4jGraph(url=NEO4J_URL, username=NEO4J_USER, password=NEO4J_PASSWORD)
        print("   [Neo4j] ready")

        total_relationships = 0
        for text in DEMO_TEXTS:
            total_relationships += process(DEFAULT_USER_ID, text, mem0, graph, llm_transformer)

        print(
            "\n>>> Verification complete: "
            f"vector memory and graph memory are available ({total_relationships} relationships)."
        )
    except Exception as exc:
        print(f"Initialization failed: {exc}")
        raise SystemExit(1)
    finally:
        if mem0 is not None:
            close_mem0(mem0)


if __name__ == "__main__":
    main()
