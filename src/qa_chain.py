# Load your retriever (from retriever.py)
# Connect it to an LLM (like ChatGroq, ChatOpenAI, etc.)
# Build a Retrieval-QA Chain

from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from retriever import get_retriever
from embed import get_embedding_model
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

def build_qa_chain(persist_dir="faiss_db"):
    """Build and return a QA chain using FAISS retriever."""
    embedding_model = get_embedding_model()
    retriever = get_retriever(persist_dir, embedding_model)
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

    template = """
    You are an intelligent and helpful AI assistant designed to provide accurate, reliable, and natural responses.

    Your primary goal is to answer questions based on the provided context.
    If the context is relevant to the question, use it to produce a clear, well-structured answer.
    If the context does not contain the answer, rely on your general knowledge to respond accurately and naturally.
    If neither context nor general knowledge provides a valid answer, say "I don't know."

    You should:
    - Use plain text only (no bullet points, tables, or markdown formatting).
    - Respond naturally, like a human in conversation (e.g., if greeted, respond casually).
    - Provide concise answers when appropriate, but be detailed when necessary.
    - Avoid hallucination and never make up facts.
    - Be able to answer general world questions as well (e.g., “What is the capital of Bangladesh?”).
    - When summarizing or explaining content from the PDF, keep it precise and clear.
    - When unsure, politely express uncertainty.

    Context (from documents):
    {context}

    Question:
    {question}

    Answer:
    """


    prompt = PromptTemplate(template=template, input_variables=["context", "question"])

    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=False,
    )