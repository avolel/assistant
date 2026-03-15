from typing import List
from ..config.settings import settings
import httpx

# Generates vector embeddings using Ollama (fully local).
class EmbeddingService:
    def __init__(self, model: str = settings.embed_model,
                 base_url: str = settings.llm_base_url) -> None:
        self.model = model
        self.base_url = base_url

    # Generate an embedding for the given text.
    async def embed(self, text: str) -> List[float]:
        # Ollama's embedding endpoint expects a POST request with the model and prompt in the JSON body.
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text}
            )
            response.raise_for_status()
            return response.json()["embedding"]
        
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [await self.embed(t) for t in texts]