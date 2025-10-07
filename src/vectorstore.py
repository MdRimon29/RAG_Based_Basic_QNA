# vectorstore.py
from langchain_community.vectorstores import FAISS
import os
import pickle

def save_faiss(store, persist_directory="faiss_db"):
    """Persist FAISS index + metadata to disk."""
    if not os.path.exists(persist_directory):
        os.makedirs(persist_directory)
    store.save_local(persist_directory)
    print(f"💾 FAISS vectorstore saved at '{persist_directory}'")

def load_faiss(embedding_model, persist_directory="faiss_db"):
    """Load a saved FAISS index."""
    if os.path.exists(os.path.join(persist_directory, "index.faiss")):
        print(f"📂 Loading existing FAISS index from '{persist_directory}'")
        return FAISS.load_local(persist_directory, embedding_model, allow_dangerous_deserialization=True)
    else:
        print("⚠️ No existing FAISS index found, returning None.")
        return None

def create_faiss(chunks, embedding_model, persist_directory="faiss_db"):
    """Create a FAISS index from chunks and persist it."""
    print("🧱 Creating new FAISS index...")
    store = FAISS.from_documents(chunks, embedding_model)
    save_faiss(store, persist_directory)
    return store
