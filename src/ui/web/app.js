document.addEventListener("DOMContentLoaded", () => {
  const $ = id => document.getElementById(id);

  // Safe check for elements
  const chatEl = $("chat");
  const filesEl = $("files");
  const btnUpload = $("btnUpload");
  const btnAsk = $("btnAsk");
  const qEl = $("q");
  const uploadStatusEl = $("uploadStatus");
  const sessionChipEl = $("sessionChip");
  const topKEl = $("topK");
  const useGlobalEl = $("useGlobal");

  if (!chatEl || !filesEl || !btnUpload || !btnAsk || !qEl || !uploadStatusEl || !sessionChipEl) {
    console.error("Some DOM elements not found. Check HTML IDs.");
    return;
  }

  let SESSION_ID = null;

  const API = window.location.origin.includes("localhost") 
    ? "http://127.0.0.1:8000" 
    : window.location.origin;

  const addBubble = (text, who="bot") => {
    const bubble = document.createElement("div");
    bubble.className = "bubble " + (who==="user"?"user":"bot");
    bubble.textContent = text;
    chatEl.appendChild(bubble);
    chatEl.scrollTop = chatEl.scrollHeight;
  };

  btnUpload.onclick = async () => {
    const files = filesEl.files;
    if (!files || !files.length) return uploadStatusEl.textContent="Choose at least 1 PDF";

    if (!SESSION_ID) {
      try {
        const res = await fetch(`${API}/sessions`, {method:"POST"});
        const data = await res.json();
        SESSION_ID = data.session_id;
        sessionChipEl.textContent = SESSION_ID;
      } catch(err) {
        console.error(err);
        uploadStatusEl.textContent = "Failed to create session";
        return;
      }
    }

    uploadStatusEl.textContent="Uploading…";
    for (const f of files) {
      const fd = new FormData();
      fd.append("files", f);
      fd.append("session_id", SESSION_ID);

      try {
        const r = await fetch(`${API}/upload`, {method:"POST", body:fd});
        const data = await r.json();
        uploadStatusEl.textContent = `Ingested: ${data.files_ingested.join(", ")}`;
        addBubble(`📄 Ingested: ${data.files_ingested.join(", ")}`);
      } catch(err) {
        console.error(err);
        uploadStatusEl.textContent=`Error: ${f.name}`;
        addBubble(`❌ Upload failed: ${f.name}`);
      }
    }
  };

  btnAsk.onclick = async () => {
    const question = qEl.value.trim();
    if (!question) return;
    qEl.value="";
    addBubble(question,"user");

    try {
      const r = await fetch(`${API}/chat`, {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
          query: question,
          session_id: SESSION_ID,
          top_k: parseInt(topKEl.value,10),
          use_global: useGlobalEl.checked
        })
      });
      const data = await r.json();
      addBubble(data.answer || "No answer","bot");
    } catch(err) {
      console.error(err);
      addBubble("❌ API request failed","bot");
    }
  };

  qEl.addEventListener("keydown", (e) => {
    if (e.key==="Enter" && (e.ctrlKey||e.metaKey)) btnAsk.click();
  });
});
