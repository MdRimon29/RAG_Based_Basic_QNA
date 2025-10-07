from fastapi import FastAPI, UploadFile
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os, shutil

load_dotenv()

PDF_FOLDER = "data"
DEFAULT_PDF_PATH = os.path.join(PDF_FOLDER, "Medical_Words_Reference.pdf")
VECTOR_PATH = "faiss_index"

os.makedirs(PDF_FOLDER, exist_ok=True)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
llm = ChatGroq(model="openai/gpt-oss-120b")

qa = None
default_qa = None


def create_vectorstore(pdf_path: str):
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    vectordb = FAISS.from_documents(chunks, embeddings)
    vectordb.save_local(VECTOR_PATH)
    return vectordb

from langchain.prompts import PromptTemplate

def build_qa_from_pdf(pdf_path: str):
    vectordb = create_vectorstore(pdf_path)
    retriever = vectordb.as_retriever(search_kwargs={"k": 4})

    prompt = PromptTemplate(
        template=(
            "You are a helpful assistant. "
            "Answer the user's question briefly and clearly in one or two sentences. "
            "Do not include sources or extra newlines. "
            "If the question is simple (like general knowledge), reply shortly.\n\n"
            "Context:\n{context}\n\n"
            "Question: {question}\n\n"
            "Answer:"
        ),
        input_variables=["context", "question"],
    )

    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=False,
        chain_type_kwargs={"prompt": prompt}
    )


def build_qa_from_pdf(pdf_path: str):
    vectordb = create_vectorstore(pdf_path)
    retriever = vectordb.as_retriever(search_kwargs={"k": 4})
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=False
    )


# ✅ Modern lifespan startup handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    global default_qa
    if os.path.exists(DEFAULT_PDF_PATH):
        print("Loading default PDF:", DEFAULT_PDF_PATH)
        default_qa = build_qa_from_pdf(DEFAULT_PDF_PATH)
        print("✅ Default PDF loaded successfully!")
    else:
        print("⚠️ Default PDF not found at:", DEFAULT_PDF_PATH)

    # yield control back to FastAPI runtime
    yield

app = FastAPI(title="RAG PDF Q&A API", lifespan=lifespan)


@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile):
    global qa
    save_path = os.path.join(PDF_FOLDER, file.filename)
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    qa = build_qa_from_pdf(save_path)
    return {"message": f"✅ '{file.filename}' uploaded and processed successfully!"}


class Question(BaseModel):
    query: str


import re

def clean_answer(text: str) -> str:
    # Remove markdown bold/italic and extra spaces/newlines
    text = re.sub(r"[*_#>`~]+", "", text)
    text = text.replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text

@app.post("/ask")
async def ask_uploaded_pdf(question: Question):
    global qa
    if qa is None:
        return {"error": "⚠️ No uploaded PDF found. Please upload one first at /upload_pdf."}

    result = qa.invoke({"query": question.query})
    answer = clean_answer(result["result"])
    return {"answer": answer}


@app.post("/ask_default")
async def ask_default_pdf(question: Question):
    global default_qa
    if default_qa is None:
        return {"error": "⚠️ Default PDF not loaded. Ensure 'data/document.pdf' exists."}

    result = default_qa.invoke({"query": question.query})
    answer = clean_answer(result["result"])
    return {"answer": answer}
