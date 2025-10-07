from langchain_community.vectorstores import FAISS
import os

def save_faiss(store, persist_directory="faiss_db"):
    """Save FAISS vectorstore to disk."""
    os.makedirs(persist_directory, exist_ok=True)
    store.save_local(persist_directory)

def load_faiss(embedding_model, persist_directory="faiss_db"):
    """Load FAISS vectorstore if it exists."""
    path = os.path.join(persist_directory, "index.faiss")
    if os.path.exists(path):
        return FAISS.load_local(persist_directory, embedding_model, allow_dangerous_deserialization=True)
    return None

def create_faiss(chunks, embedding_model, persist_directory="faiss_db"):
    """Create and save FAISS index."""
    store = FAISS.from_documents(chunks, embedding_model)
    save_faiss(store, persist_directory)
    return store