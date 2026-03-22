# Tool registry: a module-level dict that maps tool names to instances.
# Tools self-register by applying the @register_tool decorator to their class.
# The ConversationEngine imports the tool modules to trigger registration as a side effect.
from typing import Dict, Type, List
from .base import BaseTool

# Module-level dict — acts as a singleton registry shared across the whole process.
_REGISTRY: Dict[str, BaseTool] = {}


def register_tool(cls: Type[BaseTool]) -> Type[BaseTool]:
    """Decorator that instantiates a BaseTool subclass and adds it to the registry.
    Usage: @register_tool on a class definition.
    The decorator receives the class object, not an instance, so cls() creates the instance."""
    _REGISTRY[cls.name] = cls()   # Instantiate once at import time
    return cls                    # Return the class unchanged so it can still be used normally


class ToolRegistry:
    """Interface for looking up tools and generating the Ollama-format tool manifest."""

    def get(self, name: str) -> BaseTool:
        """Retrieve a tool by name. Raises KeyError if not registered."""
        if name not in _REGISTRY:
            raise KeyError(f"Tool '{name}' not registered")
        return _REGISTRY[name]

    def all_tools(self) -> List[BaseTool]:
        """Return all registered tool instances."""
        return list(_REGISTRY.values())

    def manifest_text(self) -> str:
        """Generate a plain-text tool manifest for models that use the TOOL_CALL: text fallback."""
        lines = ["## Available Tools",
                 "Call a tool by responding with: TOOL_CALL: tool_name | param: value",
                 ""]
        for tool in self.all_tools():
            lines.append(f"- {tool.name}: {tool.description}")
            for param_name, param_info in tool.parameters.items():
                lines.append(f"    {param_name} ({param_info['type']}): {param_info.get('description', '')}")
        return "\n".join(lines)

    def to_ollama_tools(self) -> List[dict]:
        """Convert all registered tools into Ollama's native tool-calling JSON format.
        This is sent in the `tools` field of the /api/chat request payload.
        The `required` list excludes parameters marked optional=True so the model
        only includes them when contextually appropriate."""
        ollama_tools = []
        for tool in self.all_tools():
            ollama_tools.append({
                "type": "function",
                "function": {
                    "name":        tool.name,
                    "description": tool.description,
                    "parameters":  {
                        "type":       "object",
                        "properties": {
                            k: {"type": v["type"], "description": v.get("description", "")}
                            for k, v in tool.parameters.items()
                        },
                        # Include a param in `required` only if it is NOT marked optional.
                        "required": [
                            k for k, v in tool.parameters.items()
                            if not v.get("optional", False)
                        ]
                    }
                }
            })
        return ollama_tools