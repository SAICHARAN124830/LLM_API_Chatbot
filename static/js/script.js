/**
 * Smart Assistant — Client-Side Application Script
 * Handles multi-turn chat interaction, state persistence, markdown rendering, and API communication.
 */

// Application State
const State = {
    conversationId: null,
    conversations: [],
    isGenerating: false,
    theme: localStorage.getItem("chatbot_theme") || "dark"
};

// DOM Elements
const DOM = {
    appLayout: document.querySelector(".app-layout"),
    sidebar: document.getElementById("sidebar"),
    sidebarOverlay: document.getElementById("sidebarOverlay"),
    mobileMenuBtn: document.getElementById("mobileMenuBtn"),
    closeSidebarBtn: document.getElementById("closeSidebarBtn"),
    newChatBtn: document.getElementById("newChatBtn"),
    headerNewChatBtn: document.getElementById("headerNewChatBtn"),
    clearChatBtn: document.getElementById("clearChatBtn"),
    themeToggleBtn: document.getElementById("themeToggleBtn"),
    themeIcon: document.getElementById("themeIcon"),
    themeLabel: document.getElementById("themeLabel"),
    conversationsList: document.getElementById("conversationsList"),
    chatCount: document.getElementById("chatCount"),
    chatTitle: document.getElementById("chatTitle"),
    messageCounterPill: document.getElementById("messageCounterPill"),
    chatBody: document.getElementById("chatBody"),
    welcomeContainer: document.getElementById("welcomeContainer"),
    messagesContainer: document.getElementById("messagesContainer"),
    typingIndicator: document.getElementById("typingIndicator"),
    chatForm: document.getElementById("chatForm"),
    messageInput: document.getElementById("messageInput"),
    sendBtn: document.getElementById("sendBtn"),
    toastContainer: document.getElementById("toastContainer")
};

// Initialize marked markdown options
if (typeof marked !== "undefined") {
    marked.setOptions({
        breaks: true,
        gfm: true,
        highlight: function (code, lang) {
            if (typeof hljs !== "undefined" && lang && hljs.getLanguage(lang)) {
                try {
                    return hljs.highlight(code, { language: lang }).value;
                } catch (e) {
                    console.error("Syntax highlight error:", e);
                }
            }
            return code;
        }
    });
}

// ==========================================
// Initialization
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    bindEvents();
    loadConversations();
    autoResizeTextarea();
});

// ==========================================
// Event Listeners
// ==========================================
function bindEvents() {
    // Form submission
    DOM.chatForm.addEventListener("submit", handleSubmit);

    // Enter key sends, Shift+Enter makes newline
    DOM.messageInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            DOM.chatForm.dispatchEvent(new Event("submit"));
        }
    });

    // Auto-resize input textarea
    DOM.messageInput.addEventListener("input", autoResizeTextarea);

    // New Chat buttons
    DOM.newChatBtn.addEventListener("click", () => startNewChat());
    DOM.headerNewChatBtn.addEventListener("click", () => startNewChat());

    // Clear current chat
    DOM.clearChatBtn.addEventListener("click", handleClearChat);

    // Theme toggle
    DOM.themeToggleBtn.addEventListener("click", toggleTheme);

    // Mobile sidebar toggle
    DOM.mobileMenuBtn.addEventListener("click", () => {
        DOM.sidebar.classList.add("open");
        DOM.sidebarOverlay.classList.add("active");
    });

    DOM.closeSidebarBtn.addEventListener("click", closeMobileSidebar);
    DOM.sidebarOverlay.addEventListener("click", closeMobileSidebar);

    // Suggestion cards click handler
    document.querySelectorAll(".suggestion-card").forEach(card => {
        card.addEventListener("click", () => {
            const prompt = card.getAttribute("data-prompt");
            if (prompt) {
                DOM.messageInput.value = prompt;
                autoResizeTextarea();
                DOM.messageInput.focus();
                DOM.chatForm.dispatchEvent(new Event("submit"));
            }
        });
    });
}

function closeMobileSidebar() {
    DOM.sidebar.classList.remove("open");
    DOM.sidebarOverlay.classList.remove("active");
}

// ==========================================
// Theme Management
// ==========================================
function initTheme() {
    document.documentElement.setAttribute("data-theme", State.theme);
    updateThemeUI();
}

function toggleTheme() {
    State.theme = State.theme === "dark" ? "light" : "dark";
    localStorage.setItem("chatbot_theme", State.theme);
    document.documentElement.setAttribute("data-theme", State.theme);
    updateThemeUI();
}

function updateThemeUI() {
    const isDark = State.theme === "dark";
    DOM.themeIcon.className = isDark ? "fa-solid fa-moon" : "fa-solid fa-sun";
    DOM.themeLabel.textContent = isDark ? "Dark Mode" : "Light Mode";
    
    // Switch highlight.js theme if available
    const hljsTheme = document.getElementById("hljs-theme");
    if (hljsTheme) {
        hljsTheme.href = isDark 
            ? "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css"
            : "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css";
    }
}

// ==========================================
// Textarea Auto-Resize
// ==========================================
function autoResizeTextarea() {
    DOM.messageInput.style.height = "auto";
    const newHeight = Math.min(DOM.messageInput.scrollHeight, 160);
    DOM.messageInput.style.height = `${newHeight}px`;
    DOM.sendBtn.disabled = !DOM.messageInput.value.trim() || State.isGenerating;
}

// ==========================================
// Chat Handling & Submission
// ==========================================
async function handleSubmit(e) {
    e.preventDefault();
    const text = DOM.messageInput.value.trim();
    if (!text || State.isGenerating) return;

    // Reset input
    DOM.messageInput.value = "";
    autoResizeTextarea();

    // Hide welcome view
    DOM.welcomeContainer.style.display = "none";

    // Append User Message to UI
    appendMessageUI({
        role: "user",
        content: text,
        timestamp: new Date().toISOString()
    });

    // Set generating state
    setGeneratingState(true);

    try {
        const payload = {
            message: text,
            conversation_id: State.conversationId
        };

        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            const errorMsg = data.error || "Failed to get a response from Gemini.";
            showToast(errorMsg, "error");
            appendMessageUI({
                role: "assistant",
                content: `⚠️ **Error:** ${errorMsg}`,
                timestamp: new Date().toISOString()
            });
            return;
        }

        // Update active conversation ID
        if (data.conversation_id && State.conversationId !== data.conversation_id) {
            State.conversationId = data.conversation_id;
        }

        // Append Assistant Reply
        appendMessageUI({
            role: "assistant",
            content: data.reply,
            timestamp: new Date().toISOString()
        });

        // Refresh sidebar conversation list
        await loadConversations();

    } catch (err) {
        console.error("Chat request failed:", err);
        showToast("Network connection error. Please check your internet connection.", "error");
        appendMessageUI({
            role: "assistant",
            content: "⚠️ **Network Error:** Unable to reach the server. Please check your connection and try again.",
            timestamp: new Date().toISOString()
        });
    } finally {
        setGeneratingState(false);
    }
}

function setGeneratingState(generating) {
    State.isGenerating = generating;
    DOM.sendBtn.disabled = generating || !DOM.messageInput.value.trim();
    if (generating) {
        DOM.typingIndicator.classList.add("active");
        scrollToBottom();
    } else {
        DOM.typingIndicator.classList.remove("active");
    }
}

// ==========================================
// Rendering Messages
// ==========================================
function appendMessageUI(msg) {
    const isUser = msg.role === "user";
    const row = document.createElement("div");
    row.className = `message-row ${isUser ? "user" : "assistant"}`;

    const avatar = document.createElement("div");
    avatar.className = `avatar ${isUser ? "user-avatar" : "assistant-avatar"}`;
    avatar.innerHTML = isUser ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';

    const wrapper = document.createElement("div");
    wrapper.className = "message-content-wrapper";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";

    if (isUser) {
        bubble.textContent = msg.content;
    } else {
        // Render Markdown safely
        if (typeof marked !== "undefined") {
            bubble.innerHTML = marked.parse(msg.content);
            enhanceCodeBlocks(bubble);
        } else {
            bubble.textContent = msg.content;
        }
    }

    const time = document.createElement("div");
    time.className = "message-time";
    time.textContent = formatTime(msg.timestamp);

    wrapper.appendChild(bubble);
    wrapper.appendChild(time);

    row.appendChild(avatar);
    row.appendChild(wrapper);

    DOM.messagesContainer.appendChild(row);
    updateMessageCounter();
    scrollToBottom();
}

function enhanceCodeBlocks(container) {
    const preBlocks = container.querySelectorAll("pre");
    preBlocks.forEach((pre) => {
        // Prevent double wrapping
        if (pre.parentElement.classList.contains("code-block-wrapper")) return;

        const code = pre.querySelector("code");
        let language = "code";
        if (code && code.className) {
            const match = code.className.match(/language-(\w+)/);
            if (match) language = match[1];
        }

        const wrapper = document.createElement("div");
        wrapper.className = "code-block-wrapper";

        const header = document.createElement("div");
        header.className = "code-block-header";
        header.innerHTML = `
            <span>${language}</span>
            <button class="copy-code-btn" type="button" title="Copy code">
                <i class="fa-regular fa-copy"></i> Copy
            </button>
        `;

        const copyBtn = header.querySelector(".copy-code-btn");
        copyBtn.addEventListener("click", () => {
            const rawText = code ? code.innerText : pre.innerText;
            navigator.clipboard.writeText(rawText).then(() => {
                copyBtn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
                setTimeout(() => {
                    copyBtn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
                }, 2000);
            });
        });

        pre.parentNode.insertBefore(wrapper, pre);
        wrapper.appendChild(header);
        wrapper.appendChild(pre);
    });
}

function scrollToBottom() {
    DOM.chatBody.scrollTop = DOM.chatBody.scrollHeight;
}

function updateMessageCounter() {
    const count = DOM.messagesContainer.querySelectorAll(".message-row").length;
    DOM.messageCounterPill.innerHTML = `<i class="fa-solid fa-layer-group"></i> ${count} message${count === 1 ? "" : "s"}`;
}

function formatTime(isoStr) {
    try {
        const date = isoStr ? new Date(isoStr) : new Date();
        return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
        return "";
    }
}

// ==========================================
// Conversation Management
// ==========================================
async function loadConversations() {
    try {
        const res = await fetch("/api/conversations");
        const data = await res.json();
        if (data.success) {
            State.conversations = data.conversations || [];
            renderSidebarConversations();
        }
    } catch (err) {
        console.error("Failed to load conversations:", err);
    }
}

function renderSidebarConversations() {
    DOM.conversationsList.innerHTML = "";
    DOM.chatCount.textContent = State.conversations.length;

    if (State.conversations.length === 0) {
        DOM.conversationsList.innerHTML = `
            <div class="empty-chat-state">
                <i class="fa-regular fa-comments" style="font-size: 1.5rem; margin-bottom: 6px; display: block;"></i>
                No previous conversations
            </div>
        `;
        return;
    }

    State.conversations.forEach((conv) => {
        const item = document.createElement("div");
        item.className = `chat-item ${conv.id === State.conversationId ? "active" : ""}`;
        item.setAttribute("data-id", conv.id);

        item.innerHTML = `
            <div class="chat-item-main">
                <i class="fa-regular fa-message"></i>
                <span class="chat-item-title">${escapeHTML(conv.title || "Conversation")}</span>
            </div>
            <button class="chat-item-delete" title="Delete conversation" data-id="${conv.id}">
                <i class="fa-solid fa-trash-can"></i>
            </button>
        `;

        // Switch to this conversation
        item.querySelector(".chat-item-main").addEventListener("click", () => {
            selectConversation(conv.id);
            closeMobileSidebar();
        });

        // Delete button
        item.querySelector(".chat-item-delete").addEventListener("click", (e) => {
            e.stopPropagation();
            deleteConversation(conv.id);
        });

        DOM.conversationsList.appendChild(item);
    });
}

async function selectConversation(id) {
    if (State.isGenerating) return;
    try {
        const res = await fetch(`/api/conversations/${id}`);
        const data = await res.json();
        if (data.success) {
            State.conversationId = id;
            const currentConv = State.conversations.find(c => c.id === id);
            DOM.chatTitle.textContent = currentConv ? currentConv.title : "Conversation";

            // Render messages
            DOM.messagesContainer.innerHTML = "";
            DOM.welcomeContainer.style.display = data.messages.length ? "none" : "block";

            data.messages.forEach(msg => appendMessageUI(msg));
            renderSidebarConversations();
            scrollToBottom();
        }
    } catch (err) {
        console.error("Failed to fetch conversation history:", err);
        showToast("Failed to load conversation history.", "error");
    }
}

async function startNewChat() {
    if (State.isGenerating) return;
    try {
        const res = await fetch("/api/conversations/new", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });
        const data = await res.json();
        if (data.success) {
            State.conversationId = data.conversation_id;
            DOM.chatTitle.textContent = "New Conversation";
            DOM.messagesContainer.innerHTML = "";
            DOM.welcomeContainer.style.display = "block";
            updateMessageCounter();
            await loadConversations();
            closeMobileSidebar();
            DOM.messageInput.focus();
        }
    } catch (err) {
        console.error("Failed to start new chat:", err);
        showToast("Error creating a new conversation.", "error");
    }
}

async function handleClearChat() {
    if (!State.conversationId) return;
    if (!confirm("Are you sure you want to clear the messages in this conversation?")) return;

    try {
        const res = await fetch(`/api/conversations/${State.conversationId}/clear`, {
            method: "POST"
        });
        const data = await res.json();
        if (data.success) {
            DOM.messagesContainer.innerHTML = "";
            DOM.welcomeContainer.style.display = "block";
            updateMessageCounter();
            showToast("Conversation cleared.", "success");
            await loadConversations();
        }
    } catch (err) {
        showToast("Failed to clear conversation.", "error");
    }
}

async function deleteConversation(id) {
    if (!confirm("Delete this conversation?")) return;
    try {
        const res = await fetch(`/api/conversations/${id}`, { method: "DELETE" });
        const data = await res.json();
        if (data.success) {
            showToast("Conversation deleted.", "success");
            if (State.conversationId === id) {
                await startNewChat();
            } else {
                await loadConversations();
            }
        }
    } catch (err) {
        showToast("Failed to delete conversation.", "error");
    }
}

// ==========================================
// Toast Notifications
// ==========================================
function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    const icon = type === "error" ? "fa-circle-exclamation" : (type === "success" ? "fa-circle-check" : "fa-info-circle");
    toast.innerHTML = `
        <i class="fa-solid ${icon} toast-icon"></i>
        <span class="toast-message">${escapeHTML(message)}</span>
    `;

    DOM.toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(30px)";
        toast.style.transition = "all 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function escapeHTML(str) {
    if (!str) return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
