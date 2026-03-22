# Long-term memory uses ChromaDB, a local vector database.
# Instead of keyword search, it uses cosine similarity between embedding vectors
# to find semantically related memories even when wording differs.
#
# Dual storage: every memory is saved in BOTH ChromaDB (for vector search)
# and SQLite (for relational queries, listing, and deletion by ID).
import uuid, pathlib
from datetime import datetime, timezone
from typing import List, Dict, Optional
import chromadb
from .embeddings import EmbeddingService
from ..database.connection import get_db_connection
from chromadb.config import Settings
from ..config.settings import settings

CHROMA_PATH = pathlib.Path.home() / ".assistant" / "chroma"


class LongTermMemory:
    def __init__(self, owner_id: str, embed_service: EmbeddingService) -> None:
        self.owner_id = owner_id
        self.embed    = embed_service
        # PersistentClient saves the vector index to disk at CHROMA_PATH.
        # anonymized_telemetry=False suppresses ChromaDB's telemetry warning noise.
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_PATH),
            settings=Settings(anonymized_telemetry=False)
        )
        # A "collection" in ChromaDB is like a table — all memories share one collection here.
        # hnsw:space="cosine" sets the similarity metric; cosine works well for text embeddings.
        self.collection = self.client.get_or_create_collection(
            name="ltm_memories",
            metadata={"hnsw:space": "cosine"}
        )

    async def store(self, content: str, memory_type: str, importance: float = 0.5) -> str:
        """Embed the content and persist it in both ChromaDB and SQLite. Returns the new memory_id."""
        memory_id = str(uuid.uuid4())
        vector    = await self.embed.embed(content)   # List[float] — the embedding vector
        now       = datetime.now(timezone.utc).isoformat()

        # ChromaDB stores four parallel lists: ids, embeddings, documents (raw text), and metadata.
        # The where filter on owner_id ensures each user only retrieves their own memories.
        self.collection.add(
            ids=[memory_id],
            embeddings=[vector],                      # The numeric vector used for similarity search
            documents=[content],                      # Original text, returned in query results
            metadatas=[{
                "owner_id":    self.owner_id,
                "memory_type": memory_type,
                "importance":  importance,
                "created_at":  now
            }]
        )

        # Mirror in SQLite for API listing, deletion, and any non-vector queries.
        with get_db_connection() as db:
            db.execute(
                "INSERT INTO memories VALUES (?,?,?,?,?,?,?,?,?,?)",
                (memory_id, self.owner_id, memory_type, content,
                 importance, memory_id, 0, None, now, "{}")
            )
        return memory_id

    def list_memories(self, limit: int = 100, offset: int = 0,
                      memory_type: Optional[str] = None) -> List[Dict]:
        """List memories for this owner from SQLite, ordered by creation date descending."""
        with get_db_connection() as db:
            if memory_type:
                rows = db.execute(
                    "SELECT memory_id, memory_type, content, importance, created_at, last_accessed, access_count "
                    "FROM memories WHERE owner_id=? AND memory_type=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (self.owner_id, memory_type, limit, offset)
                ).fetchall()
            else:
                rows = db.execute(
                    "SELECT memory_id, memory_type, content, importance, created_at, last_accessed, access_count "
                    "FROM memories WHERE owner_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (self.owner_id, limit, offset)
                ).fetchall()
        return [
            {"memory_id": r[0], "memory_type": r[1], "content": r[2],
             "importance": r[3], "created_at": r[4], "last_accessed": r[5], "access_count": r[6]}
            for r in rows
        ]

    def delete(self, memory_id: str) -> bool:
        """Delete a memory from both ChromaDB and SQLite. Returns True if a row was deleted."""
        try:
            self.collection.delete(ids=[memory_id])
        except Exception:
            pass
        with get_db_connection() as db:
            result = db.execute(
                "DELETE FROM memories WHERE memory_id=? AND owner_id=?",
                (memory_id, self.owner_id)
            )
            return result.rowcount > 0

    async def update(self, memory_id: str, content: str) -> bool:
        """Re-embed updated content and persist it in both ChromaDB and SQLite."""
        vector = await self.embed.embed(content)
        try:
            self.collection.update(ids=[memory_id], embeddings=[vector], documents=[content])
        except Exception:
            pass
        with get_db_connection() as db:
            result = db.execute(
                "UPDATE memories SET content=? WHERE memory_id=? AND owner_id=?",
                (content, memory_id, self.owner_id)
            )
            return result.rowcount > 0

    async def query(self, query_text: str,
                    n_results: int = settings.ltm_n_results) -> List[Dict]:
        """Embed the query and return the n most similar memories for this owner.
        Returns a list of dicts with keys: memory_id, content, metadata, distance."""
        vector = await self.embed.embed(query_text)

        # ChromaDB raises an error if you request more results than exist in the collection.
        count    = self.collection.count()
        n_results = min(n_results, count)

        if n_results == 0:
            return []

        # query_embeddings accepts a list of vectors (batched queries). We send one at a time.
        # where= filters results to only this owner's memories before similarity ranking.
        results = self.collection.query(
            query_embeddings=[vector],
            n_results=n_results,
            where={"owner_id": self.owner_id}
        )

        # ChromaDB returns results as parallel lists nested under [0] (for the first query in the batch).
        # results["documents"][0] = list of raw text strings for the first query
        # results["ids"][0]       = list of memory IDs
        # results["distances"][0] = cosine distances (lower = more similar)
        memories = []
        for i, doc in enumerate(results["documents"][0]):
            memories.append({
                "memory_id": results["ids"][0][i],
                "content":   doc,
                "metadata":  results["metadatas"][0][i],
                "distance":  results["distances"][0][i]
            })
        return memories