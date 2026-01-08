import os
from mem0 import Memory
import qdrant_client

# ================= 配置区域 =================
# 还是用你期望的配置，看看它到底听不听话
VECTOR_STORAGE_PATH = "./my_agent_vector_db"
COLLECTION_NAME = "agent_mem_1024"

print(">>> 🕵️‍♂️ [v2] 开始侦查 Mem0 的真实连接状态...")

try:
    # 1. 初始化 Mem0
    mem0 = Memory.from_config({
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "path": VECTOR_STORAGE_PATH,
                "collection_name": COLLECTION_NAME
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
                "embedding_dims": 1024
            }
        }
    })
    print("✅ Mem0 对象初始化成功")

    # 2. 深入刺探 (Introspection)
    if not hasattr(mem0, 'vector_store'):
        print("❌ 无法找到 vector_store 属性")
        exit()
        
    vs = mem0.vector_store
    print(f"\n[证据 1] 向量存储对象类型: {type(vs)}")
    
    # 获取底层的 QdrantClient
    if hasattr(vs, 'client'):
        real_client = vs.client
        print(f"[证据 2] 真实的 QdrantClient 对象: {real_client}")
        
        # 3. 挖掘物理存储路径
        # QdrantClient(python版) 内部通常有个 _client 属性存储连接信息 (SyncApis)
        # SyncApis -> _client (QdrantClient) -> _init_args 等等
        
        # 我们尝试打印出 client 的连接参数
        # 不同的 qdrant-client 版本结构不同，我们暴力打印它的属性
        print(f"\n[证据 3] 🕵️‍♂️ 深度挖掘连接参数:")
        
        # 尝试方案 A: 查 _client 属性
        if hasattr(real_client, "_client"):
            inner = real_client._client
            # 检查是否是内存模式
            if hasattr(inner, "location"): # 有些版本叫 location
                print(f"   -> location: {inner.location}")
            if hasattr(inner, "path"): # 有些版本叫 path
                print(f"   -> path: {inner.path}")
            if hasattr(inner, "url"):
                print(f"   -> url: {inner.url}")
        
        # 尝试方案 B: 查 _init_options (如果有)
        if hasattr(real_client, "_init_options"):
             print(f"   -> init_options: {real_client._init_options}")

        # 4. 遍历所有集合，查看维度 (最关键)
        print(f"\n[证据 4] 数据库中现存的所有集合:")
        try:
            # 获取所有集合列表
            cols_resp = real_client.get_collections()
            collections = cols_resp.collections
            
            if not collections:
                print("   (空数据库，没有集合)")
            
            for col in collections:
                name = col.name
                # 获取集合详情
                info = real_client.get_collection(name)
                dim = info.config.params.vectors.size
                
                print(f"   -----------------------------")
                print(f"   - 集合名称: '{name}'")
                print(f"     维度: {dim}")
                
                if dim == 1536:
                    print("     ❌ 状态: 这是一个 1536 维的集合 (OpenAI 默认)")
                    print("     ⚠️ 结论: Mem0 正在用这个集合，导致了报错！")
                elif dim == 1024:
                    print("     ✅ 状态: 这是正确的 1024 维集合 (BGE-M3)")
                else:
                    print(f"     ❓ 状态: 未知维度")
                    
        except Exception as e:
            print(f"   无法读取集合信息: {e}")

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"❌ 侦查过程中发生错误: {e}")
