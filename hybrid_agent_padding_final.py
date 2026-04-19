import os
import shutil
import logging
import argparse
from pathlib import Path
from mem0 import Memory
from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.graphs import Neo4jGraph
from langchain_community.chat_models import ChatOllama
from config import (
    NEO4J_PASSWORD,
    NEO4J_URL,
    NEO4J_USER,
    OLLAMA_EMBED_MODEL,
    OLLAMA_LLM_MODEL,
    TARGET_EMBEDDING_DIM,
    VECTOR_DB_PATH,
)
from embedding_patch import install_ollama_embedding_padding_patch

# ================= 1. 💉 修复版：维度填充补丁 =================

# ================= 2. 配置与清理 =================

def reset_vector_store(path):
    resolved = path.resolve()
    project_root = Path(__file__).resolve().parent
    if project_root not in resolved.parents and resolved != project_root:
        raise ValueError(f"拒绝删除项目目录外的路径: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
        print(f"   🧹 已清理向量库: {resolved}")

parser = argparse.ArgumentParser(description="验证 Mem0 + Neo4j 混合记忆链路")
parser.add_argument("--reset", action="store_true", help="运行前清理本地向量库")
args = parser.parse_args()

print(f">>> 1. 注入维度填充补丁 ({TARGET_EMBEDDING_DIM})...")
if install_ollama_embedding_padding_patch():
    print("   ✅ 补丁已应用：支持多参数调用和维度补齐。")
else:
    print("   ✅ 补丁已存在，跳过重复注入。")

if args.reset:
    reset_vector_store(VECTOR_DB_PATH)

# ================= 3. 启动 Agent =================

print(">>> 2. 启动混合记忆 Agent...")

try:
    # A. 初始化 Mem0
    # 我们故意设置 embedding_dims 为 1536，配合我们的补丁
    mem0 = Memory.from_config({
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "path": str(VECTOR_DB_PATH),
                "collection_name": "mem0"
            }
        },
        "llm": {
            "provider": "ollama",
            "config": {"model": OLLAMA_LLM_MODEL, "temperature": 0}
        },
        "embedder": {
            "provider": "ollama",
            "config": {
                "model": OLLAMA_EMBED_MODEL,
                "embedding_dims": TARGET_EMBEDDING_DIM
            }
        }
    })
    print("   ✅ Mem0 (向量层) 就绪")

    # B. 初始化 LangChain
    llm = ChatOllama(model=OLLAMA_LLM_MODEL, temperature=0, format="json")
    llm_transformer = LLMGraphTransformer(llm=llm)
    graph = Neo4jGraph(url=NEO4J_URL, username=NEO4J_USER, password=NEO4J_PASSWORD)
    print("   ✅ LangChain + Neo4j (图谱层) 就绪")

except Exception as e:
    print(f"❌ 初始化报错: {e}")
    raise SystemExit(1)

# ================= 4. 执行写入测试 =================

def process(user_id, text):
    print(f"\n--- 处理: {text} ---")
    
    # 1. 向量写入
    try:
        mem0.add(text, user_id=user_id)
        # 如果这里成功，说明参数传递问题和维度问题都解决了
        print("   ✅ [Mem0] 向量写入成功")
    except Exception as e:
        print(f"   ❌ [Mem0] 失败: {e}")
        import traceback
        traceback.print_exc()

    # 2. 图谱写入
    try:
        docs = [Document(page_content=text)]
        g_docs = llm_transformer.convert_to_graph_documents(docs)
        if g_docs:
            graph.add_graph_documents(g_docs)
            print(f"   ✅ [Neo4j] 图谱写入成功 ({len(g_docs[0].relationships)} 关系)")
            for r in g_docs[0].relationships:
                print(f"      🔗 {r.source.id} --[{r.type}]--> {r.target.id}")
    except Exception as e:
        print(f"   ❌ [Neo4j] 失败: {e}")

if __name__ == "__main__":
    process("padding_user_final", "Alex works as a Python Developer.")
    process("padding_user_final", "Alex loves Neo4j.")
    print("\n>>> 🎉 验证完成！这次一定行！")
