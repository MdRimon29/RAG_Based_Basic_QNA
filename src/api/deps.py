import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from src.embed import get_embedding_model  # reuse your embedding model
from functools import lru_cache

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(ROOT, "faiss_db")
UPLOADS_DIR = os.path.join(ROOT, "uploads")
GLOBAL_DIR = os.path.join(DATA_DIR, "global")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

load_dotenv(os.path.join(ROOT, ".env"))

@lru_cache(maxsize=1)
def embeddings():
    # from embed.py: all-MiniLM-L6-v2
    return get_embedding_model()

@lru_cache(maxsize=1)
def llm():
    # fast/cheap reasoning for RAG answering
    return ChatGroq(model="llama-3.1-8b-instant", temperature=0)

def session_dir(session_id: str) -> str:
    return os.path.join(DATA_DIR, session_id)
