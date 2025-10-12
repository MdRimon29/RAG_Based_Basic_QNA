from pydantic import BaseModel, Field
from typing import Optional, List

class SessionCreateResponse(BaseModel):
    session_id: str

class UploadResponse(BaseModel):
    session_id: str
    files_ingested: List[str] = Field(default_factory=list)
    chunks_added: int

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None    # if omitted: use global or LLM-only
    top_k: int = 4
    use_global: bool = True             # also search faiss_db/global if present

class Source(BaseModel):
    doc_name: Optional[str] = None
    page: Optional[int] = None
    score: Optional[float] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[Source] = Field(default_factory=list)
    mode: str  # "session_rag" | "global_rag" | "llm_only"
