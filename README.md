# Personal AI Assistant

A fully local, always-on AI assistant that runs entirely on your machine. Built with Python, it maintains a **persistent identity**, **evolving memory**, **emotional simulation**, and **time awareness** — designed to feel like a consistent digital personality rather than a stateless chatbot.

> No cloud. No subscriptions. Your data never leaves your machine.

---

## Features

- **Persistent Identity** — Name and personality that survive restarts
- **Hybrid Memory** — Short-term session memory (SQLite) + long-term semantic recall (ChromaDB)
- **Session Management** — List, resume, delete, and export past conversation sessions
- **Conversation Export** — Export sessions to plain text, markdown, or JSON
- **Emotional Simulation** — LLM-powered sentiment analysis drives internal mood, trust, stress, and engagement that subtly influence every response
- **Time Awareness** — Knows the date, time, day of week, and simulates work-hour availability
- **Tool System** — Native LLM tool calling (structured JSON, no regex parsing)
- **Web Search** — Fully local via SearXNG in Docker — no API keys, no rate limits
- **Notes** — Save, list, and read markdown notes stored locally on disk
- **Voice Interface** — Local STT via faster-whisper + TTS via pyttsx3 or Coqui
- **REST API** — FastAPI backend with Swagger docs at `/docs`
- **React Frontend** — Chat UI with markdown rendering and live mood indicator
- **Single Owner** — One assistant identity dedicated to one owner, with persistent profile, sessions, and memories

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     USER INTERFACES                      │
│              React Frontend          Voice               │
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
└─────────┬────────────────────────────────────────────────┘
          │
   ┌──────┼──────────┐
   ▼      ▼          ▼
┌──────┐ ┌────────┐ ┌───────┐
│ LLM  │ │ Memory │ │ Tools │
│Layer │ │  STM   │ │Search │
│Ollama│ │  LTM   │ │Notes  │
└──────┘ └───┬────┘ └───────┘
             ▼
   ┌──────────────────┐
   │    Persistence   │
   │ SQLite + ChromaDB│
   └──────────────────┘
```

**Request flow:**
1. User sends message via React frontend → API → ConversationEngine
2. Relevant long-term memories retrieved via semantic search
3. User message classified as POSITIVE / NEGATIVE / RUDE → emotional state updated
4. System prompt built from identity + time context + emotional state
5. LLM called with available tool definitions
6. If model issues a tool call → executed and result returned to model
7. Final response stored in short-term memory, important facts stored in long-term memory
8. Response returned with current emotional state

---

## Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com) installed and running
- Docker (for SearXNG web search)

```bash
ollama pull llama3
ollama pull nomic-embed-text   # required for long-term memory
```

### Installation

```bash
git clone https://github.com/avolel/assistant.git
cd assistant

pip install poetry
poetry install

cp .env.example .env
```

### Start Required Services

```bash
# SearXNG — local web search (no API key, no rate limits)
docker run -d \
  --name searxng \
  -p 8080:8080 \
  -e SEARXNG_SECRET_KEY=changeme \
  --restart unless-stopped \
  searxng/searxng

# Enable JSON API (run once after first start)
docker exec searxng sed -i 's/formats:/formats:\n    - json/' /etc/searxng/settings.yml
docker restart searxng
```

### Run

```bash
python run.py
# http://localhost:8000        React frontend
# http://localhost:8000/docs   Swagger UI
```

---

## Memory System

| Store | Technology | Purpose |
|-------|-----------|---------|
| Short-Term Memory | SQLite | Current session turns (last N, auto-trimmed) |
| Long-Term Memory | ChromaDB | Semantic recall across sessions |
| User Facts | ChromaDB collection | Preferences and personal info |
| Conversation Summaries | ChromaDB collection | Compressed past sessions |

Long-term memories are embedded with Ollama's `nomic-embed-text` model and retrieved via cosine similarity. This enables natural queries like *"what do you know about my job?"* without keyword matching.

Data is stored at:
- SQLite database: `~/.assistant/assistant.db`
- ChromaDB vectors: `~/.assistant/chroma/`
- Notes: `~/assistant_notes/`
- Exports: `~/assistant_exports/`

---

## Emotional State

Every user message is classified as `POSITIVE`, `NEGATIVE`, or `RUDE` by a small LLM. This drives four internal state variables that influence response tone:

| Variable | Range | Baseline |
|----------|-------|---------|
| `mood` | 0.0–1.0 | 0.5 |
| `trust` | 0.0–1.0 | 0.5 |
| `stress` | 0.0–1.0 | 0.2 |
| `engagement` | 0.0–1.0 | 0.7 |

Positive interactions raise mood and trust. Negative interactions increase stress. Rude interactions significantly reduce trust and engagement. All values drift back toward their baseline over time. The emotional state is injected into the system prompt on every turn and persists across restarts.

---

## Tool System

Tools use native LLM tool calling — the model receives structured JSON definitions and returns structured `tool_calls` responses. No text parsing, no regex.

Adding a tool:

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

Parameters marked `optional: True` are excluded from the `required` field sent to the model. Import the module in `assistant/conversation/engine.py` and the tool is registered automatically.

### Built-in Tools

| Tool | Backend | Description |
|------|---------|-------------|
| `web_search` | SearXNG (local Docker) | Search the web with no API key and no rate limits |
| `notes` | Local filesystem | Save, list, and read markdown notes |

---

## REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/identity/` | Get assistant identity |
| `POST` | `/api/identity/setup` | First-time setup |
| `PATCH` | `/api/identity/` | Rename assistant |
| `PATCH` | `/api/identity/owner` | Update owner info |
| `POST` | `/api/chat/` | Send a message |
| `GET` | `/api/memory/` | List all memories |
| `POST` | `/api/memory/search` | Semantic memory search |
| `POST` | `/api/memory/` | Store a memory manually |
| `PATCH` | `/api/memory/{id}` | Update a memory |
| `DELETE` | `/api/memory/{id}` | Delete a memory |
| `GET` | `/api/sessions/` | List all sessions |
| `GET` | `/api/sessions/{id}` | Get session + turn history |
| `GET` | `/api/sessions/{id}/export` | Export session (`?format=json\|markdown\|text`) |
| `DELETE` | `/api/sessions/{id}` | Delete a session |
| `POST` | `/api/voice/listen` | Record audio and transcribe |
| `POST` | `/api/voice/transcribe` | Upload audio file for transcription |
| `POST` | `/api/voice/speak` | Synthesize speech from text |

---

## Voice Interface

| Direction | Library | Notes |
|-----------|---------|-------|
| Speech → Text | `faster-whisper` | Local Whisper model, CPU/GPU |
| Text → Speech | `pyttsx3` | System TTS, zero install |
| Text → Speech (HQ) | Coqui `TTS` (XTTS-v2) | Near-human quality, fully local |

Requires PortAudio on Linux:

```bash
sudo apt install -y portaudio19-dev
```

---

## LLM Configuration

```env
ASSISTANT_LLM_PROVIDER=ollama
ASSISTANT_LLM_MODEL=llama3
ASSISTANT_LLM_MODEL_EMOTION=llama3.1:8b
ASSISTANT_LLM_BASE_URL=http://localhost:11434
ASSISTANT_LLM_TEMPERATURE=0.7
```

Any Ollama model works. Native tool-calling models (that return structured `tool_calls` JSON) work best. Adding a new provider requires implementing the `LLMProvider` abstract base class in `assistant/llm/base.py`.

---

## Environment Variables

```env
# LLM
ASSISTANT_LLM_PROVIDER=ollama
ASSISTANT_LLM_MODEL=llama3
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

## Project Structure

```
assistant/
├── run.py                         # Server entry point (uvicorn)
├── pyproject.toml
├── .env.example
│
├── assistant/
│   ├── core/
│   │   ├── assistant.py           # AssistantCore orchestrator
│   │   ├── identity.py            # IdentityManager + OwnerProfile
│   │   └── session.py             # Session lifecycle
│   │
│   ├── conversation/
│   │   ├── engine.py              # Main chat loop + tool execution
│   │   ├── prompt_builder.py      # System prompt construction
│   │   └── history.py             # History trimming + export
│   │
│   ├── memory/
│   │   ├── manager.py             # MemoryManager facade
│   │   ├── short_term.py          # Recent turns (SQLite)
│   │   ├── long_term.py           # Semantic store (ChromaDB)
│   │   ├── embeddings.py          # Embedding generation (Ollama)
│   │   └── summarizer.py          # Session compression
│   │
│   ├── emotions/
│   │   ├── state.py               # EmotionalState model
│   │   ├── engine.py              # Sentiment-driven state updates
│   │   └── store.py               # Emotional state persistence
│   │
│   ├── time_awareness/
│   │   └── service.py             # Time context + work hour tracking
│   │
│   ├── llm/
│   │   ├── base.py                # LLMProvider abstract base
│   │   ├── ollama_provider.py     # Ollama implementation
│   │   └── factory.py             # Provider factory
│   │
│   ├── tools/
│   │   ├── registry.py            # Tool registry + Ollama manifest
│   │   ├── base.py                # BaseTool + ToolResult
│   │   ├── web_search.py          # SearXNG integration
│   │   └── notes.py               # Local markdown notes
│   │
│   ├── api/
│   │   ├── app.py                 # FastAPI application
│   │   ├── models.py              # Request/response models
│   │   ├── session_store.py       # In-memory session store
│   │   └── routes/
│   │       ├── chat.py
│   │       ├── identity.py
│   │       ├── memory.py
│   │       ├── sessions.py
│   │       ├── voice.py
│   │       └── health.py
│   │
│   ├── voice/
│   │   ├── stt.py                 # Speech-to-text (faster-whisper)
│   │   └── tts.py                 # Text-to-speech (pyttsx3 / Coqui)
│   │
│   ├── database/
│   │   ├── connection.py          # SQLite context manager (WAL mode)
│   │   ├── migrations.py          # Schema initialization
│   │   └── schema.sql             # Database schema
│   │
│   └── config/
│       └── settings.py            # Pydantic settings
│
├── frontend/                      # React + Vite + Tailwind chat UI
│
└── tests/
    ├── unit/
    ├── integration/
    └── accuracy/
```

---

## Security

- All credentials are loaded from `.env` — never hardcoded
- `.env` is gitignored — never commit it
- All user data stored in `~/.assistant/` on your local filesystem
- All services (Ollama, SearXNG) run locally — nothing leaves your machine
- Run `chmod 700 ~/.assistant` to restrict access to your OS user

---

## Testing

```bash
pytest tests/ --cov=assistant     # All tests with coverage
pytest tests/unit/                # Unit tests
pytest tests/integration/         # Integration tests
pytest tests/accuracy/            # Memory retrieval accuracy
```

---

## Dependencies

```toml
httpx              # Async HTTP (Ollama + SearXNG)
pydantic           # Data models + settings
chromadb           # Vector database for long-term memory
faster-whisper     # Local speech-to-text
pyttsx3            # Text-to-speech
sounddevice        # Microphone input
fastapi            # REST API
uvicorn            # ASGI server
```

Full list in `pyproject.toml`.