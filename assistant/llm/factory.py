# Factory function: centralises provider construction so callers don't import concrete classes.
# To add a new provider (e.g. OpenAI), add an elif branch and a new class in its own module.
from .base import LLMProvider
from .ollama_provider import OllamaProvider
from ..config.settings import settings


def create_llm_provider(provider: str = settings.llm_provider, **kwargs) -> LLMProvider:
    """Instantiate and return the appropriate LLMProvider subclass.
    **kwargs are forwarded to the constructor (model, base_url, emotion_model, etc.).
    Raises ValueError for unknown provider names."""
    if provider == "ollama":
        return OllamaProvider(**kwargs)
    raise ValueError(f"Unknown provider: {provider}")