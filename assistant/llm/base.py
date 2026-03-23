# Abstract base classes define the interface that all LLM providers must implement.
# This decouples the rest of the codebase from any specific provider (Ollama, OpenAI, etc.).
# To add a new provider, subclass LLMProvider and implement the two abstract methods.
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, List, Optional


@dataclass
class LLMMessage:
    """A single message in the conversation, matching the OpenAI/Ollama chat message format."""
    role:    str    # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    """The full response from an LLM call, including optional native tool_calls."""
    content:           str
    model:             str
    prompt_tokens:     Optional[int] = None
    completion_tokens: Optional[int] = None
    # tool_calls is populated when the model decides to invoke a tool instead of (or before) replying.
    # Each entry is a dict in OpenAI-compatible format: { "function": { "name": ..., "arguments": {...} } }
    tool_calls:        List[dict] = field(default_factory=list)


# ABC (Abstract Base Class) from the `abc` module.
# A class that inherits from ABC cannot be instantiated directly — it's a contract.
# @abstractmethod forces subclasses to implement the method or they'll raise TypeError at instantiation.
class LLMProvider(ABC):

    @abstractmethod
    async def classify_memory(self, user_message: str) -> str:
        """Classify whether a message is worth storing and what type it is.
        Returns one of: user_fact | preference | event | summary | none"""
        pass

    @abstractmethod
    async def complete(self,
                       messages:    List[LLMMessage],
                       temperature: float = 0.7,
                       max_tokens:  int   = 2048,
                       tools:       List[dict] = None) -> LLMResponse:
        """Send a list of messages and return a full (non-streaming) response."""
        pass

    @abstractmethod
    async def stream(self,
                     messages:    List[LLMMessage],
                     temperature: float = 0.7) -> AsyncIterator[str]:
        """Send messages and yield response tokens as they arrive (for streaming UIs)."""
        pass