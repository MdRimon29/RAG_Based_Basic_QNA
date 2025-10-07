from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

print("🔑 Testing Groq model…")
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

try:
    result = llm.invoke("Say hello, Groq!")
    print("🧠 Groq response:", result)
except Exception as e:
    import traceback
    print("❌ Error talking to Groq:", e)
    traceback.print_exc()
