/** ========= CONFIG / STATE ========= **/
const $ = (id)=>document.getElementById(id);
let API = $("apiBase").value.trim();
let SESSION_ID = null;

/** ========= UI HELPERS ========= **/
function setHealth(ok){
  $("health").textContent = "health: " + (ok ? "ok" : "down");
  $("health").className = "chip " + (ok ? "ok" : "bad");
}
function setSessionChip(){ $("sessionChip").textContent = "session: " + (SESSION_ID || "—"); }
function addBubble(text, who="bot", sources=[], mode=null){
  const chat = $("chat");
  const bubble = document.createElement("div");
  bubble.className = "bubble " + (who==="user" ? "user" : "bot");
  bubble.textContent = text;
  chat.appendChild(bubble);

  if (who!=="user" && (mode || (sources && sources.length))){
    const meta = document.createElement("div"); meta.className = "meta";
    if (mode) meta.innerHTML = `<strong>mode</strong>: ${mode}`;
    bubble.appendChild(meta);

    if (sources && sources.length){
      const box = document.createElement("div"); box.className="sources";
      sources.forEach(s=>{
        const label = [s.doc_name || "doc", s.page!=null?("p."+s.page):null].filter(Boolean).join(" · ");
        const chip = document.createElement("span"); chip.className="source"; chip.textContent = label;
        box.appendChild(chip);
      });
      bubble.appendChild(box);
    }
  }
  chat.scrollTop = chat.scrollHeight;
}

/** ========= API CALLS ========= **/
async function health(){
  try{
    const r = await fetch(`${API}/health`, {method:"GET"});
    setHealth(r.ok);
  }catch(e){ setHealth(false); }
}

async function createSession(){
  try{
    const r = await fetch(`${API}/sessions`, {method:"POST"});
    if(!r.ok) throw new Error(await r.text());
    const j = await r.json();
    SESSION_ID = j.session_id;
    setSessionChip();
    addBubble("✅ New session created.", "bot");
  }catch(e){
    addBubble("❌ Failed to create session. Check API Base & server logs.", "bot");
  }
}

async function deleteSession(){
  if(!SESSION_ID){ addBubble("No session to delete.", "bot"); return; }
  try{
    const r = await fetch(`${API}/sessions/${SESSION_ID}`, {method:"DELETE"});
    if(!r.ok) throw new Error(await r.text());
    SESSION_ID = null; setSessionChip();
    addBubble("🧹 Session deleted.", "bot");
  }catch(e){ addBubble("❌ Failed to delete session.", "bot"); }
}

async function uploadFiles(){
  const files = $("files").files;
  if(!files.length){ $("uploadStatus").textContent = "choose at least one PDF"; return; }
  if(!SESSION_ID){ await createSession(); }
  $("uploadStatus").textContent = "uploading…";

  for (const f of files){
    if(!f.name.toLowerCase().endsWith(".pdf")) { $("uploadStatus").textContent = `skip non-pdf: ${f.name}`; continue; }
    const fd = new FormData();
    fd.append("files", f);
    fd.append("session_id", SESSION_ID);
    try{
      const r = await fetch(`${API}/upload`, {method:"POST", body: fd});
      if(!r.ok){ throw new Error(await r.text()); }
      const j = await r.json();
      $("uploadStatus").textContent = `ingested: ${j.files_ingested.join(", ")} (+${j.chunks_added} chunks)`;
      addBubble(`📄 Ingested: ${j.files_ingested.join(", ")}`, "bot");
    }catch(e){
      $("uploadStatus").textContent = `error: ${f.name}`;
      addBubble(`❌ Upload failed for ${f.name}: ${e}`, "bot");
    }
  }
}

async function ask(){
  const q = $("q").value.trim();
  if(!q) return;
  $("q").value = "";
  addBubble(q, "user");

  const payload = {
    query: q,
    session_id: SESSION_ID, // can be null → backend answers with LLM-only
    top_k: parseInt($("topK").value, 10),
    use_global: $("useGlobal").checked
  };
  try{
    const r = await fetch(`${API}/chat`, {
      method:"POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(payload)
    });
    if(!r.ok){
      const text = await r.text();
      addBubble(`❌ ${r.status} ${r.statusText}\n${text}`, "bot");
      return;
    }
    const j = await r.json();
    addBubble(j.answer, "bot", j.sources || [], j.mode);
  }catch(e){
    addBubble("❌ Request failed. Is the API running?", "bot");
  }
}

/** ========= EVENTS ========= **/
$("btnPing").onclick = ()=>{ API = $("apiBase").value.trim() || API; health(); };
$("btnSession").onclick = createSession;
$("btnDelete").onclick = deleteSession;
$("btnUpload").onclick = uploadFiles;
$("btnAsk").onclick = ask;
$("apiBase").addEventListener("change", (e)=>{ API = e.target.value.trim(); });
$("q").addEventListener("keydown", (e)=>{ if(e.key==="Enter" && (e.ctrlKey||e.metaKey)){ $("btnAsk").click(); } });

/** ========= INIT ========= **/
(async function init(){
  await health();
  setSessionChip();
})();
