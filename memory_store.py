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


def _close_known_clients(obj, seen=None, depth=0):
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
        _close_known_clients(child, seen=seen, depth=depth + 1)

    try:
        members = vars(obj)
    except TypeError:
        members = {}

    for name, child in members.items():
        lowered = name.lower()
        if any(token in lowered for token in ("client", "qdrant", "vector", "store")):
            _close_known_clients(child, seen=seen, depth=depth + 1)


def close_memory():
    """Close cached local memory clients before interpreter shutdown."""
    try:
        memory = get_memory()
    except Exception:
        memory = None

    _close_known_clients(memory)
    get_memory.cache_clear()
