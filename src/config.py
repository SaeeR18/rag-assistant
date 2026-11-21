import os
from pathlib import Path
from dotenv import load_dotenv

# Read secrets from the .env file
load_dotenv()

# ---------- Paths ----------
BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "data" / "docs"
CHROMA_DIR = BASE_DIR / "chroma_db"

# ---------- Secrets ----------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ---------- Models ----------
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-3.5-flash-lite")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ---------- Settings we will experiment with in Phase 5 ----------
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 800))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 100))
TOP_K = int(os.getenv("TOP_K", 4))

# ---------- Database ----------
COLLECTION_NAME = "cloud_docs"


if __name__ == "__main__":
    # Quick self-check. Never prints the key itself.
    print("Base folder    :", BASE_DIR)
    print("Docs folder    :", DOCS_DIR, "| exists:", DOCS_DIR.exists())
    print("Chroma folder  :", CHROMA_DIR)
    print("API key found  :", bool(GOOGLE_API_KEY))
    print("Chat model     :", CHAT_MODEL)
    print("Embedding model:", EMBEDDING_MODEL)
    print("Chunk size     :", CHUNK_SIZE)
    print("Chunk overlap  :", CHUNK_OVERLAP)
    print("Top-k          :", TOP_K)