import os
import logging
from mem0 import Memory

# ================= 🔧 开启调试日志 (关键) =================
# 这会把所有隐藏的报错都打印出来
logging.basicConfig(level=logging.DEBUG)

# Neo4j 配置
neo4j_config = {
    "provider": "neo4j",
    "config": {
        "url": "bolt://localhost:7687",
        "username": "neo4j",
        "password": "password123456"
    }
}

# LLM 配置
llm_config = {
    "provider": "ollama",
    "config": {
        "model": "qwen2.5:7b",
        "temperature": 0.1,
        "max_tokens": 2000, # 给大一点空间
        "top_p": 0.1        # 让模型更严谨，便于输出 JSON
    }
}

# Embedding 配置
embedder_config = {
    "provider": "ollama",
    "config": {
        "model": "bge-m3:latest",
        "embedding_dims": 1024
    }
}

def main():
    print(">>> 1. 初始化引擎...")
    m = Memory.from_config({
        "graph_store": neo4j_config,
        "llm": llm_config,
        "embedder": embedder_config,
        "version": "v1.1"
    })

    user_id = "debug_user_001"
    text = "User is a software engineer. User likes Python."

    print(f"\n>>> 2. 尝试写入 Neo4j (User: {user_id})...")
    print(f"   输入文本: {text}")
    
    # 这一步会触发大量的 DEBUG 日志
    m.add(text, user_id=user_id)
    
    print("\n>>> 3. 写入操作完成，请检查上方的 DEBUG 日志中是否有 'Error' 字样")

if __name__ == "__main__":
    main()
