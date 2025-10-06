from fastapi import FastAPI, UploadFile, Form
from pydantic import BaseModel
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
import shutil

load_dotenv()

app = FastAPI(title="RAG PDF QA API")

PDF_PATH = "data/document.pdf"
VECTOR_PATH = "faiss_index"

# Embeddings + LLM (loaded once at startup)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
llm = ChatGroq(model="openai/gpt-oss-120b")

# Global QA object
qa = None


def build_vectorstore(pdf_path: str):
    """Load, split, and build FAISS index from PDF"""
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    vectordb = FAISS.from_documents(documents=chunks, embedding=embeddings)
    vectordb.save_local(VECTOR_PATH)
    return vectordb


def load_or_create_vectorstore():
    if os.path.exists(VECTOR_PATH):
        return FAISS.load_local(VECTOR_PATH, embeddings, allow_dangerous_deserialization=True)
    else:
        return build_vectorstore(PDF_PATH)


@app.on_event("startup")
def startup_event():
    global qa
    vectordb = load_or_create_vectorstore()
    retriever = vectordb.as_retriever(search_kwargs={"k": 4})
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )


class Question(BaseModel):
    query: str


@app.post("/ask")
async def ask_question(question: Question):
    """Ask a question about the loaded PDF"""
    result = qa.invoke({"query": question.query})

    return {
        "answer": result["result"],
        "sources": [
            {"page": doc.metadata.get("page"), "content": doc.page_content[:200]}
            for doc in result["source_documents"]
        ]
    }


@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile):
    """Upload a new PDF and rebuild vectorstore"""
    global qa

    save_path = f"data/{file.filename}"
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    vectordb = build_vectorstore(save_path)
    retriever = vectordb.as_retriever(search_kwargs={"k": 4})
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )

    return {"message": f"Uploaded and processed {file.filename}"}