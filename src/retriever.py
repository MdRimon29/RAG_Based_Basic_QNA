# create a retriever — an object that knows how to search and fetch the most relevant chunks from your vector database (e.g., ChromaDB) when the user asks a question.

from langchain_community.vectorstores import FAISS
import os

def get_retriever(persist_directory, embedding_model, k=3):
    """Return a retriever for FAISS vectorstore."""
    path = os.path.join(persist_directory, "index.faiss")

    if not os.path.exists(path):
        raise FileNotFoundError(f"FAISS index not found at {persist_directory}")
    
    store = FAISS.load_local(persist_directory, embedding_model, allow_dangerous_deserialization=True)
    
    return store.as_retriever(search_kwargs={"k": k})