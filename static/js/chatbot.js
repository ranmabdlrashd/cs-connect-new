/**
 * CS Connect Chatbot - Professional Frontend Logic
 * Connects to the Flask/Groq backend and handles premium UI interactions.
 */

// ── Globals ───────────────────────────────────────────────────────────
let isChatOpen = false;

// ── Toggle Logic ──────────────────────────────────────────────────────
function toggleFloatingChat() {
    const windowEl = document.getElementById("floatingChatWindow");
    const floatBtn = document.getElementById("chatbotFloat");
    
    isChatOpen = !isChatOpen;
    
    if (isChatOpen) {
        windowEl.classList.add("active");
        floatBtn.classList.add("chat-open");
        floatBtn.innerHTML = '<i class="fas fa-times"></i>';
        scrollChatToBottom();
    } else {
        windowEl.classList.remove("active");
        floatBtn.classList.remove("chat-open");
        floatBtn.innerHTML = "💬";
    }
}

// ── Message Handling ──────────────────────────────────────────────────
async function sendFloatingMessage() {
    const input = document.getElementById("floatingInput");
    const text = input.value.trim();
    if (!text) return;

    // Hide welcome if it's there
    const welcome = document.getElementById("floatingWelcome");
    if (welcome) welcome.style.display = "none";

    // Add User Message
    addMessage(text, 'user');
    input.value = "";
    
    // Show Typing
    showTyping();

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });
        const data = await response.json();
        
        hideTyping();
        addMessage(data.response, 'bot');
    } catch (error) {
        console.error("Chat Error:", error);
        hideTyping();
        addMessage("Sorry, I'm having trouble connecting to the server. Please try again later.", 'bot');
    }
}

function handleFloatingEnter(event) {
    if (event.key === "Enter") {
        sendFloatingMessage();
    }
}

function sendFloatingQuick(text) {
    const input = document.getElementById("floatingInput");
    input.value = text;
    sendFloatingMessage();
}

// ── DOM Helpers ───────────────────────────────────────────────────────
function addMessage(text, sender) {
    const container = document.getElementById("floatingChatMessages");
    const msgDiv = document.createElement("div");
    msgDiv.className = `floating-message ${sender}`;
    
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Simple Markdown-to-HTML (Bold and Links)
    let formattedText = text
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>');

    msgDiv.innerHTML = `
        <div class="floating-message-avatar">${sender === 'bot' ? '🤖' : '👤'}</div>
        <div class="msg-content-wrapper">
            <div class="floating-message-bubble">${formattedText}</div>
            <div class="floating-message-time">${time}</div>
        </div>
    `;
    
    container.appendChild(msgDiv);
    scrollChatToBottom();
}

function showTyping() {
    const typing = document.getElementById("floatingTyping");
    if (typing) {
        typing.classList.add("active");
        scrollChatToBottom();
    }
}

function hideTyping() {
    const typing = document.getElementById("floatingTyping");
    if (typing) typing.classList.remove("active");
}

function scrollChatToBottom() {
    const container = document.getElementById("floatingChatMessages");
    if (container) container.scrollTop = container.scrollHeight;
}

function clearFloatingChat() {
    if (!confirm("Clear this conversation?")) return;
    const container = document.getElementById("floatingChatMessages");
    
    // Clear everything except Typing indicator
    const typing = document.getElementById("floatingTyping");
    container.innerHTML = "";
    container.appendChild(typing);
    
    // Bring back welcome
    addMessage("Hello! I'm your **CS Connect Assistant**. How can I help you today?", 'bot');
}
