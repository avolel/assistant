# OllamaProvider implements LLMProvider for a locally running Ollama instance.
# Ollama exposes an OpenAI-compatible /api/chat endpoint, so request/response shapes are similar.
import httpx, json
from typing import AsyncIterator, List
from .base import LLMProvider, LLMMessage, LLMResponse
from ..config.settings import settings


class OllamaProvider(LLMProvider):
    def __init__(self,
                 model:         str = settings.llm_model,
                 base_url:      str = settings.llm_base_url,
                 emotion_model: str = settings.llm_model_emotion) -> None:
        self.model         = model           # Main conversational model
        self.base_url      = base_url        # e.g. "http://localhost:11434"
        self.emotion_model = emotion_model   # Smaller model used only for sentiment classification

    async def emotion_analysis(self, user_message: str) -> str:
        """Classify the emotional tone of a message as POSITIVE, NEGATIVE, or RUDE.
        Uses a separate (typically smaller/faster) model than the main conversation model."""
        payload = {
            "model": self.emotion_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an emotion classifier. "
                        "Analyze the emotional tone of the user's message and respond with a single word only. "
                        "Your response must be exactly one of: POSITIVE, NEGATIVE or RUDE. "
                        "No explanation, no punctuation, no other text. Just the single word."
                    )
                },
                {
                    "role":    "user",
                    "content": user_message
                }
            ],
            "stream":  False,
            "options": {"temperature": 0.7, "num_predict": 2048}
        }

        # httpx.AsyncClient is a session that reuses the TCP connection.
        # `async with` ensures it's closed when the block exits, even on exceptions.
        # timeout=120.0 is generous — local LLM inference can be slow on CPU.
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                data    = response.json()
                message = data.get("message", {})
                content = message.get("content", "")
                return content.strip()
            except httpx.HTTPError as e:
                print(f"DEBUG HTTP ERROR (Emotion Analysis): {e.response.status_code} — {e.response.text}")
                raise
            except Exception as e:
                print(f"{payload}")
                print(f"DEBUG UNEXPECTED ERROR (Emotion Analysis): {type(e).__name__}: {e}")
                raise

    async def classify_memory(self, user_message: str) -> str:
        """Classify whether the message is worth storing long-term and what type it is.
        Uses the emotion model (fast/small). Returns one of: user_fact | preference | event | summary | none"""
        payload = {
            "model": self.emotion_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a memory classifier. Analyze the user's message and decide if it is a "
                        "declarative statement that contains new information worth storing long-term. "
                        "Questions, requests, and commands must always return 'none' — only statements qualify.\n"
                        "Respond with exactly one word — no explanation, no punctuation:\n"
                        "  user_fact  — a statement of personal fact (name, job, family, location, age, etc.)\n"
                        "  preference — a statement of something the user likes, dislikes, or prefers\n"
                        "  event      — a statement about something that happened or is planned\n"
                        "  summary    — a statement that summarises information\n"
                        "  none       — a question, request, command, or message with no long-term memory value"
                    )
                },
                {"role": "user", "content": user_message}
            ],
            "stream":  False,
            "options": {"temperature": 0.0, "num_predict": 10}
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                content = response.json().get("message", {}).get("content", "none").strip().lower()
                # Normalise — model may return "user_fact." or extra whitespace
                for valid in ("user_fact", "preference", "event", "summary"):
                    if valid in content:
                        return valid
                return "none"
            except Exception:
                return "none"   # Fail silently — memory classification is non-critical

    async def complete(self,
                       messages:    List[LLMMessage],
                       temperature: float = 0.7,
                       max_tokens:  int   = 2048,
                       tools:       List[dict] = None) -> LLMResponse:
        """Send a list of messages to Ollama and return the full response.
        If `tools` is provided, the model may return a tool_calls list instead of (or alongside) content."""
        payload = {
            "model":    self.model,
            # List comprehension converts LLMMessage dataclass objects to plain dicts for JSON serialization.
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream":   False,
            "options":  {"temperature": temperature, "num_predict": max_tokens}
        }

        # Only include tools in the payload if they were provided.
        # Models that don't support tool calling will error if an empty list is sent.
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()

                message    = data.get("message", {})
                content    = message.get("content", "")
                tool_calls = message.get("tool_calls", [])  # Empty list if model didn't call a tool

                return LLMResponse(content=content, model=self.model, tool_calls=tool_calls)
            except httpx.HTTPError as e:
                print(f"DEBUG HTTP ERROR: {e.response.status_code} — {e.response.text}")
                raise
            except Exception as e:
                print(f"DEBUG UNEXPECTED ERROR: {type(e).__name__}: {e}")
                raise

    async def stream(self,
                     messages:    List[LLMMessage],
                     temperature: float = 0.7) -> AsyncIterator[str]:
        """Stream response tokens as they are generated. Yields one string fragment at a time.
        The caller uses `async for token in provider.stream(...)` to receive tokens."""
        payload = {
            "model":    self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "options":  {"temperature": temperature},
            "stream":   True   # Ollama sends back newline-delimited JSON objects as tokens arrive
        }

        # `client.stream(...)` keeps the response body open for reading line by line.
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                response.raise_for_status()
                # aiter_lines() yields each newline-delimited JSON string as it arrives.
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        # done=True is the final sentinel message — skip it to avoid yielding empty string.
                        if not data.get("done"):
                            yield data["message"]["content"]