# Memory routes: list, update, and delete long-term memories.
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ...memory.long_term import LongTermMemory
from ...memory.embeddings import EmbeddingService
from ...core.identity import IdentityManager

router = APIRouter()


class UpdateMemoryBody(BaseModel):
    content: str


def _get_ltm() -> LongTermMemory:
    """Load the first owner's LongTermMemory instance. Raises 400 if not configured."""
    mgr      = IdentityManager()
    identity = mgr.load()
    if not identity:
        raise HTTPException(400, "Assistant not configured.")
    owner_id = identity.owners[0].owner_id
    return LongTermMemory(owner_id, EmbeddingService())


@router.get("/")
async def list_memories(limit: int = 100, offset: int = 0, memory_type: str = None):
    """List long-term memories, newest first. Optionally filter by memory_type."""
    ltm       = _get_ltm()
    memories  = ltm.list_memories(limit=limit, offset=offset, memory_type=memory_type)
    return {"memories": memories, "total": len(memories)}


@router.patch("/{memory_id}")
async def update_memory(memory_id: str, body: UpdateMemoryBody):
    """Update a memory's content and re-embed it in ChromaDB."""
    if not body.content.strip():
        raise HTTPException(400, "Content cannot be empty.")
    ltm     = _get_ltm()
    updated = await ltm.update(memory_id, body.content.strip())
    if not updated:
        raise HTTPException(404, f"Memory '{memory_id}' not found.")
    return {"updated": True, "memory_id": memory_id}


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a memory from ChromaDB and SQLite."""
    ltm     = _get_ltm()
    deleted = ltm.delete(memory_id)
    if not deleted:
        raise HTTPException(404, f"Memory '{memory_id}' not found.")
    return {"deleted": True, "memory_id": memory_id}