from typing import Dict, Type, List
from .base import BaseTool

# Registry for tools that the assistant can use. 
# Tools can be registered with a name and description, and can be retrieved by name.
_REGISTRY: Dict[str, BaseTool] = {}

# Decorator to register a tool class in the registry. 
# The tool class must inherit from BaseTool and have a unique name.
def register_tool(cls: Type[BaseTool]) -> Type[BaseTool]:
    _REGISTRY[cls.name] = cls() # Instantiate the tool and store it in the registry
    return cls

class ToolRegistry:
    # Retrieve a tool instance by name. Raises KeyError if the tool is not registered.
    def get(self, name: str) -> BaseTool:
        if name not in _REGISTRY:
            raise KeyError(f"Tool '{name}' not registered")
        return _REGISTRY[name]
    
    # Return a list of all registered tool instances. 
    def all_tools(self) -> List[BaseTool]:
        return list(_REGISTRY.values())
 
    def manifest_text(self) -> str:
        lines = ["## Available Tools",
                 "Call a tool by responding with: TOOL_CALL: tool_name | param: value",
                 ""]
        for tool in self.all_tools():
            lines.append(f"- {tool.name}: {tool.description}")
            for param_name, param_info in tool.parameters.items():
                lines.append(f"    {param_name} ({param_info['type']}): {param_info.get('description','')}")
        return "\n".join(lines)
    
    # Return tool definitions in Ollama's native tool format.
    def to_ollama_tools(self) -> List[dict]:
        ollama_tools = []
        for tool in self.all_tools():
            ollama_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            k: {"type": v["type"], "description": v.get("description", "")}
                            for k, v in tool.parameters.items()
                        },
                        "required": [
                            k for k, v in tool.parameters.items()
                            if not v.get("optional", False)
                        ]
                    }
                }
            })
        return ollama_tools