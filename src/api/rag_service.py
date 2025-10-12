import os
import uuid
from typing import List, Tuple
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from src.ingest import load_pdf
from src.splitter import split_documents
from src.vectorstore import load_faiss, create_faiss, save_faiss
from src.api.deps import embeddings, session_dir, GLOBAL_DIR, llm

# helpers

def new_session_id() -> str:
    return uuid.uuid4().hex

def ensure_store(dir_path: str):
    emb = embeddings()
    store = load_faiss(emb, dir_path)
    return store

def _add_documents_to_store(store: FAISS, docs: List[Document], dir_path: str) -> int:
    # FAISS supports add_documents; then persist
    store.add_documents(docs)
    save_faiss(store, dir_path)
    return len(docs)

def build_or_update_store(dir_path: str, docs: List[Document]) -> Tuple[FAISS, int]:
    emb = embeddings()
    store = load_faiss(emb, dir_path)
    if store is None:
        store = create_faiss(docs, emb, dir_path)  # persists
        return store, len(docs)
    else:
        added = _add_documents_to_store(store, docs, dir_path)
        return store, added

def ingest_pdfs(paths: List[str], session_id: str) -> Tuple[str, int, List[str]]:
    # load -> split -> index/update
    all_docs = []
    file_names = []
    for p in paths:
        docs = load_pdf(p)  # 1 Document per page :contentReference[oaicite:8]{index=8}
        file_names.append(os.path.basename(p))
        all_docs.extend(docs)

    # chunking configs are from your splitter (1000/200) :contentReference[oaicite:9]{index=9}
    chunks = split_documents(all_docs)
    dir_path = session_dir(session_id)
    os.makedirs(dir_path, exist_ok=True)
    store, added = build_or_update_store(dir_path, chunks)
    return dir_path, added, file_names

def retrieve_answer(query: str, dir_path: str, k: int = 4):
    emb = embeddings()
    store = FAISS.load_local(dir_path, emb, allow_dangerous_deserialization=True)
    retriever = store.as_retriever(search_kwargs={"k": k})
    docs = retriever.get_relevant_documents(query)
    return docs

def format_sources(docs):
    out = []
    for d in docs:
        meta = d.metadata or {}
        out.append({
            "doc_name": meta.get("source") and os.path.basename(meta.get("source")),
            "page": meta.get("page"),
            "score": meta.get("score")
        })
    return out

def answer_with_llm(context: List[Document], query: str) -> str:
    # simple "stuff" prompt; langchain chain optional, but direct is fine
    system = (
        "You are a helpful RAG assistant. Use the provided context if available. "
        "If the answer isn't in the context, say so briefly and answer from your general knowledge."
    )
    ctx_text = "\n\n".join([d.page_content for d in context]) if context else ""
    prompt = f"{system}\n\nContext:\n{ctx_text}\n\nUser question: {query}\nAnswer:"
    return llm().invoke(prompt).content
