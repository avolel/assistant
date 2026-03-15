import uuid, pathlib
from datetime import datetime, timezone
from typing import List, Dict, Optional
import chromadb
from .embeddings import EmbeddingService
from ..database.connection import get_db_connection
from chromadb.config import Settings
from ..config.settings import settings

CHROMA_PATH = pathlib.Path.home() / ".assistant" / "chroma"

# Long-term memory system using ChromaDB for vector storage and retrieval.
class LongTermMemory:
    def __init__(self, owner_id: str,
        embed_service: EmbeddingService) -> None:
        self.owner_id = owner_id
        self.embed = embed_service
        self.client = chromadb.PersistentClient(path=str(CHROMA_PATH),
                                                settings=Settings(anonymized_telemetry=False))
        self.collection = self.client.get_or_create_collection(
            name="ltm_memories",
            metadata={"hnsw:space": "cosine"}
        )

    async def store(self, content: str, memory_type: str,
                    importance: float = 0.5) -> str:
        memory_id = str(uuid.uuid4())
        vector = await self.embed.embed(content)
        now = datetime.now(timezone.utc).isoformat()
        # Store the memory in ChromaDB with metadata for retrieval.
        self.collection.add(
            ids=[memory_id],
            embeddings=[vector], # Store the embedding vector for the content.
            documents=[content], # Store the original content for reference.
            metadatas=[{"owner_id": self.owner_id, "memory_type": memory_type,
                        "importance": importance, "created_at": now}] # Store metadata for filtering and sorting memories.
        )

        # Also store the memory in the SQLite database for additional metadata and retrieval options.
        with get_db_connection() as db:
            db.execute(
                "INSERT INTO memories VALUES (?,?,?,?,?,?,?,?,?,?)",
                (memory_id, self.owner_id, memory_type, content,
                 importance, memory_id, 0, None, now, "{}")
            )
        return memory_id
    
    # Query memories based on a text query, returning the most relevant memories 
    # with their metadata and distance scores.
    async def query(self, query_text: str,
                    n_results: int = settings.ltm_n_results) -> List[Dict]:
        vector = await self.embed.embed(query_text)

        count = self.collection.count()
        n_results = min(n_results, count)

        if n_results == 0:
            return [] 

        # Query ChromaDB for the most relevant memories based on cosine similarity of the embeddings.
        results = self.collection.query(
            query_embeddings=[vector],
            n_results=n_results, # Number of relevant memories to return.
            where={"owner_id": self.owner_id}
        )

        memories = []
        # Process the results to extract the memory content, metadata, 
        # and distance scores for each relevant memory.
        for i, doc in enumerate(results["documents"][0]):
            memories.append({
                "memory_id": results["ids"][0][i],
                "content": doc,
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })
        return memories