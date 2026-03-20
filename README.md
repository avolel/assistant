# 🤖 Always-On Personal AI Assistant

A fully local, always-on AI assistant that runs on your computer. Built with Python, it maintains a **persistent identity**, **evolving memory**, **emotional simulation**, and **time awareness** — designed to feel like a consistent digital personality rather than a stateless chatbot.

> No cloud required. No subscriptions. Your data stays on your machine.

> ⚠️ This project is currently in active development. Core functionality is working but some features are still being built out.

---

## ✨ Features

- **Persistent Identity** — Give your assistant a name and personality that survives restarts
- **Memory System** — Short-term session memory + long-term semantic memory via vector embeddings
- **Learns About You** — Remembers facts, preferences, and past conversations over time
- **Emotional Simulation** — Internal mood, trust, stress, and engagement variables that influence responses
- **Time Awareness** — Knows the date, time, day of week, and can simulate availability/work hours
- **Tool System** — Plugin-style tools with native LLM tool calling support
- **Web Search** — Fully local search via SearXNG, no API keys, no rate limits, nothing leaves your machine
- **Notes** — Save and retrieve markdown notes stored locally on disk
- **Voice Interface** — Speak to your assistant and hear responses back (fully local STT/TTS)
- **Local LLM** — Runs with Ollama; supports any model including native tool-calling models

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERFACES                        │
│         [CLI / Terminal]   [Voice / STT]   [Web / API]      │
└───────────────────────────┬─────────────────────────────────┘
                            │ Input / Output loop
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              ASSISTANT CORE (Orchestrator)                  │
│  ┌──────────────────────┐      ┌──────────────────────────┐ │
│  │   Identity / Persona │◄────►│   Reasoning & Logic      │ │
│  └──────────────────────┘      └──────────────────────────┘ │
│  ┌──────────────────────┐      ┌──────────────────────────┐ │
│  │  Time / Context Aware│◄────►│  Emotion / Tone Engine   │ │
│  └──────────────────────┘      └──────────────────────────┘ │
└────────────┬──────────────────────┬──────────────┬──────────┘
             │                      │              │
     ┌───────▼──────┐     ┌─────────▼──────┐  ┌───▼────────┐
     │  LLM LAYER   │     │    MEMORY       │  │   TOOLS    │
     │ (Inference)  │     │  (Context)      │  │ (Actions)  │
     ├──────────────┤     ├─────────────────┤  ├────────────┤
     │ Ollama/Local │     │ STM (Buffer)    │  │ Web Search │
     │ Remote APIs  │     │ LTM (Vector)    │  │Notes/Files │
     └───────┬──────┘     └─────────┬───────┘  └───┬────────┘
             │                      │               │
             └──────────────┬───────┘───────────────┘
                            ▼
     ┌──────────────────────────────────────────────────────┐
     │                  PERSISTENCE LAYER                   │
     │    [SQLite: Logs / Meta]    [ChromaDB: Embeddings]   │
     └──────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com) installed and running locally
- Docker (for SearXNG web search)
- A pulled Ollama model — a native tool-calling model is recommended

```bash
ollama pull gpt-oss:20b
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
# SearXNG — local web search (required for web search tool)
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
LLM model [gpt-oss:20b]: gpt-oss:20b

✓ Identity created.
✓ Database initialized.
✓ Configuration saved to .env
Run `python main.py chat` to start.
```

### Start Chatting

```bash
# Text interface
python main.py chat
```
---

## 📁 Project Structure

```
assistant/
├── main.py                        # Entry point
├── pyproject.toml
├── .env.example
│
├── assistant/
│   ├── core/                      # Orchestrator, identity, session
│   ├── conversation/              # Engine, prompt builder, history
│   ├── memory/                    # STM + LTM, embeddings, summarizer
│   ├── emotions/                  # Emotional state + update engine
│   ├── time_awareness/            # Time context + availability
│   ├── llm/                       # LLM abstraction + providers
│   ├── tools/                     # Plugin registry + built-in tools
│   ├── voice/                     # STT + TTS services
│   ├── database/                  # SQLite connection + migrations
│   └── config/                    # Pydantic settings + defaults
│
└── tests/
    ├── unit/
    ├── integration/
    └── accuracy/
```

---

## 🧠 Memory System

The assistant uses a **hybrid memory architecture**:

| Store | Technology | Used For |
|-------|-----------|----------|
| Short-Term Memory | SQLite | Current session turns (last 20) |
| Long-Term Memory | ChromaDB (vector DB) | Semantic recall across sessions |
| User Facts | ChromaDB collection | Preferences, personal info |
| Conversation Summaries | ChromaDB collection | Compressed past sessions |

Long-term memories are embedded using **Ollama's `nomic-embed-text`** model and retrieved via cosine similarity — so the assistant can answer *"what do you know about my job?"* without keyword matching.

> **Note:** ChromaDB telemetry warnings are suppressed by passing `settings=Settings(anonymized_telemetry=False)` 
> when initializing the ChromaDB client in `assistant/memory/long_term.py`. No `.env` changes required.

---

## 💬 Emotional State

The assistant maintains four internal variables that drift based on your interactions:

| Variable | Range | Baseline |
|----------|-------|---------|
| `mood` | 0.0–1.0 | 0.5 |
| `trust` | 0.0–1.0 | 0.5 |
| `stress` | 0.0–1.0 | 0.2 |
| `engagement` | 0.0–1.0 | 0.7 |

Positive interactions raise mood and trust. Negative or rude interactions increase stress and reduce trust. All values naturally drift back toward their baseline over time. These states subtly influence the tone of every response without being mentioned explicitly.

---

## 🔧 Tool System

Tools use **native LLM tool calling** — the model receives structured JSON tool definitions and returns structured `tool_calls` responses. No text parsing, no fragile regex, no custom prompt formatting required. The tool definitions are built automatically from each tool's `name`, `description`, and `parameters` attributes and sent to Ollama with every request.

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

Parameters marked `optional: True` are excluded from the `required` list sent to the model, so it only passes them when the context calls for it.

### Built-in Tools

| Tool | Backend | Description |
|------|---------|-------------|
| `web_search` | SearXNG (local Docker) | Search the web with no API key and no rate limits |
| `notes` | Local filesystem | Save and retrieve markdown notes in `~/assistant_notes/` |

---

## 🔍 Web Search

Web search is powered by **SearXNG** running locally in Docker. This means:

- No API key required
- No rate limiting
- No search queries sent to third parties
- Results aggregated from multiple search engines locally

The SearXNG web UI is available at `http://localhost:8080` while the container is running.

```
You: Search the web for upcoming DJ Puffy shows
Aria: Here's what I found...
```

## 🤖 LLM Configuration

The assistant uses **Ollama** with any locally pulled model. Native tool-calling models work best as they return structured `tool_calls` JSON rather than relying on text formatting in the response.

```env
ASSISTANT_LLM_PROVIDER=ollama
ASSISTANT_LLM_MODEL=gpt-oss:20b
ASSISTANT_LLM_BASE_URL=http://localhost:11434
```

The LLM abstraction layer means adding a new provider only requires implementing one class that extends `LLMProvider`.

---

## 🎤 Voice Interface **Still In Development**

| Direction | Library | Notes |
|-----------|---------|-------|
| Speech → Text | `faster-whisper` | Local Whisper model, CPU/GPU |
| Text → Speech | `pyttsx3` | System TTS, zero install |
| Text → Speech (HQ) | Coqui `TTS` (XTTS-v2) | Near-human quality, fully local |

---

## ⚙️ Environment Variables

```env
# LLM
ASSISTANT_LLM_PROVIDER=ollama
ASSISTANT_LLM_MODEL=gpt-oss:20b
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

| Service | Purpose | Port |
|---------|---------|------|
| SearXNG | Local web search | UI: http://localhost:8080 |

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

```

Target coverage: **≥ 80%** for all core modules.

---

## 🗺️ Development Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| **1** | Core assistant — CLI chat, identity, basic memory | ✅ Done |
| **2** | Long-term semantic memory + session summarization | ✅ Done |
| **3a** | Tool system — web search | ✅ Done |
| **3c** | Tool system — notes | ✅ Done |
| **4** | Voice interface — STT + TTS | ✅ Done |
| **5** | Emotional simulation |  ✅ Done |

---

## 🔒 Security Notes

- Passwords and API keys are loaded from `.env` only — never hardcoded
- All user data is stored in `~/.assistant/` — not in the repo
- Notes are stored in `~/assistant_notes/` on your local filesystem
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