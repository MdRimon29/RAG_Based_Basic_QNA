# Load your retriever (from retriever.py)
# Connect it to an LLM (like ChatGroq, ChatOpenAI, etc.)
# Build a Retrieval-QA Chain

# qa_chain.py
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from retriever import get_retriever
from embed import get_embedding_model
from dotenv import load_dotenv
import os

# Always load .env from project root
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)
print("🔑 GROQ_API_KEY loaded:", bool(os.getenv("GROQ_API_KEY")))

def build_qa_chain():
    """Build and return the QA chain."""
    embedding_model = get_embedding_model()
    retriever = get_retriever("faiss_db", embedding_model)

    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    print("✅ Groq LLM loaded")

    template = """You are a helpful assistant. Use the context below to answer.
If unsure, say you don’t know.

Context:
{context}

Question:
{question}

Answer:
"""
    prompt = PromptTemplate(template=template, input_variables=["context", "question"])

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=False,
    )
    return qa_chain

