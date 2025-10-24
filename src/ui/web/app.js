document.addEventListener("DOMContentLoaded", () => {
  const $ = id => document.getElementById(id);

  // Elements
  const chatEl = $("chat");
  const filesEl = $("files");
  const btnUpload = $("btnUpload");
  const btnAsk = $("btnAsk");
  const qEl = $("q");
  const uploadStatusEl = $("uploadStatus");
  const topKEl = $("topK");
  const useGlobalEl = $("useGlobal");
  const sessionStatusEl = $("sessionStatus");
  const docCountEl = $("docCount");
  const fileListEl = $("fileList");
  const fileDropZone = $("fileDropZone");
  const mobileToggle = $("mobileToggle");
  const sidebar = document.querySelector(".sidebar");

  // Sanity check
  if (!chatEl || !filesEl || !btnUpload || !btnAsk || !qEl || !uploadStatusEl) {
    console.error("Some DOM elements not found. Check HTML IDs.");
    return;
  }

  let SESSION_ID = null;
  let uploadedDocsCount = 0;

  const API = window.location.origin.includes("localhost")
    ? "http://127.0.0.1:8000"
    : window.location.origin;

  // Mobile toggle
  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener("click", () => {
      sidebar.classList.toggle("active");
      mobileToggle.classList.toggle("active");
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener("click", (e) => {
      if (window.innerWidth <= 768) {
        if (!sidebar.contains(e.target) && !mobileToggle.contains(e.target) && sidebar.classList.contains("active")) {
          sidebar.classList.remove("active");
          mobileToggle.classList.remove("active");
        }
      }
    });
  }

  // Auto-resize textarea
  const autoResize = (textarea) => {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
  };

  qEl.addEventListener('input', () => autoResize(qEl));

  // Format file size
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  // Display selected files
  const displayFiles = (files) => {
    if (!files || files.length === 0) {
      fileListEl.classList.remove('show');
      fileListEl.innerHTML = '';
      return;
    }

    fileListEl.classList.add('show');
    fileListEl.innerHTML = '';
    
    Array.from(files).forEach(file => {
      const fileItem = document.createElement('div');
      fileItem.className = 'file-item';
      fileItem.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
        <span class="file-name" title="${file.name}">${file.name}</span>
        <span class="file-size">${formatFileSize(file.size)}</span>
      `;
      fileListEl.appendChild(fileItem);
    });
  };

  // File input handler
  filesEl.addEventListener('change', () => {
    displayFiles(filesEl.files);
  });

  // Drag and drop handlers
  if (fileDropZone) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      fileDropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
      });
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      fileDropZone.addEventListener(eventName, () => {
        fileDropZone.querySelector('.file-button').classList.add('drag-over');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      fileDropZone.addEventListener(eventName, () => {
        fileDropZone.querySelector('.file-button').classList.remove('drag-over');
      });
    });

    fileDropZone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      
      // Filter only PDF files
      const pdfFiles = Array.from(files).filter(file => 
        file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
      );
      
      if (pdfFiles.length > 0) {
        // Create a new FileList-like object
        const dataTransfer = new DataTransfer();
        pdfFiles.forEach(file => dataTransfer.items.add(file));
        filesEl.files = dataTransfer.files;
        displayFiles(filesEl.files);
      }
    });
  }

  // File input handler
  filesEl.addEventListener('change', () => {
    displayFiles(filesEl.files);
  });

  // Example prompt buttons
  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('example-btn') || e.target.closest('.example-btn')) {
      const btn = e.target.classList.contains('example-btn') ? e.target : e.target.closest('.example-btn');
      const prompt = btn.getAttribute('data-prompt');
      if (prompt) {
        qEl.value = prompt;
        autoResize(qEl);
        qEl.focus();
      }
    }
  });

  // Show status message
  const showStatus = (message, type = 'loading') => {
    uploadStatusEl.textContent = message;
    uploadStatusEl.className = 'upload-status show ' + type;
    setTimeout(() => {
      if (type !== 'loading') {
        uploadStatusEl.classList.remove('show');
      }
    }, 5000);
  };

  // Remove welcome message
  const removeWelcomeMessage = () => {
    const welcome = chatEl.querySelector('.welcome-container');
    if (welcome) {
      welcome.remove();
    }
  };

  // Add chat bubble
  const addBubble = (text, who = "bot") => {
    removeWelcomeMessage();
    const bubble = document.createElement("div");
    bubble.className = "bubble " + (who === "user" ? "user" : "bot");
    
    const content = document.createElement("div");
    content.className = "bubble-content";
    content.textContent = text;
    
    bubble.appendChild(content);
    chatEl.appendChild(bubble);
    chatEl.scrollTop = chatEl.scrollHeight;
  };

  // Update session status
  const updateSessionStatus = (status) => {
    if (sessionStatusEl) {
      sessionStatusEl.textContent = status;
    }
  };

  // Update document count
  const updateDocCount = (count) => {
    uploadedDocsCount = count;
    if (docCountEl) {
      docCountEl.textContent = count;
    }
  };

  // Upload PDFs
  btnUpload.onclick = async () => {
    const files = filesEl.files;
    if (!files || !files.length) {
      showStatus("Please select at least one PDF file", "error");
      return;
    }

    // Create session if needed
    if (!SESSION_ID) {
      try {
        showStatus("Creating session...", "loading");
        const res = await fetch(`${API}/sessions`, { method: "POST" });
        const data = await res.json();
        SESSION_ID = data.session_id;
        updateSessionStatus("Active");
      } catch (err) {
        console.error(err);
        showStatus("Failed to create session", "error");
        return;
      }
    }

    // Upload files
    showStatus("Uploading files...", "loading");
    let successCount = 0;
    let failCount = 0;

    for (const f of files) {
      const fd = new FormData();
      fd.append("files", f);
      fd.append("session_id", SESSION_ID);

      try {
        const r = await fetch(`${API}/upload`, { method: "POST", body: fd });
        const data = await r.json();
        
        if (data.files_ingested && data.files_ingested.length > 0) {
          successCount++;
          addBubble(`📄 Uploaded: ${data.files_ingested.join(", ")}`);
        }
      } catch (err) {
        console.error(err);
        failCount++;
        addBubble(`❌ Failed to upload: ${f.name}`);
      }
    }

    // Update status
    if (failCount === 0) {
      showStatus(`Successfully uploaded ${successCount} file${successCount > 1 ? 's' : ''}`, "success");
      updateDocCount(uploadedDocsCount + successCount);
    } else {
      showStatus(`Uploaded ${successCount}, failed ${failCount}`, "error");
    }

    // Clear file input
    filesEl.value = '';
    fileListEl.classList.remove('show');
    fileListEl.innerHTML = '';
  };

  // Ask a question
  const askQuestion = async () => {
    const question = qEl.value.trim();
    if (!question) return;

    qEl.value = "";
    autoResize(qEl);
    addBubble(question, "user");

    // Disable send button
    btnAsk.disabled = true;

    try {
      const r = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: question,
          session_id: SESSION_ID,
          top_k: parseInt(topKEl.value, 10),
          use_global: useGlobalEl.checked
        })
      });
      const data = await r.json();
      addBubble(data.answer || "No answer received", "bot");
    } catch (err) {
      console.error(err);
      addBubble("❌ Failed to get response. Please try again.", "bot");
    } finally {
      btnAsk.disabled = false;
    }
  };

  // Button click handler
  btnAsk.onclick = askQuestion;

  // Keyboard handler for textarea
  qEl.addEventListener("keydown", (e) => {
    // Enter without Shift = Send message
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      askQuestion();
    }
    // Shift+Enter = New line (default behavior, no need to handle)
  });

  // Initialize
  updateSessionStatus("Ready");
  updateDocCount(0);
});