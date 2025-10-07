from langchain_huggingface import HuggingFaceEmbeddings

def get_embedding_model():
    """
    Initialize and return a HuggingFace embedding model.
    """
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
