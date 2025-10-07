# document ingestion layer

from langchain_community.document_loaders import PyPDFLoader

def load_pdf(path: str):
    """
    Load a single PDF file and return a list of LangChain Document objects.

    Args:
        path (str): Path to the PDF file.

    Returns:
        List[Document]: One Document per page of the PDF.
    """
    loader = PyPDFLoader(path)
    documents = loader.load()
    return documents