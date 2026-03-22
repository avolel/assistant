# Base classes for the tool system.
# Every tool must subclass BaseTool and implement run().
# ToolResult is what run() returns — a structured success/error envelope.
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ToolResult:
    """Envelope returned by every tool. Callers check success before using output."""
    success: bool
    output:  str                              # Human-readable result string (injected back into the LLM)
    data:    Dict[str, Any] = field(default_factory=dict)  # Optional structured data
    error:   Optional[str] = None            # Error message when success=False


class BaseTool(ABC):
    """Abstract base for all tools. Class-level attributes (name, description, parameters)
    define the tool's identity and are read by ToolRegistry to build the Ollama tool manifest."""
    name:        str  = ""
    description: str  = ""
    parameters:  dict = {}   # {param_name: {type, description, optional?}}

    @abstractmethod
    async def run(self, **kwargs) -> ToolResult:
        """Execute the tool with the given keyword arguments and return a ToolResult."""
        pass