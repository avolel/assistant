from duckduckgo_search import AsyncDDGS
from .base import BaseTool, ToolResult
from .registry import register_tool

@register_tool
class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the internet for current information."
    # Using duckduckgo_search for privacy-focused search results without API keys
    parameters = {
        "query": {"type": "string", "description": "Search query"},
        "max_results": {"type": "integer", "description": "Number of results (default 5)", "optional": True}
    }

    async def run(self, query: str, max_results: int = 5) -> ToolResult:
        if not query:
            return ToolResult(success=False, output="", error="Query is required")

        try:
            async with AsyncDDGS() as ddgs:
                results = [r async for r in ddgs.text(query, max_results=max_results)] 

            # DEBUG
            print(f"DEBUG DDG RAW RESULTS COUNT: {len(results)}")
            if results:
                print(f"DEBUG FIRST RESULT: {results[0]}")

            if not results:
                return ToolResult(success=False, output="", error="DuckDuckGo returned no results for that query.")

            output = "\n".join(f"- {r['title']}: {r['body']}" for r in results)
            return ToolResult(success=True, output=output) 
        except Exception as e:
            print(f"DEBUG DDG EXCEPTION: {type(e).__name__}: {e}")
            return ToolResult(success=False, output="", error=str(e))