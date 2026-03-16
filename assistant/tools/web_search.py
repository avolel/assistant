import httpx
from .base import BaseTool, ToolResult
from .registry import register_tool

SEARXNG_URL = "http://localhost:8080/search"

@register_tool
class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the internet for current information."
    parameters = {
        "query":       {"type": "string",  "description": "The search query"},
        "max_results": {"type": "integer", "description": "Number of results to return", "optional": True}
    }

    async def run(self, query: str, max_results: int = 5) -> ToolResult:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(
                    SEARXNG_URL,
                    params={
                        "q":                 query,
                        "format":            "json",
                        "number_of_results": max_results,
                        "language":          "en",
                        "safesearch":        "0",
                    }
                )
                r.raise_for_status()
                data = r.json()

            results = data.get("results", [])

            if not results:
                return ToolResult(
                    success=False,
                    output="",
                    error="SearXNG returned no results for that query."
                )

            output = "\n".join(
                f"- {r.get('title', 'No title')}: {r.get('content', r.get('url', ''))}"
                for r in results[:max_results]
            )
            return ToolResult(success=True, output=output)

        except httpx.ConnectError:
            return ToolResult(
                success=False,
                output="",
                error="Could not connect to SearXNG. Is Docker running? Check http://localhost:8080"
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))