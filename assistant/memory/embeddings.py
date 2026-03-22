# EmbeddingService converts text into a fixed-length vector of floats using Ollama's embedding model.
# These vectors capture semantic meaning — similar sentences produce similar vectors,
# enabling cosine similarity search in ChromaDB without keyword matching.
from typing import List
from ..config.settings import settings
import httpx


class EmbeddingService:
    def __init__(self, model: str = settings.embed_model,
                 base_url: str = settings.llm_base_url) -> None:
        self.model    = model
        self.base_url = base_url

    async def embed(self, text: str) -> List[float]:
        """Call Ollama's /api/embeddings endpoint and return the embedding vector for one text string.

        httpx.AsyncClient is the async equivalent of the `requests` library.
        `async with` ensures the HTTP connection is closed even if an error occurs.
        `await client.post(...)` suspends this coroutine until the HTTP response arrives,
        freeing the event loop to handle other requests in the meantime.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text}
            )
            response.raise_for_status()   # Raises an exception if status is 4xx or 5xx
            return response.json()["embedding"]   # List[float], e.g. 768 floats for nomic-embed-text

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts sequentially. For large batches, a true parallel approach would be faster."""
        return [await self.embed(t) for t in texts]