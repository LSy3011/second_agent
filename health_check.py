import importlib.util
import json

import ollama

from config import (
    NEO4J_PASSWORD,
    NEO4J_URL,
    NEO4J_USER,
    OLLAMA_EMBED_MODEL,
    OLLAMA_LLM_MODEL,
    SKILLS_DIR,
    VECTOR_DB_PATH,
)


def check_import(module_name):
    return importlib.util.find_spec(module_name) is not None


def check_ollama_models():
    try:
        response = ollama.list()
        raw_models = response.get("models", []) if isinstance(response, dict) else getattr(response, "models", [])
        names = set()
        for model in raw_models:
            if isinstance(model, dict):
                names.add(model.get("name") or model.get("model"))
            else:
                names.add(getattr(model, "name", None) or getattr(model, "model", None))
        names.discard(None)
        return {
            "ok": True,
            "models": sorted(names),
            "has_llm": OLLAMA_LLM_MODEL in names,
            "has_embedding": OLLAMA_EMBED_MODEL in names,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def check_neo4j():
    try:
        from neo4j import GraphDatabase

        with GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver:
            driver.verify_connectivity()
        return {"ok": True, "url": NEO4J_URL}
    except Exception as exc:
        return {"ok": False, "url": NEO4J_URL, "error": str(exc)}


def main():
    checks = {
        "paths": {
            "vector_db_path": str(VECTOR_DB_PATH),
            "vector_db_exists": VECTOR_DB_PATH.exists(),
            "skills_dir": str(SKILLS_DIR),
            "skills_dir_exists": SKILLS_DIR.exists(),
            "skills": sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir()) if SKILLS_DIR.exists() else [],
        },
        "imports": {
            "mem0": check_import("mem0"),
            "neo4j": check_import("neo4j"),
            "qdrant_client": check_import("qdrant_client"),
            "langchain": check_import("langchain"),
            "dotenv": check_import("dotenv"),
        },
        "ollama": check_ollama_models(),
        "neo4j": check_neo4j(),
    }
    print(json.dumps(checks, ensure_ascii=False, indent=2))

    critical_ok = (
        checks["imports"]["mem0"]
        and checks["imports"]["neo4j"]
        and checks["paths"]["skills_dir_exists"]
        and checks["ollama"]["ok"]
        and checks["ollama"].get("has_llm", False)
        and checks["ollama"].get("has_embedding", False)
        and checks["neo4j"]["ok"]
    )
    raise SystemExit(0 if critical_ok else 1)


if __name__ == "__main__":
    main()
