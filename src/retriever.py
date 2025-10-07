# create a retriever — an object that knows how to search and fetch the most relevant chunks from your vector database (e.g., ChromaDB) when the user asks a question.

# retriever.py
from langchain_community.vectorstores import FAISS
import os

def get_retriever(persist_directory, embedding_model, k=3):
    """Return a retriever from FAISS vectorstore."""
    if not os.path.exists(os.path.join(persist_directory, "index.faiss")):
        raise FileNotFoundError(f"❌ FAISS index not found in {persist_directory}")
    
    print(f"📚 Loading FAISS retriever from '{persist_directory}'")
    store = FAISS.load_local(persist_directory, embedding_model, allow_dangerous_deserialization=True)
    return store.as_retriever(search_kwargs={"k": k})
