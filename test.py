# src/test_modular.p
from langchain.chains import RetrievalQA
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain_core.llms import OpenAI
from langchain_core.embeddings import OpenAIEmbeddings
from langchain_core.vectorstores import FAISS

# Minimal test to ensure imports work
print("✅ All modern LangChain imports are working!")
