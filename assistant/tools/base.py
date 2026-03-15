from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass
class ToolResult:
    success: bool
    output: str
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

# Base class for tools that the assistant can use. Each tool has a name, description, 
# and parameters, and must implement the run method.
class BaseTool(ABC):
    name: str = ""
    description: str = ""
    parameters: dict = {}
 
    @abstractmethod
    async def run(self, **kwargs) -> ToolResult:
        pass