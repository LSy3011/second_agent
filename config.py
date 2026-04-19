import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass


def resolve_path(value, default):
    path = Path(os.getenv(value, default))
    return path if path.is_absolute() else BASE_DIR / path

NEO4J_URL = os.getenv("NEO4J_URL", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123456")

OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "qwen2.5:7b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "bge-m3:latest")

SOURCE_EMBEDDING_DIM = int(os.getenv("SOURCE_EMBEDDING_DIM", "1024"))
TARGET_EMBEDDING_DIM = int(os.getenv("TARGET_EMBEDDING_DIM", "1536"))

VECTOR_DB_PATH = resolve_path("VECTOR_DB_PATH", BASE_DIR / "my_agent_vector_padding")
TRACE_FILE = resolve_path("AGENT_TRACE_FILE", BASE_DIR / "agent_reasoning_traces.json")
SKILLS_DIR = resolve_path("SKILLS_DIR", BASE_DIR / "skills")
DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID", "padding_user_final")
