from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, List, Optional

# Data classes for LLM messages and responses
@dataclass
class LLMMessage:
    role: str      # "system" | "user" | "assistant"
    content: str

@dataclass
class LLMResponse:
    content: str
    model: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None

# Base class for LLM providers
class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, 
                       messages: List[LLMMessage], 
                       mtemperature: float = 0.7,
                       max_tokens: int = 2048) -> LLMResponse:
        pass

    @abstractmethod
    async def stream(self, 
                     messages: List[LLMMessage], 
                     temperature: float = 0.7) -> AsyncIterator[str]:
        pass