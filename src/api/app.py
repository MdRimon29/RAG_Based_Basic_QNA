import os, shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from src.api.models import SessionCreateResponse, UploadResponse, ChatRequest, ChatResponse, Source
from src.api.deps import UPLOADS_DIR, GLOBAL_DIR, session_dir
from src.api import rag_service as rag

app = FastAPI(title="Project-1 RAG API", version="1.0.0")

# CORS – update for your domain(s)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # lock down in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/sessions", response_model=SessionCreateResponse)
def create_session():
    sid = rag.new_session_id()
    os.makedirs(session_dir(sid), exist_ok=True)
    os.makedirs(os.path.join(UPLOADS_DIR, sid), exist_ok=True)
    return SessionCreateResponse(session_id=sid)

@app.post("/upload", response_model=UploadResponse)
async def upload_files(
    files: List[UploadFile] = File(...),
    session_id: Optional[str] = Form(None)
):
    if not files:
        raise HTTPException(400, "No files uploaded")

    if session_id is None:
        sid = rag.new_session_id()
    else:
        sid = session_id

    upload_dir = os.path.join(UPLOADS_DIR, sid)
    os.makedirs(upload_dir, exist_ok=True)

    paths = []
    for f in files:
        # simple extension guard
        if not f.filename.lower().endswith(".pdf"):
            raise HTTPException(400, f"Only PDF accepted: {f.filename}")
        dest = os.path.join(upload_dir, f.filename)
        with open(dest, "wb") as out:
            out.write(await f.read())
        paths.append(dest)

    _, added, names = rag.ingest_pdfs(paths, sid)
    return UploadResponse(session_id=sid, files_ingested=names, chunks_added=added)

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # prefer session store; optionally combine with global store
    docs = []
    mode = "llm_only"

    # session RAG
    if req.session_id:
        sdir = session_dir(req.session_id)
        if os.path.exists(os.path.join(sdir, "index.faiss")):
            docs = rag.retrieve_answer(req.query, sdir, k=req.top_k)
            mode = "session_rag"

    # if no session docs OR we also want global
    if req.use_global and os.path.exists(os.path.join(GLOBAL_DIR, "index.faiss")):
        global_docs = rag.retrieve_answer(req.query, GLOBAL_DIR, k=req.top_k)
        # simple blend: prefer session docs first
        if mode == "session_rag":
            docs = (docs or []) + global_docs
        else:
            docs = global_docs
            mode = "global_rag" if global_docs else mode

    answer = rag.answer_with_llm(docs, req.query)
    sources = rag.format_sources(docs)
    return ChatResponse(answer=answer, sources=[Source(**s) for s in sources], mode=mode)

@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    sdir = session_dir(session_id)
    udir = os.path.join(UPLOADS_DIR, session_id)
    for d in [sdir, udir]:
        if os.path.exists(d):
            shutil.rmtree(d)
    return {"deleted": session_id}

from fastapi.staticfiles import StaticFiles

# Serve the static website at /web/
app.mount("/web", StaticFiles(directory="src/ui/web", html=True), name="web")
