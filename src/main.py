from vectorstore import create_faiss, load_faiss
from qa_chain import build_qa_chain
from embed import get_embedding_model
from splitter import split_documents
from ingest import load_pdf
import os

def main():
    pdf_path = "data/document.pdf"
    persist_dir = "faiss_db"

    # 1️⃣ Load + Split
    docs = load_pdf(pdf_path)
    print(f"✅ Loaded {len(docs)} pages from {pdf_path}")
    chunks = split_documents(docs)
    print(f"✅ Split into {len(chunks)} chunks")

    # 2️⃣ Embeddings
    embedding_model = get_embedding_model()
    print("✅ Embedding model ready")

    # 3️⃣ Create or load FAISS
    store = load_faiss(embedding_model, persist_dir)
    if store is None:
        store = create_faiss(chunks, embedding_model, persist_dir)
    print(f"✅ FAISS vectorstore ready at '{persist_dir}'")

    # 4️⃣ QA Chain
    qa_chain = build_qa_chain()
    print("✅ QA Chain initialized")

    print("\n💬 Ask me something about your document (type 'exit' to quit):\n")
    while True:
        query = input("You: ").strip()
        if query.lower() in {"exit", "quit"}:
            print("👋 Goodbye!")
            break

        try:
            result = qa_chain.invoke({"query": query})
            answer = result.get("result") or result.get("output_text") or str(result)
            print("\n🤖 Assistant:", answer, "\n")
        except Exception as e:
            import traceback
            print("❌ Error:", e)
            traceback.print_exc()

if __name__ == "__main__":
    main()
