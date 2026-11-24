# 🤖 Smart Assistant — LLM API Chatbot with Multi-Turn Memory & Context Window Management

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask 3.0+](https://img.shields.io/badge/Flask-3.1.3-green.svg)](https://flask.palletsprojects.com/)
[![Google GenAI SDK](https://img.shields.io/badge/Google%20GenAI-3.6.1-orange.svg)](https://github.com/googleapis/python-genai)
[![Gemini 3.5 Flash Lite](https://img.shields.io/badge/Model-Gemini%203.5%20Flash%20Lite-purple.svg)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise-grade, full-stack AI conversational application built with **Python**, **Flask**, and **Google Gemini AI**. Featuring multi-turn conversation memory, state-of-the-art context window management (**Last N Messages Strategy**), custom system personas, graceful error resilience with automated model fallbacks, and a sleek **ChatGPT-inspired** responsive interface.

---

## 📌 Table of Contents
- [Project Overview](#-project-overview)
- [Problem Statement](#-problem-statement)
- [Key Objectives](#-key-objectives)
- [Features](#-features)
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Project Folder Structure](#-project-folder-structure)
- [Prerequisites & Installation](#-prerequisites--installation)
- [Environment Configuration](#-environment-configuration)
- [Running the Application](#-running-the-application)
- [RESTful API Endpoints](#-restful-api-endpoints)
- [Verified Multi-Turn Conversation Proof](#-verified-multi-turn-conversation-proof)
- [Automated Testing Suite](#-automated-testing-suite)
- [UI & Screenshots Walkthrough](#-ui--screenshots-walkthrough)
- [Git & GitHub Submission Commands](#-git--github-submission-commands)
- [Future Enhancements](#-future-enhancements)
- [License](#-license)

---

## 📖 Project Overview
This project delivers a production-ready conversational chatbot that integrates with the official **Google GenAI Python SDK (`google-genai`)** and connects directly to Google's flagship **Gemini** models (e.g., `gemini-3.5-flash`). Unlike naive chatbots that treat every prompt as isolated, this system retains conversational history across multiple turns, tracks separate conversation sessions, and prevents token overflow through configurable context window management.

---

## 🎯 Problem Statement
Standard single-turn LLM integrations suffer from key limitations:
1. **Statelessness:** The model forgets who the user is or what was discussed in previous turns.
2. **Context Window Overflow:** Naively passing unbounded conversation history quickly exceeds token limits, increases API latency, and inflates costs.
3. **Session Contamination:** Multi-user or multi-chat environments risk mixing dialogue histories.
4. **Fragile Error Handling:** Transient API spikes (such as HTTP 503 high demand or HTTP 429 rate limits) often crash applications or leave users stranded with blank screens.

---

## 🎯 Key Objectives
- **Direct LLM API Integration:** Seamless, real-time connectivity with Google Gemini using the latest official SDK.
- **Robust Multi-Turn Memory:** Track user profile information, technical requirements, and context over 5+ conversational turns.
- **Context Window Management:** Implement a configurable **Last $N$ Messages Strategy** that truncates older messages while ensuring valid conversational flow (starting on user turns) and preserving system instructions.
- **Resilient Fault Tolerance:** Automatic retry with exponential backoff and intelligent model fallbacks (e.g. from `gemini-3.5-flash` to `gemini-3.5-flash-lite`).
- **Modern ChatGPT-Grade UI:** Responsive layout with dark/light themes, markdown rendering, syntax highlighting with one-click code copy, conversation sidebar, and toast alerts.

---

## ✨ Features

- **🧠 Multi-Turn Memory & Separate Histories:**
  - Unique UUID-based conversation sessions (`ConversationManager`).
  - Isolated contexts: user conversations never cross-talk.
  - Sidebar with dynamic chat switching, renaming, clearing, and deletion.

- **🪟 Context Window Management (Last N Messages):**
  - Configurable message budget via `.env` (`MAX_HISTORY_MESSAGES=10`).
  - Automatically slices dialogue turns to fit model context without losing coherence.
  - Ensures Gemini dialogue invariants: always begins with a `user` turn and preserves `system_instruction`.

- **🛡️ Custom System Prompt & Persona:**
  - Dedicated **Smart Assistant** persona designed for programming, research, and technical tutoring.
  - Step-by-step explanatory behavior with grounded responses.

- **🔄 Automatic Retries & Model Fallbacks:**
  - Handles transient network drops, rate limits (429), and demand spikes (503).
  - Exponential backoff retry logic.
  - Graceful fallback model switching if the primary model is saturated.

- **🎨 ChatGPT-Inspired Frontend:**
  - Pure Vanilla JavaScript & CSS (no heavy frontend framework overhead).
  - Dark & Light mode toggle with local storage persistence.
  - Code block formatting with syntax highlighting (`highlight.js`) and one-click copy.
  - Auto-scrolling, typing indicators, auto-resizing input textarea, and mobile-responsive drawer.

---

## 🛠️ Architecture & Tech Stack

```mermaid
flowchart TD
    User["Web Browser (User)"]
    Frontend["HTML5 / CSS3 / Vanilla JS (script.js)"]
    Flask["Flask Application (app.py)"]
    ConvMgr["Conversation Manager (conversation_manager.py)"]
    GeminiSvc["Gemini Service (gemini_service.py)"]
    GeminiAPI["Google Gemini AI API (Cloud)"]

    User <-->|HTTP / REST JSON| Frontend
    Frontend <-->|POST /api/chat| Flask
    Flask <-->|Store / Retrieve Turns & Context| ConvMgr
    Flask -->|Context Window & System Prompt| GeminiSvc
    GeminiSvc <-->|google-genai SDK (HTTPS)| GeminiAPI
```

### Technologies Used:
- **Backend:** Python 3.10+, Flask 3.1.3, Werkzeug, Jinja2
- **AI / SDK:** Google GenAI SDK (`google-genai` 3.6.1), Google Gemini 3.5 Flash
- **Configuration & Security:** `python-dotenv`, Pydantic
- **Frontend:** HTML5, CSS3 Variables, ES6+ JavaScript, FontAwesome 6, Highlight.js, Marked.js
- **Testing:** Python `unittest`, automated multi-turn verification runner

---

## 📁 Project Folder Structure

```
LLM_API_Chatbot/
│
├── app.py                      # Flask application factory, routing & API endpoints
├── config.py                   # Centralized configuration & environment loader
├── gemini_service.py           # Gemini API client wrapper, retry logic & fallbacks
├── conversation_manager.py     # Multi-turn memory & context window manager
├── run_tests.py                # Unified test runner (Unit, API, Live 5-turn test)
├── test_gemini.py              # Diagnostic script to test Gemini API connection
├── requirements.txt            # Python dependencies
├── .env                        # Private environment variables (excluded from git)
├── .env.example                # Template for environment configuration
├── .gitignore                  # Git exclusions (venv, .env, __pycache__)
├── README.md                   # Complete project documentation
│
├── templates/
│   └── index.html              # ChatGPT-inspired responsive UI template
│
├── static/
│   ├── css/
│   │   └── style.css           # Modern theme styling, animations & responsive media queries
│   └── js/
│       └── script.js           # Frontend controller: fetch API, markdown, state management
│
└── tests/
    ├── test_api.py             # Integration tests for Flask endpoints & validation
    ├── test_conversation.py    # Unit tests for ConversationManager & context window slicing
    └── test_multi_turn_live.py # Live 5-turn memory verification with real Gemini API
```

---

## 🚀 Prerequisites & Installation

### 1. Prerequisites
- **Python 3.10** or higher installed.
- A **Google Gemini API Key** (obtainable free from [Google AI Studio](https://aistudio.google.com/)).

### 2. Clone the Repository
```bash
git clone https://github.com/<your-username>/LLM_API_Chatbot.git
cd LLM_API_Chatbot
```

### 3. Create and Activate Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ⚙️ Environment Configuration

1. Copy the `.env.example` file to create your own `.env`:
   ```bash
   cp .env.example .env
   ```
   *(Or on Windows PowerShell: `Copy-Item .env.example .env`)*

2. Open `.env` and fill in your Gemini API key:
   ```ini
   # Google Gemini API Key
   GEMINI_API_KEY=your_actual_gemini_api_key_here

   # Target Gemini Model (gemini-3.5-flash-lite is fast, reliable, and active)
   GEMINI_MODEL=gemini-3.5-flash-lite

   # Maximum recent conversation messages sent in context window
   MAX_HISTORY_MESSAGES=10

   # Server Port (optional, default: 5000)
   FLASK_PORT=5000
   FLASK_DEBUG=False
   ```

> [!IMPORTANT]
> The `.env` file contains your private API key and is strictly ignored in `.gitignore`. Never commit `.env` to public version control.

---

## 🏃 Running the Application

### 1. Verify API Connection
Before starting the web app, you can run the diagnostic tool:
```bash
python test_gemini.py
```
Output:
```
============================================================
 Gemini API Connection Diagnostic Test
============================================================
[OK] API Key loaded successfully
[INFO] Target Model: gemini-3.5-flash
Connecting to Google Gemini API...
[SUCCESS] Gemini Response Received:
The API connection is active and working properly.
[STATUS] Connection is working perfectly!
```

### 2. Start the Flask Application
```bash
python app.py
```

### 3. Open in Browser
Visit `http://localhost:5000` in your web browser.

---

## 🔌 RESTful API Endpoints

| Method | Endpoint | Description | Sample Request / Response |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Web interface homepage | Returns HTML document |
| `POST` | `/api/chat` | Send user message and get AI response with memory | **Req:** `{"message": "Hello", "conversation_id": "uuid"}`<br>**Res:** `{"success": true, "reply": "...", "conversation_id": "uuid"}` |
| `GET` | `/api/conversations` | List all conversation sessions with metadata | **Res:** `{"success": true, "conversations": [...]}` |
| `POST` | `/api/conversations/new` | Create a new conversation session | **Res:** `{"success": true, "conversation_id": "uuid"}` |
| `GET` | `/api/conversations/<id>` | Retrieve full message history of a conversation | **Res:** `{"success": true, "messages": [...]}` |
| `POST` | `/api/conversations/<id>/clear` | Clear message history in conversation | **Res:** `{"success": true, "message": "Cleared"}` |
| `DELETE` | `/api/conversations/<id>` | Delete conversation session completely | **Res:** `{"success": true, "message": "Deleted"}` |
| `GET` | `/api/health` | Health check endpoint | **Res:** `{"status": "healthy", "model": "gemini-3.5-flash"}` |

---

## 🧪 Verified Multi-Turn Conversation Proof

Below is the transcript from the actual automated 5-turn verification test executed against Google Gemini (`gemini-3.5-flash`):

```text
======================================================================
 LIVE 5-TURN CONVERSATION MEMORY VERIFICATION TEST
======================================================================
[SESSION] Created test conversation: 9d5ef85e-2e12-47f3-834a-7626ec185aa2

--- TURN 1 ---
User: My name is Sai.
Assistant (gemini-3.5-flash): Hello Sai! It's great to meet you. How can I help you today?

--- TURN 2 ---
User: I am studying Artificial Intelligence.
Assistant (gemini-3.5-flash): That's exciting, Sai! Artificial Intelligence is a fascinating and rapidly evolving field. 
Whether you need help understanding complex concepts, debugging code, working through math foundations...

--- TURN 3 ---
User: I am currently in my fifth semester.
Assistant (gemini-3.5-flash): That's a great stage in your studies! Semester five is usually when things get really interesting in an AI or Computer Science program...

--- TURN 4 ---
User: What is my name?
Assistant (gemini-3.5-flash): Your name is Sai!
[CHECK PASSED] Model remembered: 'Sai'

--- TURN 5 ---
User: Which subject am I studying and which semester am I in?
Assistant (gemini-3.5-flash): You are studying Artificial Intelligence and you are currently in your fifth semester!
[CHECK PASSED] Model remembered both subject and semester correctly!

======================================================================
 ALL 5 TURNS COMPLETED AND VERIFIED SUCCESSFULLY!
 Multi-turn context memory is fully functional with Google Gemini API.
======================================================================
```

---

## 🧪 Automated Testing Suite

Run the full automated test suite (including unit tests, API integration tests, and live multi-turn verification) with a single command:

```bash
python run_tests.py
```

Or run individual test modules:
```bash
# Run unit & API integration tests
python -m unittest tests/test_conversation.py tests/test_api.py

# Run live 5-turn Gemini multi-turn test
python tests/test_multi_turn_live.py
```

### Test Coverage Highlights:
- ✅ **Conversation Isolation:** Verifies separate conversation IDs do not bleed or cross-talk.
- ✅ **Context Window Truncation:** Tests Last $N$ messages cutoff and ensures context always starts with a `user` turn.
- ✅ **API Input Validation:** Rejects empty, whitespace-only, and non-string payloads with 400 Bad Request.
- ✅ **Error Shielding:** Tests that internal stack traces or raw API keys are never exposed in JSON responses.
- ✅ **Session Lifecycle:** Tests creation, listing, retrieval, clearing, and deletion of conversation threads.

---

## 🖥️ UI & Screenshots Walkthrough

1. **Modern Layout:** Left sidebar for conversation management and right chat pane with auto-scrolling message streams.
2. **Welcome Screen:** Engaging initial view with quick prompt suggestions for AI exploration, coding, and prompt engineering.
3. **Markdown & Code Blocks:** Formatted responses with syntax highlighting and a 1-click **Copy** button.
4. **Theme Customization:** Toggle between dark mode and light mode with persistent settings.
5. **Session Controls:** Fast "New Chat", "Clear Chat", and individual conversation deletion.

---

## 📦 Git & GitHub Submission Commands

Follow these exact steps to publish this completed project to your public GitHub repository:

```bash
# 1. Initialize git repository (if not already initialized)
git init

# 2. Check that .env and venv are ignored
git status

# 3. Add all project files
git add .

# 4. Commit files with a professional commit message
git commit -m "feat: complete LLM API Chatbot with multi-turn memory and context window management"

# 5. Set default branch to main
git branch -M main

# 6. Add your GitHub remote repository URL
# Replace <YOUR-GITHUB-USERNAME> and <REPO-NAME> with your details
git remote add origin https://github.com/<YOUR-GITHUB-USERNAME>/LLM_API_Chatbot.git

# 7. Push to GitHub
git push -u origin main
```

---

## 🔮 Future Enhancements
- [ ] **Streaming Responses (SSE):** Stream tokens incrementally using Server-Sent Events for faster perceived latency.
- [ ] **Persistent Database:** Migrate in-memory storage to SQLite or PostgreSQL with SQLAlchemy.
- [ ] **Running Summarization:** Summarize older truncated messages with a lightweight background LLM call to retain semantic context across 50+ turns.
- [ ] **Multimodal Support:** Enable file and image uploads for analysis via Gemini Vision capabilities.
- [ ] **Export Chat:** Provide one-click export of chat sessions to Markdown or PDF.

---

## 📄 License
This project is licensed under the [MIT License](LICENSE). Feel free to use, modify, and distribute it for academic and commercial purposes.
