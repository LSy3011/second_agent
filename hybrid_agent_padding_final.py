import os
import shutil
import logging
from mem0 import Memory
from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.graphs import Neo4jGraph
from langchain_community.chat_models import ChatOllama
from mem0.embeddings.ollama import OllamaEmbedding

# ================= 1. 💉 修复版：维度填充补丁 =================

print(">>> 1. 注入维度填充补丁 (1024 -> 1536)...")

# 保存原始方法
original_embed = OllamaEmbedding.embed

# 🔧 修复点：加上 *args 和 **kwargs，不管 Mem0 传多少个参数，全收下！
def patched_embed(self, text, *args, **kwargs):
    # 1. 调用原始方法 (把所有参数都透传过去)
    try:
        vector = original_embed(self, text, *args, **kwargs)
    except TypeError:
        # 万一原始方法也不支持多参数，就只传 text
        vector = original_embed(self, text)
    
    # 2. 维度填充逻辑 (Padding)
    target_dim = 1536 # 伪装成 OpenAI 的维度
    current_dim = len(vector)
    
    if current_dim < target_dim:
        pad_width = target_dim - current_dim
        # 补 0.0
        padded_vector = vector + [0.0] * pad_width
        return padded_vector
    
    return vector

# 应用补丁
OllamaEmbedding.embed = patched_embed
print("   ✅ 补丁已应用：支持多参数调用。")

# ================= 2. 配置与清理 =================

NEO4J_URL = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password123456"
VECTOR_DB_PATH = "./my_agent_vector_padding"

# 清理旧数据，保证全新开始
if os.path.exists(VECTOR_DB_PATH):
    shutil.rmtree(VECTOR_DB_PATH)

# ================= 3. 启动 Agent =================

print(">>> 2. 启动混合记忆 Agent...")

try:
    # A. 初始化 Mem0
    # 我们故意设置 embedding_dims 为 1536，配合我们的补丁
    mem0 = Memory.from_config({
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "path": VECTOR_DB_PATH,
                "collection_name": "mem0"
            }
        },
        "llm": {
            "provider": "ollama",
            "config": {"model": "qwen2.5:7b", "temperature": 0}
        },
        "embedder": {
            "provider": "ollama",
            "config": {
                "model": "bge-m3:latest",
                "embedding_dims": 1536 
            }
        }
    })
    print("   ✅ Mem0 (向量层) 就绪")

    # B. 初始化 LangChain
    llm = ChatOllama(model="qwen2.5:7b", temperature=0, format="json")
    llm_transformer = LLMGraphTransformer(llm=llm)
    graph = Neo4jGraph(url=NEO4J_URL, username=NEO4J_USER, password=NEO4J_PASSWORD)
    print("   ✅ LangChain + Neo4j (图谱层) 就绪")

except Exception as e:
    print(f"❌ 初始化报错: {e}")
    exit()

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
