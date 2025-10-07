# splitter.py

from langchain.text_splitter import RecursiveCharacterTextSplitter

def split_documents(documents):
    """
    Split documents into smaller chunks for embedding and retrieval.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,      # characters per chunk
        chunk_overlap=200,    # overlap between chunks
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    return chunks