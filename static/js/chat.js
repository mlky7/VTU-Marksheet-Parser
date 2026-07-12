document.addEventListener("DOMContentLoaded", () => {
  const panel = document.getElementById("chat-panel");
  const box = document.getElementById("chat-box");
  const fileInput = document.getElementById("chat-file-upload");
  const clearBtn = document.getElementById("chat-clear"); 

  // Toggle Chat
  document.getElementById("chat-toggle").addEventListener("click", () => {
    panel.classList.toggle("hidden");
    if (!panel.classList.contains("hidden") && !box.children.length) {
      append("Hi! You can upload your PDF directly here using the paperclip icon, then ask me anything about your marks.", "bot");
    }
  });

  // Close Chat
  document.getElementById("chat-close").addEventListener("click", () => panel.classList.add("hidden"));
  
  // Clear Chat Logic
  if (clearBtn) {
    clearBtn.addEventListener("click", async () => {
      box.innerHTML = ""; // Clear frontend DOM
      append("Chat memory cleared. What would you like to ask now?", "bot");
      try {
        await fetch("/clear_chat", { method: "POST" }); // Clear backend memory
      } catch (e) {
        console.error("Failed to clear backend memory");
      }
    });
  }

  // Submit Text Message
  document.getElementById("chat-form").addEventListener("submit", send);

  // Handle PDF Upload directly from chat
  if (fileInput) {
    fileInput.addEventListener("change", async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      append(`Uploading ${file.name}...`, "user");
      const typing = append("Processing PDF...", "bot", "typing");

      const formData = new FormData();
      formData.append("file", file);

      try {
        const response = await fetch("/upload", { method: "POST", body: formData });
        const data = await response.json();
        typing.remove();
        if (response.ok && !data.error) {
          append("✅ Marksheet processed! What would you like to know about your grades?", "bot");
        } else {
          append("❌ Upload failed: " + (data.error || "Could not read the PDF."), "bot");
        }
      } catch (err) {
        typing.remove();
        append("❌ Network error while uploading.", "bot");
      }
      e.target.value = '';
    });
  }
});

// Appends messages to the chat box with Tailwind styling and Markdown
function append(text, who, extra = "") {
  const box = document.getElementById("chat-box");
  const div = document.createElement("div");
  
  // Styling for User vs Bot messages
  const baseStyle = who === "user" 
    ? "bg-brand-100 text-brand-900 self-end rounded-l-lg rounded-tr-lg p-2.5 max-w-[85%] ml-auto" 
    : "bg-white border border-slate-200 text-slate-700 self-start rounded-r-lg rounded-tl-lg p-2.5 max-w-[85%]";
  
  // Added "prose prose-sm" so the markdown lists and bold text look beautiful
  div.className = `mb-3 text-sm flex flex-col prose prose-sm max-w-none ${baseStyle} ${extra}`;
  
  if (who === "bot" && extra === "typing") {
      // Modern bouncing dots animation using pure Tailwind CSS
      div.innerHTML = `
        <div class="flex space-x-1.5 h-5 items-center px-1">
          <div class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: -0.3s"></div>
          <div class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: -0.15s"></div>
          <div class="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
        </div>
      `;
  } else if (who === "bot" && typeof marked !== "undefined") {
      // Parse markdown for bot messages!
      div.innerHTML = marked.parse(text);
  } else {
      div.textContent = text; // Plain text for user messages
  }

  box.appendChild(div); 
  box.scrollTop = box.scrollHeight;
  return div;
}

// Sends text questions to the RAG backend
async function send(e) {
  e.preventDefault();
  const input = document.getElementById("chat-input");
  const btn = document.getElementById("chat-send");
  const msg = input.value.trim(); 
  
  if (!msg) return;

  append(msg, "user"); 
  input.value = ""; 
  btn.disabled = true;
  
  const typing = append("Thinking…", "bot", "typing");
  
  try {
    const r = await fetch("/chat", {
      method: "POST", 
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg })
    });
    const data = await r.json();
    
    typing.remove();
    append(data.response || data.error || "No response.", "bot");
  } catch (err) {
    typing.remove(); 
    append("Network error: " + err.message, "bot");
  } finally { 
    btn.disabled = false; 
    input.focus(); 
  }
}