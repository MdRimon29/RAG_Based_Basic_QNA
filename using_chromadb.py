from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

# 1. Settings
PDF_PATH = "data/document.pdf"
VECTOR_PATH = "faiss_index"

# 2. Load and split PDF
loader = PyPDFLoader(PDF_PATH)
docs = loader.load()
print(f"Loaded {len(docs)} pages from PDF.")

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(docs)
print(f"Split into {len(chunks)} chunks.")

# 3. Embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# 4. Create FAISS DB
vectordb = FAISS.from_documents(documents=chunks, embedding=embeddings)
vectordb.save_local(VECTOR_PATH)
print("Vector DB created.")

# 5. Groq LLM
llm = ChatGroq(model="llama-3.1-8b-instant")

# 6. RetrievalQA chain
retriever = vectordb.as_retriever(search_kwargs={"k": 4})
qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True
)
print("RetrievalQA chain ready.")

# 7. Interactive Q&A loop
print("\n RAG system ready! Ask questions about your document.")
print("Type 'exit' to quit.\n")

while True:
    query = input("Q: ")
    if query.lower() in ["exit", "quit"]:
        break

    result = qa.invoke({"query": query})
    print("\nA:", result["result"])
    print("\nSources:")
    for doc in result["source_documents"]:
        print(f" - Page {doc.metadata.get('page')}: {doc.page_content[:120]}...")
    print("\n" + "-"*50 + "\n")