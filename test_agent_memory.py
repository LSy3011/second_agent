import os
import logging
import ollama  # 必须导入这个库
from mem0 import Memory
from config import (
    NEO4J_PASSWORD,
    NEO4J_URL,
    NEO4J_USER,
    OLLAMA_EMBED_MODEL,
    OLLAMA_LLM_MODEL,
    SOURCE_EMBEDDING_DIM,
)

# ================= 🔧 开启调试日志 =================
logging.basicConfig(level=logging.INFO) # 降噪，只看关键信息

# ================= 💉 注入猴子补丁 (Monkey Patch) =================
#这是高级技巧：强制拦截 Mem0 对 Ollama 的调用，并塞入 format='json'
# 这样 Qwen 就不得不输出 JSON，哪怕 Mem0 的配置里没写这个参数。
original_client_chat = ollama.Client.chat

def patched_chat(self, *args, **kwargs):
    # 强制开启 JSON 模式
    kwargs['format'] = 'json' 
    # 降低温度，让它更理性
    if 'options' not in kwargs:
        kwargs['options'] = {}
    kwargs['options']['temperature'] = 0
    
    return original_client_chat(self, *args, **kwargs)

# 应用补丁
ollama.Client.chat = patched_chat
print(">>> 💉 已注入 JSON 强制模式补丁")

# ================= 1. 配置区域 =================

# Neo4j 配置
neo4j_config = {
    "provider": "neo4j",
    "config": {
        "url": NEO4J_URL,
        "username": NEO4J_USER,
        "password": NEO4J_PASSWORD,
    }
}

# LLM 配置 (注意：这里把 format 删掉了，因为我们已经在补丁里强制加了)
llm_config = {
    "provider": "ollama",
    "config": {
        "model": OLLAMA_LLM_MODEL,
        "temperature": 0,
        "top_p": 0.1
    }
}

# Embedding 配置
embedder_config = {
    "provider": "ollama",
    "config": {
        "model": OLLAMA_EMBED_MODEL,
        "embedding_dims": SOURCE_EMBEDDING_DIM,
    }
}

# ================= 2. 核心逻辑 =================

def main():
    print(">>> 1. 初始化引擎...")
    try:
        m = Memory.from_config({
            "graph_store": neo4j_config,
            "llm": llm_config,
            "embedder": embedder_config,
            "version": "v1.1"
        })
        print("✅ 引擎初始化成功！")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return

    # 模拟用户
    user_id = "final_test_user"
    
    # 使用极简的英文输入，确保 7B 模型能听懂
    # (中文有时候会让 JSON 结构崩坏，先用英文跑通流程)
    user_inputs = [
        "User is a senior python developer.",
        "User likes graph databases.",
        "User is studying AI agents."
    ]

    print(f"\n>>> 2. [存入] 正在写入 Neo4j (User: {user_id})...")
    for text in user_inputs:
        print(f"   正在处理: '{text}'")
        m.add(text, user_id=user_id)
    
    print("✅ 写入完成！")

    # --- 验证环节 ---
    print(f"\n>>> 3. [查询] 正在检索图谱记忆...")
    # 获取所有记忆
    response = m.get_all(user_id=user_id)
    
    # 打印结果
    if isinstance(response, dict):
        results = response.get("results", [])
    else:
        results = response

    if not results:
        print("⚠️ 警告：Python 没查到数据 (可能是向量检索空了)")
    else:
        for mem in results:
             print(f"🔹 {mem.get('memory', str(mem))}")

if __name__ == "__main__":
    main()
