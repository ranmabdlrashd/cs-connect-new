/**
 * CS Connect Chatbot - Premium UI Logic
 * Connects to the Flask/Anthropic backend (/api/chat).
 */

let isChatOpen = false;
let conversationHistory = []; // Stores {role: 'user'|'assistant', content: string}

// ── Toggle Logic ──────────────────────────────────────────────────────
function toggleChatWindow() {
    const windowEl = document.getElementById("chatbotWindow");
    const fabEl = document.getElementById("chatbotFab");
    const tooltipEl = document.getElementById("chatbotTooltip");
    const pillsEl = document.getElementById("chatbotQuickPills");
    
    isChatOpen = !isChatOpen;
    
    if (isChatOpen) {
        windowEl.classList.add("active");
        fabEl.classList.add("mini-fab");
        if(tooltipEl) tooltipEl.style.display = "none";
        if(pillsEl) pillsEl.style.display = "none";
        
        // Add welcome message if empty
        const messages = document.querySelectorAll('.message-row:not(.chat-typing-indicator)');
        if (messages.length === 0) {
            showInitialWelcome();
        }
        
        scrollChatToBottom();
        document.getElementById("chatInput").focus();
    } else {
        windowEl.classList.remove("active");
        fabEl.classList.remove("mini-fab");
        if(pillsEl) pillsEl.style.display = "flex";
        // Hide tooltip permanently after first click usually, but keeping it simple
    }
}

// ── Initialization ────────────────────────────────────────────────────
function showInitialWelcome() {
    const name = window.chatConfig.userName;
    const msg = name ? `Hello ${name}! I'm the CS Connect assistant. How can I help you today?` : `Hello! I'm the CS Connect assistant. Login to get personalised answers, or ask me anything about the department!`;
    
    conversationHistory.push({ role: 'assistant', content: msg });
    addMessageToDOM(msg, 'bot');
}

// ── Message Handling ──────────────────────────────────────────────────
async function sendChat() {
    const input = document.getElementById("chatInput");
    const text = input.value.trim();
    if (!text) return;

    input.value = "";
    input.style.height = "36px"; // Reset height if it was auto-expanded
    
    // Add user message locally
    conversationHistory.push({ role: 'user', content: text });
    if(conversationHistory.length > 20) {
        conversationHistory.shift(); // keep it bounded
    }
    
    addMessageToDOM(text, 'user');
    showTyping();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ messages: conversationHistory })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        hideTyping();
        
        const replyText = data.response || "Sorry, I didn't get any response.";
        conversationHistory.push({ role: 'assistant', content: replyText });
        if(conversationHistory.length > 20) {
            conversationHistory.shift();
        }
        
        addMessageToDOM(replyText, 'bot');
        
    } catch (error) {
        console.error("Chat Error:", error);
        hideTyping();
        addMessageToDOM("Sorry, I'm having trouble connecting to the server. Please try again later.", 'bot', true);
    }
}

// Handle inputs (Enter vs Shift+Enter)
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("chatInput");
    if(input) {
        input.addEventListener("keydown", function(event) {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                sendChat();
            }
        });
        
        // Optional quick pills close logic
        setTimeout(() => {
            const tooltip = document.getElementById("chatbotTooltip");
            if(tooltip && !isChatOpen) {
                tooltip.style.opacity = '1';
                setTimeout(() => tooltip.style.opacity = '0', 5000); // fade out after 5s
            }
        }, 2000);
    }
});

function sendChatbotQuick(text) {
    const input = document.getElementById("chatInput");
    input.value = text;
    if(!isChatOpen) toggleChatWindow();
    sendChat();
}

// ── DOM Helpers ───────────────────────────────────────────────────────
function addMessageToDOM(text, sender, isError=false) {
    const container = document.getElementById("chatMessages");
    const typingIndicator = document.getElementById("chatTypingIndicator");
    
    const rowEl = document.createElement("div");
    rowEl.className = `message-row ${sender}`;
    
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Premium Markdown Rendering
    let formattedText;
    if (sender === 'bot') {
        // AI responses use full Markdown rendering
        // Ensure all links open in new tab
        const renderer = new marked.Renderer();
        renderer.link = ({ href, title, text }) => {
            return `<a href="${href}" title="${title || ''}" target="_blank" rel="noopener noreferrer">${text}</a>`;
        };
        formattedText = marked.parse(text, { renderer });
    } else {
        // User messages are escaped for security and use basic break replacement
        formattedText = escapeHtml(text).replace(/\n/g, '<br>');
    }
        
    if (sender === 'bot') {
        const avatarSvg = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" class="icon-fill"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" fill="#F5E6BE"/></svg>`;
        rowEl.innerHTML = `
            <div class="bot-avatar gradient-avatar mini-bot-avatar">
                ${avatarSvg}
            </div>
            <div class="msg-content">
                <div class="bubble bot-bubble ${isError ? 'error-text' : ''}">${formattedText}</div>
                <div class="message-time">${time}</div>
            </div>
        `;
    } else {
        const initials = window.chatConfig.userInitials || "U";
        rowEl.innerHTML = `
            <div class="user-avatar-initials">${initials}</div>
            <div class="msg-content">
                <div class="bubble user-bubble">${formattedText}</div>
                <div class="message-time">${time}</div>
            </div>
        `;
    }
    
    // Insert before typing indicator
    if (typingIndicator) {
        container.insertBefore(rowEl, typingIndicator);
    } else {
        container.appendChild(rowEl);
    }
    
    scrollChatToBottom();
}

function showTyping() {
    const typing = document.getElementById("chatTypingIndicator");
    if (typing) {
        typing.style.display = "flex";
        scrollChatToBottom();
    }
}

function hideTyping() {
    const typing = document.getElementById("chatTypingIndicator");
    if (typing) typing.style.display = "none";
}

function scrollChatToBottom() {
    const container = document.getElementById("chatMessages");
    if (container) container.scrollTop = container.scrollHeight;
}

function clearChat() {
    if (!confirm("Clear this conversation?")) return;
    
    conversationHistory = [];
    
    const container = document.getElementById("chatMessages");
    const typing = document.getElementById("chatTypingIndicator");
    
    container.innerHTML = "";
    if (typing) {
        typing.style.display = "none"; // Reset typing state
        container.appendChild(typing);
    }
    
    showInitialWelcome();
}

function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}
