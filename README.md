# 🤖 Always-On Personal AI Assistant

A fully local, always-on AI assistant that runs on your computer. Built with Python, it maintains a **persistent identity**, **evolving memory**, **emotional simulation**, and **time awareness** — designed to feel like a consistent digital personality rather than a stateless chatbot.

> No cloud required. No subscriptions. Your data stays on your machine.

> ⚠️ This project is currently in active development. Core functionality is working but some features are still being built out.

---

## ✨ Features

- **Persistent Identity** — Give your assistant a name and personality that survives restarts
- **Memory System** — Short-term session memory + long-term semantic memory via vector embeddings
- **Memory Management** — List, search, store, and delete memories via CLI or REST API
- **Session Management** — List, resume, and delete past conversation sessions
- **Conversation History** — Auto-trim long sessions and export conversations to text, markdown, or JSON
- **Learns About You** — Remembers facts, preferences, and past conversations over time
- **Emotional Simulation** — LLM-powered emotion analysis (POSITIVE / NEGATIVE / RUDE) drives internal mood, trust, stress, and engagement variables
- **Time Awareness** — Knows the date, time, day of week, and simulates availability and work hours
- **Tool System** — Plugin-style tools with native LLM tool calling — no regex, no text parsing
- **Web Search** — Fully local search via SearXNG, no API keys, no rate limits, nothing leaves your machine
- **Notes** — Save, list, and read markdown notes stored locally on disk
- **Voice Interface** — Speak to your assistant and hear responses back (fully local STT/TTS)
- **REST API** — FastAPI backend with full Swagger documentation at `/docs`
- **React Frontend** — Chat UI with markdown rendering and live mood indicator
- **Local LLM** — Runs with Ollama; supports any model including native tool-calling models

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                     USER INTERFACES                      │
│   CLI / Text UI    React Frontend    Voice Interface     │
└──────────────────────────┬───────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────┐
│               FASTAPI REST API (port 8000)               │
│  /api/chat   /api/identity   /api/memory   /api/sessions │
│  /api/voice  /api/health                                 │
└──────────────────────────┬───────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────┐
│              ASSISTANT CORE (Orchestrator)               │
│   Identity Manager  │  Conversation Engine               │
│   Session Manager   │  Conversation History              │
│   Time Awareness    │  Emotional State System            │
└────────────┬─────────────────────────────────────────────┘
             │
   ┌─────────┼──────────┐
   ▼         ▼          ▼
┌──────┐  ┌───────┐  ┌───────┐
│ LLM  │  │Memory │  │ Tools │
│Layer │  │  STM  │  │Search │
│Ollama│  │  LTM  │  │       │
│      │  │       │  │ Notes │
└──────┘  └───────┘  └───────┘
              │
   ┌──────────▼──────────┐
   │     Persistence     │
   │  SQLite + ChromaDB  │
   └─────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com) installed and running locally
- Docker (for SearXNG web search)
- A pulled Ollama model — a native tool-calling model is recommended

```bash
ollama pull llama3
ollama pull nomic-embed-text   # required for long-term memory
```

### Installation

```bash
# Clone the repository
git clone https://github.com/avolel/assistant.git
cd assistant

# Install dependencies
pip install poetry
poetry install

# Copy and configure environment
cp .env.example .env
```

### Start Required Services

```bash
# SearXNG — local web search
docker run -d \
  --name searxng \
  -p 8080:8080 \
  -e SEARXNG_SECRET_KEY=changeme \
  --restart unless-stopped \
  searxng/searxng

# Enable JSON API in SearXNG (run once after first start)
docker exec searxng sed -i 's/formats:/formats:\n    - json/' /etc/searxng/settings.yml
docker restart searxng

```

### First-Time Setup

```bash
python main.py setup
```

```
Welcome! Let's configure your assistant.
Assistant name: Aria
Your name: Andy
Your email (optional): andy@localhost
Your timezone: America/New_York
LLM provider [ollama]: ollama
LLM model [llama3]: llama3

✓ Identity created.
✓ Database initialized.
✓ Configuration saved to .env
Run `python main.py chat` to start.
```

### Start the Assistant

```bash
# Text chat interface
python main.py chat

# Voice interface
python main.py voice

# REST API + React frontend
python main.py serve
# → http://localhost:8000
```

---

## 📁 Project Structure

```
assistant/
├── main.py                        # Entry point + CLI commands
├── pyproject.toml
├── .env.example
│
├── assistant/
│   ├── core/
│   │   ├── assistant.py           # AssistantCore orchestrator
│   │   ├── identity.py            # Identity + owner profile
│   │   └── session.py             # Session lifecycle management
│   │
│   ├── conversation/
│   │   ├── engine.py              # Conversation engine + tool routing
│   │   ├── prompt_builder.py      # System prompt construction
│   │   └── history.py             # History trimming + export
│   │
│   ├── memory/
│   │   ├── manager.py             # MemoryManager facade
│   │   ├── short_term.py          # STM — recent turns (SQLite)
│   │   ├── long_term.py           # LTM — semantic store (ChromaDB)
│   │   ├── embeddings.py          # Embedding generation (Ollama)
│   │   └── summarizer.py          # Session summarization
│   │
│   ├── emotions/
│   │   ├── state.py               # EmotionalState model
│   │   └── engine.py              # Emotion update rules
│   │
│   ├── time_awareness/
│   │   └── service.py             # Time context + availability
│   │
│   ├── llm/
│   │   ├── base.py                # LLMProvider abstract base
│   │   ├── ollama_provider.py     # Ollama implementation
│   │   └── factory.py             # Provider factory
│   │
│   ├── tools/
│   │   ├── registry.py            # Tool registry + Ollama manifest
│   │   ├── base.py                # BaseTool + ToolResult
│   │   ├── web_search.py          # SearXNG web search
│   │   ├── email_sender.py        # SMTP email
│   │   └── notes.py               # Local markdown notes
│   │
│   ├── api/
│   │   ├── app.py                 # FastAPI application
│   │   ├── models.py              # Request/response models
│   │   ├── session_store.py       # In-memory session store
│   │   └── routes/
│   │       ├── chat.py            # POST /api/chat
│   │       ├── identity.py        # GET/POST /api/identity
│   │       ├── memory.py          # CRUD /api/memory
│   │       ├── sessions.py        # CRUD /api/sessions
│   │       ├── voice.py           # POST /api/voice
│   │       └── health.py          # GET /api/health
│   │
│   ├── voice/
│   │   ├── stt.py                 # Speech-to-text (faster-whisper)
│   │   └── tts.py                 # Text-to-speech (pyttsx3)
│   │
│   ├── database/
│   │   ├── connection.py          # SQLite connection + context manager
│   │   └── migrations.py          # Schema creation
│   │
│   └── config/
│       └── settings.py            # Pydantic settings
│
├── frontend/                      # React + Tailwind chat UI
│
└── tests/
    ├── conftest.py                 # Shared fixtures
    ├── unit/
    ├── integration/
    └── accuracy/
```

---

## 🧠 Memory System

The assistant uses a **hybrid memory architecture**:

| Store | Technology | Used For |
|-------|-----------|----------|
| Short-Term Memory | SQLite | Current session turns (last N, auto-trimmed) |
| Long-Term Memory | ChromaDB (vector DB) | Semantic recall across sessions |
| User Facts | ChromaDB collection | Preferences, personal info |
| Conversation Summaries | ChromaDB collection | Compressed past sessions |

Long-term memories are embedded using **Ollama's `nomic-embed-text`** model and retrieved via cosine similarity — so the assistant can answer *"what do you know about my job?"* without keyword matching.

> **Note:** ChromaDB telemetry warnings are suppressed by passing `settings=Settings(anonymized_telemetry=False)` when initializing the ChromaDB client in `assistant/memory/long_term.py`. No `.env` changes required.

---

## 🗂️ Session Management

Sessions are stored in SQLite and can be managed from the CLI or via the REST API.

```bash
# List all past sessions
python main.py sessions

# Resume a previous session (shows last 6 turns for context)
python main.py resume YOUR-SESSION-ID

# Delete a session and all its turns
python main.py delete-session YOUR-SESSION-ID
```

```bash
# API
GET    /api/sessions/               # List all sessions
GET    /api/sessions/{session_id}   # Get session + full turn history
DELETE /api/sessions/{session_id}   # Delete a session
```

---

## 📜 Conversation History

History is automatically trimmed to keep sessions within the configured turn limit. Conversations can be exported at any time.

```bash
# Export the latest session as plain text (default)
python main.py export

# Export as markdown
python main.py export --format markdown

# Export as JSON
python main.py export --format json

# Export a specific session
python main.py export --format markdown --session YOUR-SESSION-ID
```

Exports are saved to `~/assistant_exports/` with a timestamp in the filename.

---

## 🧬 Memory Management

Long-term memories can be listed, searched, stored, and deleted from the CLI or the API.

```bash
# List all long-term memories
python main.py memories

# Delete a specific memory
python main.py forget YOUR-MEMORY-ID
```

```bash
# API
GET    /api/memory/          # List all memories
POST   /api/memory/search    # Semantic search  {"query": "...", "n_results": 5}
POST   /api/memory/          # Store manually   {"content": "...", "memory_type": "user_fact"}
DELETE /api/memory/{id}      # Delete a memory
```

---

## 💬 Emotional State

The assistant uses the LLM to classify the emotional tone of every user message as `POSITIVE`, `NEGATIVE`, or `RUDE`. This classification drives four internal state variables:

| Variable | Range | Baseline |
|----------|-------|---------|
| `mood` | 0.0–1.0 | 0.5 |
| `trust` | 0.0–1.0 | 0.5 |
| `stress` | 0.0–1.0 | 0.2 |
| `engagement` | 0.0–1.0 | 0.7 |

Positive interactions raise mood and trust. Negative interactions increase stress. Rude interactions significantly reduce trust and engagement. All values naturally drift back toward their baseline over time. The current emotional state subtly influences the tone of every response without being mentioned explicitly.

---

## 🔧 Tool System

Tools use **native LLM tool calling** — the model receives structured JSON tool definitions and returns structured `tool_calls` responses. No text parsing, no fragile regex, no custom prompt formatting required.

Tools follow a simple plugin contract — subclass `BaseTool`, decorate with `@register_tool`, implement `run()`:

```python
from assistant.tools.base import BaseTool, ToolResult
from assistant.tools.registry import register_tool

@register_tool
class MyTool(BaseTool):
    name = "my_tool"
    description = "Does something useful."
    parameters = {
        "query": {"type": "string", "description": "The input query"},
        "limit": {"type": "integer", "description": "Max results", "optional": True}
    }

    async def run(self, query: str, limit: int = 5) -> ToolResult:
        result = do_something(query, limit)
        return ToolResult(success=True, output=result)
```

Parameters marked `optional: True` are excluded from the `required` list sent to the model, so it only passes them when the context calls for it. Then import the module in `assistant/conversation/engine.py` and it is registered automatically.

### Built-in Tools

| Tool | Backend | Description |
|------|---------|-------------|
| `web_search` | SearXNG (local Docker) | Search the web with no API key and no rate limits |
| `notes` | Local filesystem | Save, list, and read markdown notes in `~/assistant_notes/` |

---

## 🔍 Web Search

Web search is powered by **SearXNG** running locally in Docker. This means no API key, no rate limiting, and no search queries sent to third parties. Results are aggregated from multiple search engines locally.

SearXNG web UI: `http://localhost:8080`

```
You: Search the web for the latest Python news
Aria: Here's what I found...
```

---

## 🤖 LLM Configuration

The assistant uses **Ollama** with any locally pulled model. Native tool-calling models work best as they return structured `tool_calls` JSON.

```env
ASSISTANT_LLM_PROVIDER=ollama
ASSISTANT_LLM_MODEL=gpt-oss:20b
ASSISTANT_LLM_MODEL_EMOTION=llama3.1:8b
ASSISTANT_LLM_BASE_URL=http://localhost:11434
```

The LLM abstraction layer means adding a new provider only requires implementing one class that extends `LLMProvider`.

---

## 🎤 Voice Interface

| Direction | Library | Notes |
|-----------|---------|-------|
| Speech → Text | `faster-whisper` | Local Whisper model, CPU/GPU |
| Text → Speech | `pyttsx3` | System TTS, zero install |
| Text → Speech (HQ) | Coqui `TTS` (XTTS-v2) | Near-human quality, fully local |

Voice requires PortAudio on Linux:

```bash
sudo apt install -y portaudio19-dev
```

```bash
python main.py voice
```

---

## 🌐 REST API

Start the API server:

```bash
python main.py serve
# → http://localhost:8000       React frontend
# → http://localhost:8000/docs  Swagger UI
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/identity/` | Get assistant identity |
| `POST` | `/api/identity/setup` | First-time setup |
| `POST` | `/api/chat/` | Send a message |
| `GET` | `/api/memory/` | List all memories |
| `POST` | `/api/memory/search` | Semantic memory search |
| `POST` | `/api/memory/` | Store a memory manually |
| `DELETE` | `/api/memory/{id}` | Delete a memory |
| `GET` | `/api/sessions/` | List all sessions |
| `GET` | `/api/sessions/{id}` | Get session + turns |
| `DELETE` | `/api/sessions/{id}` | Delete a session |
| `POST` | `/api/voice/listen` | Record + transcribe voice |
| `POST` | `/api/voice/speak` | Speak text via TTS |

---

## 💻 CLI Reference

```bash
python main.py setup                          # First-time setup wizard
python main.py chat                           # Start a text chat session
python main.py voice                          # Start a voice session
python main.py serve                          # Start the API + frontend server
python main.py sessions                       # List past sessions
python main.py resume SESSION_ID              # Resume a past session
python main.py delete-session SESSION_ID      # Delete a session
python main.py export                         # Export latest session as text
python main.py export --format markdown       # Export as markdown
python main.py export --format json           # Export as JSON
python main.py export --session SESSION_ID    # Export a specific session
```

---

## ⚙️ Environment Variables

```env
# LLM
ASSISTANT_LLM_PROVIDER=ollama
ASSISTANT_LLM_MODEL=gpt-oss:20b
ASSISTANT_LLM_MODEL_EMOTION=llama3.1:8b
ASSISTANT_LLM_BASE_URL=http://localhost:11434
ASSISTANT_LLM_TEMPERATURE=0.7

# Embeddings
ASSISTANT_EMBED_MODEL=nomic-embed-text

# Memory
ASSISTANT_STM_MAX_TURNS=20
ASSISTANT_LTM_N_RESULTS=5

# Voice
ASSISTANT_VOICE_ENABLED=false
ASSISTANT_STT_MODEL_SIZE=base

# Owner
ASSISTANT_OWNER_TIMEZONE=America/New_York

```

---

## 🐳 Docker Services

| Service | Purpose | URL |
|---------|---------|-----|
| SearXNG | Local web search | http://localhost:8080 |

```bash
# Check if running
docker ps | grep -E "searxng"

# Stop service
docker stop searxng

# Start service again
docker start searxng
```

---

## 🧪 Testing

```bash
# Run all tests with coverage
pytest tests/ --cov=assistant

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Memory retrieval accuracy
pytest tests/accuracy/
```

Target coverage: **≥ 80%** for all core modules.

---

## 🗺️ Development Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| **1** | Core assistant — CLI chat, identity, basic memory | ✅ Done |
| **2** | Long-term semantic memory + session summarization | ✅ Done |
| **3** | Tool system — web search, email, notes | ✅ Done |
| **4** | Session + memory management, history export | ✅ Done |
| **5** | REST API + React frontend | ✅ Done |
| **6** | Voice interface — STT + TTS | ✅ Done |
---

## 🔒 Security Notes

- Passwords and API keys are loaded from `.env` only — never hardcoded
- All user data is stored in `~/.assistant/` — not in the repo
- Notes are stored in `~/assistant_notes/` on your local filesystem
- Conversation exports are saved to `~/assistant_exports/`
- Run `chmod 700 ~/.assistant` to restrict access to your OS user
- `.env` is gitignored by default — never commit it
- All services (Ollama, SearXNG) run locally — no data leaves your machine

---

## 📦 Dependencies

Key libraries used:

```toml
httpx              # Async HTTP client (Ollama + SearXNG API calls)
pydantic           # Data models + settings
chromadb           # Local vector database for long-term memory
faster-whisper     # Local speech-to-text
pyttsx3            # Text-to-speech
sounddevice        # Microphone input
rich               # Terminal UI
typer              # CLI framework
fastapi            # REST API backend
uvicorn            # ASGI server
```

Full list in `pyproject.toml`.

---

*Built for people who want a private AI companion that actually remembers them.*