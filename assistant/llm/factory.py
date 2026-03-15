from .base import LLMProvider
from .ollama_provider import OllamaProvider

# Factory function to create LLM providers based on the specified provider name
def create_llm_provider(provider: str = "ollama", **kwargs) -> LLMProvider:
    if provider == "ollama":
        return OllamaProvider(**kwargs)
    raise ValueError(f"Unknown provider: {provider}")