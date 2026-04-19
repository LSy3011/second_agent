from functools import lru_cache

from mem0 import Memory

from config import (
    OLLAMA_EMBED_MODEL,
    OLLAMA_LLM_MODEL,
    TARGET_EMBEDDING_DIM,
    VECTOR_DB_PATH,
)
from embedding_patch import install_ollama_embedding_padding_patch


@lru_cache(maxsize=1)
def get_memory():
    install_ollama_embedding_padding_patch()
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


def search_memory(query, user_id=None, limit=5):
    memory = get_memory()
    kwargs = {}
    if user_id:
        kwargs["user_id"] = user_id

    if hasattr(memory, "search"):
        result = memory.search(query, **kwargs)
    else:
        result = memory.get_all(**kwargs)

    items = result.get("results", result) if isinstance(result, dict) else result
    if not isinstance(items, list):
        items = [items]

    normalized = []
    for item in items[:limit]:
        if isinstance(item, dict):
            text = item.get("memory") or item.get("text") or item.get("content") or str(item)
            score = item.get("score")
        else:
            text = str(item)
            score = None
        normalized.append({"memory": text, "score": score})
    return normalized
