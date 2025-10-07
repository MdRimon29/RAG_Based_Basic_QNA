from ingest import load_pdf
from splitter import split_documents
from embed import get_embedding_model
from vectorstore import create_faiss, load_faiss
from qa_chain import build_qa_chain
import os

def main():
    pdf_path = "data/document.pdf"
    persist_dir = "faiss_db"

    # Load and process PDF
    documents = load_pdf(pdf_path)
    chunks = split_documents(documents)
    embeddings = get_embedding_model()

    # Load or create FAISS vectorstore
    store = load_faiss(embeddings, persist_dir)
    if store is None:
        store = create_faiss(chunks, embeddings, persist_dir)

    # Build QA system
    qa_chain = build_qa_chain(persist_dir)
    print("Document loaded. Chatbot ready.\n")

    while True:
        query = input("Q: ").strip()
        if query.lower() in {"exit", "quit"}:
            print("Session ended.")
            break
        try:
            result = qa_chain.invoke({"query": query})
            print("A:", result.get("result", ""))
            print()
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    main()