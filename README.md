# 🤖 Always-On Personal AI Assistant

A fully local, always-on AI assistant that runs on your computer. Built with Python, it maintains a **persistent identity**, **evolving memory**, **emotional simulation**, and **time awareness** — designed to feel like a consistent digital personality rather than a stateless chatbot.

> No cloud required. No subscriptions. Your data stays on your machine.

---

## ✨ Features

- **Persistent Identity** — Give your assistant a name and personality that survives restarts
- **Memory System** — Short-term session memory + long-term semantic memory via vector embeddings
- **Learns About You** — Remembers facts, preferences, and past conversations over time
- **Emotional Simulation** — Internal mood, trust, stress, and engagement variables that influence responses
- **Time Awareness** — Knows the date, time, day of week, and can simulate availability/work hours
- **Tool System** — Plugin-style tools: web search, email sending, and note taking
- **Voice Interface** — Speak to your assistant and hear responses back (fully local STT/TTS)
- **Local LLM** — Runs with Ollama

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   USER INTERFACES                   │
│         CLI / Text UI         Voice Interface       │
└───────────────────┬─────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────┐
│              ASSISTANT CORE (Orchestrator)          │
│   Identity Manager  │  Conversation Engine          │
│   Time Awareness    │  Emotional State System       │
└────────────┬────────────────────────────────────────┘
             │
   ┌─────────┼─────────┐
   ▼         ▼         ▼
┌──────┐  ┌──────┐  ┌──────┐
│ LLM  │  │Memory│  │Tools │
│Layer │  │ STM  │  │Search│
│Ollama│  │ LTM  │  │Email │
│  HF  │  │Chroma│  │Notes │
└──────┘  └──────┘  └──────┘
             │
    ┌────────▼────────┐
    │ Persistence     │
    │ SQLite + Chroma │
    └─────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com) installed and running locally
- A pulled Ollama model (e.g. `ollama pull llama3`)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourname/assistant.git
cd assistant

# Install dependencies
pip install poetry
poetry install

# Copy and configure environment
cp .env.example .env
```

### First-Time Setup

```bash
python main.py setup
```

```
Welcome! Let's configure your assistant.
Assistant name: Aria
Your name: Alice
Your email (optional): alice@example.com
Your timezone: America/New_York
LLM provider [ollama]: ollama
LLM model [llama3]: llama3

✓ Identity created.
✓ Database initialized.
✓ Configuration saved to .env
Run `python main.py chat` to start.
```

### Start Chatting

```bash
# Text interface
python main.py chat

# Voice interface
python main.py voice
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
│   ├── llm/                       # LLM abstraction + provider
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

---

## 💬 Emotional State

The assistant maintains four internal variables that drift based on your interactions:

| Variable | Range | Baseline |
|----------|-------|---------|
| `mood` | 0.0–1.0 | 0.5 |
| `trust` | 0.0–1.0 | 0.5 |
| `stress` | 0.0–1.0 | 0.2 |
| `engagement` | 0.0–1.0 | 0.7 |

These variables influence the tone and willingness of responses. Positive interactions raise mood and trust; negative interactions increase stress. All values naturally drift back toward their baseline over time.

---

## 🔧 Tool System

Tools follow a simple plugin contract — subclass `BaseTool`, decorate, implement `run()`:

```python
from assistant.tools.base import BaseTool, ToolResult
from assistant.tools.registry import register_tool

@register_tool
class MyTool(BaseTool):
    name = "my_tool"
    description = "Does something useful."
    parameters = {"query": {"type": "string"}}

    async def run(self, query: str) -> ToolResult:
        result = do_something(query)
        return ToolResult(success=True, output=result)
```

### Built-in Tools

| Tool | Description |
|------|-------------|
| `web_search` | DuckDuckGo and SaerXng search (no API key needed) |
| `email_sender` | Send emails via SMTP |
| `notes` | Save and retrieve local markdown notes |

---

## 🤖 LLM Configuration

Switch models by changing two environment variables:

```env
ASSISTANT_LLM_PROVIDER=ollama
ASSISTANT_LLM_MODEL=llama3
```

| Provider | Models |
|----------|--------|
| `ollama` | llama3, mistral, phi3, gemma, etc. |

The LLM abstraction layer means adding a new provider only requires implementing one class.

---

## 🎤 Voice Interface

| Direction | Library | Notes |
|-----------|---------|-------|
| Speech → Text | `faster-whisper` | Local Whisper model, CPU/GPU |
| Text → Speech | `pyttsx3` | System TTS, zero install |
| Text → Speech (HQ) | Coqui `TTS` (XTTS-v2) | Near-human quality, local |

```bash
# Start voice mode
python main.py voice

# Push spacebar to speak, release to send
```

---

## ⚙️ Environment Variables

```env
# LLM
ASSISTANT_LLM_PROVIDER=ollama
ASSISTANT_LLM_MODEL=llama3
ASSISTANT_LLM_BASE_URL=http://localhost:11434

# Voice
ASSISTANT_VOICE_ENABLED=false
ASSISTANT_STT_MODEL_SIZE=base

# Owner
ASSISTANT_OWNER_TIMEZONE=America/New_York

# Email (for email tool)
ASSISTANT_SMTP_HOST=smtp.gmail.com
ASSISTANT_SMTP_USER=you@gmail.com
ASSISTANT_SMTP_PASS=your_app_password
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ --cov=assistant

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Memory retrieval accuracy
pytest tests/accuracy/

```
## 🔒 Security Notes

- Passwords and API keys are loaded from `.env` only — **never hardcoded**
- All user data is stored in `~/.assistant/` - **not in the repo**
- Set `chmod 700 ~/.assistant` to restrict access to your OS user
- `.env` is gitignored by default — **never committed**
---