import os, requests, streamlit as st

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")

st.set_page_config(page_title="Chat with your pdf file", layout="centered")
st.title("PDF Chatbot")

if "session_id" not in st.session_state:
    # create a session
    r = requests.post(f"{API_BASE}/sessions")
    r.raise_for_status()
    st.session_state.session_id = r.json()["session_id"]

st.caption(f"Session: {st.session_state.session_id}")

with st.expander("📄 Upload PDFs", expanded=True):
    files = st.file_uploader("Select one or more PDFs", type=["pdf"], accept_multiple_files=True)
    if st.button("Upload", disabled=not files):
        uploaded = []
        for f in files:
            files_param = {"files": (f.name, f.getvalue(), "application/pdf")}
            data = {"session_id": st.session_state.session_id}
            r = requests.post(f"{API_BASE}/upload", files=files_param, data=data)
            r.raise_for_status()
            res = r.json()
            uploaded.extend(res["files_ingested"])
        st.success(f"Uploaded: {', '.join(uploaded)}")

st.divider()
query = st.text_input("Ask anything (with or without PDFs)")
col1, col2 = st.columns(2)
with col1:
    top_k = st.slider("Top-K", 1, 10, 4)
with col2:
    use_global = st.checkbox("Also search global index", value=True)

if st.button("Ask") and query.strip():
    payload = {
        "query": query,
        "session_id": st.session_state.session_id,
        "top_k": top_k,
        "use_global": use_global
    }
    r = requests.post(f"{API_BASE}/chat", json=payload)
    r.raise_for_status()
    res = r.json()
    st.markdown(f"**Mode:** `{res['mode']}`")
    st.write(res["answer"])
    if res.get("sources"):
        st.divider()
        st.subheader("Sources")
        for s in res["sources"]:
            st.write(f"- {s.get('doc_name')} (page {s.get('page')})")
