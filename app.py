import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

# Settings
PDF_PATH = "data/document.pdf"
VECTOR_PATH = "faiss_index"

@st.cache_resource
def load_vectorstore():
    # 1. Load and split PDF
    loader = PyPDFLoader(PDF_PATH)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    # 2. Embeddings
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 3. Create / Load FAISS DB
    if os.path.exists(VECTOR_PATH):
        vectordb = FAISS.load_local(VECTOR_PATH, embeddings, allow_dangerous_deserialization=True)
    else:
        vectordb = FAISS.from_documents(documents=chunks, embedding=embeddings)
        vectordb.save_local(VECTOR_PATH)

    return vectordb

# Load FAISS index
vectordb = load_vectorstore()

# Groq LLM
llm = ChatGroq(model="openai/gpt-oss-120b")

# RetrievalQA
retriever = vectordb.as_retriever(search_kwargs={"k": 4})
qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True
)

# Streamlit UI
st.title("📚 RAG Chat with Your Document")
st.markdown("Ask questions about a research paper PDF named 'Attention is All You Need' below 👇")

query = st.text_input("Enter your question:")

if query:
    with st.spinner("Thinking..."):
        result = qa.invoke({"query": query})

    st.subheader("Answer")
    st.write(result["result"])

    with st.expander("Sources"):
        for doc in result["source_documents"]:
            st.markdown(f"- **Page {doc.metadata.get('page')}**: {doc.page_content[:200]}...")
