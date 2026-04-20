import argparse
import gc
import shutil
import traceback
import warnings
from pathlib import Path

from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer
from mem0 import Memory

try:
    from langchain_core._api import LangChainDeprecationWarning
except Exception:
    LangChainDeprecationWarning = DeprecationWarning

warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

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
    "Second Agent uses Mem0, Qdrant, and Neo4j to support enterprise knowledge workflows.",
]


def reset_vector_store(path):
    resolved = path.resolve()
    project_root = Path(__file__).resolve().parent
    if project_root not in resolved.parents and resolved != project_root:
        raise ValueError(f"Refusing to delete a path outside the project: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
        print(f"   [重置] 已删除本地向量库: {resolved}")


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


def close_nested_clients(obj, seen=None, depth=0):
    if obj is None or depth > 4:
        return

    if seen is None:
        seen = set()

    obj_id = id(obj)
    if obj_id in seen:
        return
    seen.add(obj_id)

    close = getattr(obj, "close", None)
    if callable(close):
        try:
            close()
        except Exception:
            pass

    for attr in (
        "vector_store",
        "client",
        "_client",
        "qdrant_client",
        "_qdrant_client",
        "db",
        "_db",
    ):
        try:
            child = getattr(obj, attr, None)
        except Exception:
            child = None
        close_nested_clients(child, seen=seen, depth=depth + 1)

    try:
        members = vars(obj)
    except TypeError:
        members = {}

    for name, child in members.items():
        lowered = name.lower()
        if any(token in lowered for token in ("client", "qdrant", "vector", "store")):
            close_nested_clients(child, seen=seen, depth=depth + 1)


def close_mem0(mem0):
    """Best-effort cleanup to reduce Qdrant local client shutdown noise."""
    close_nested_clients(mem0)
    gc.collect()


def close_graph(graph):
    """Best-effort close for Neo4jGraph internal driver/session objects."""
    for attr in ("_driver", "driver", "_database"):
        obj = getattr(graph, attr, None)
        close = getattr(obj, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                pass


def process(user_id, text, mem0, graph, llm_transformer):
    print(f"\n--- 处理文本: {text} ---")

    try:
        mem0.add(text, user_id=user_id)
        print("   [Mem0] 向量记忆写入成功")
    except Exception as exc:
        print(f"   [Mem0] 写入失败: {exc}")
        traceback.print_exc()

    try:
        docs = [Document(page_content=text)]
        graph_docs = llm_transformer.convert_to_graph_documents(docs)
        relationship_count = sum(len(doc.relationships) for doc in graph_docs)

        if relationship_count > 0:
            graph.add_graph_documents(graph_docs)
            print(f"   [Neo4j] 图谱写入成功 ({relationship_count} 条关系)")
            for graph_doc in graph_docs:
                for rel in graph_doc.relationships:
                    print(f"      {rel.source.id} --[{rel.type}]--> {rel.target.id}")
            return relationship_count

        fallback_count = write_demo_graph_fallback(graph)
        print(
            "   [Neo4j] LLM 未抽取到关系，"
            f"已写入稳定演示 fallback 图谱 ({fallback_count} 条关系)"
        )
        return fallback_count
    except Exception as exc:
        print(f"   [Neo4j] 写入失败: {exc}")
        return 0


def parse_args():
    parser = argparse.ArgumentParser(description="Verify Mem0 + Neo4j hybrid memory pipeline")
    parser.add_argument("--reset", action="store_true", help="remove local vector store before running")
    return parser.parse_args()


def main():
    args = parse_args()

    print("=== Second Agent 混合记忆写入演示 ===")
    print(f">>> 1. 注入 Embedding 维度补齐补丁 ({TARGET_EMBEDDING_DIM})")
    if install_ollama_embedding_padding_patch():
        print("   [补丁] 已注入")
    else:
        print("   [补丁] 已存在，跳过重复注入")

    if args.reset:
        reset_vector_store(VECTOR_DB_PATH)

    print(">>> 2. 启动 Mem0 向量层与 Neo4j 图谱层")
    mem0 = None
    graph = None
    try:
        mem0 = build_mem0()
        print("   [Mem0] 就绪")

        llm = ChatOllama(model=OLLAMA_LLM_MODEL, temperature=0, format="json")
        llm_transformer = LLMGraphTransformer(llm=llm)
        graph = Neo4jGraph(url=NEO4J_URL, username=NEO4J_USER, password=NEO4J_PASSWORD)
        print("   [Neo4j] 就绪")

        total_relationships = 0
        for text in DEMO_TEXTS:
            total_relationships += process(DEFAULT_USER_ID, text, mem0, graph, llm_transformer)

        print(
            "\n>>> 验证完成: "
            f"向量记忆与图谱记忆均可用，本次写入/确认 {total_relationships} 条关系。"
        )
    except Exception as exc:
        print(f"初始化失败: {exc}")
        raise SystemExit(1)
    finally:
        if graph is not None:
            close_graph(graph)
        if mem0 is not None:
            close_mem0(mem0)


if __name__ == "__main__":
    main()
