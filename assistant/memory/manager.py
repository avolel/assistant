# MemoryManager is a facade that unifies short-term memory (SQLite conversation turns)
# and long-term memory (ChromaDB vector store) behind a single interface.
# The ConversationEngine only talks to this class, not to STM/LTM directly.
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict
from .short_term import ShortTermMemory
from .long_term import LongTermMemory
from .embeddings import EmbeddingService


# Enum defines a fixed set of named constants. Access as MemoryType.USER_FACT, etc.
# Stored as the .value string in the DB ("user_fact"), not the enum name ("USER_FACT").
class MemoryType(Enum):
    CONVERSATION = "conversation"
    USER_FACT    = "user_fact"
    PREFERENCE   = "preference"
    EVENT        = "event"
    SUMMARY      = "summary"


@dataclass
class Memory:
    """Represents a single long-term memory entry (not stored in DB as-is, used for in-memory modelling)."""
    memory_id:     str
    owner_id:      str
    memory_type:   MemoryType
    content:       str                         # The raw text of the memory
    embedding:     Optional[List[float]] = None  # Vector representation (set after embedding)
    importance:    float = 0.5                 # 0.0–1.0; higher = more likely to be recalled
    created_at:    datetime = field(default_factory=datetime.now(timezone.utc))
    last_accessed: Optional[datetime] = None
    access_count:  int = 0
    metadata:      dict = field(default_factory=dict)


@dataclass
class ConversationTurn:
    """Represents one exchange (user or assistant) within a session."""
    turn_id:            str
    session_id:         str
    role:               str                    # "user" | "assistant"
    content:            str
    timestamp:          datetime = field(default_factory=datetime.now(timezone.utc))
    tool_calls:         List[dict] = field(default_factory=list)
    emotional_snapshot: Optional[dict] = None  # Emotional state at the time of this turn


class MemoryManager:
    """Coordinates short-term and long-term memory for a single session."""

    def __init__(self, owner_id: str, session_id: str) -> None:
        self.owner_id   = owner_id
        self.session_id = session_id
        self.embed_svc  = EmbeddingService()
        # STM is scoped to this session; LTM spans all sessions for this owner.
        self.stm        = ShortTermMemory(session_id)
        self.ltm        = LongTermMemory(owner_id, self.embed_svc)

    def add_turn(self, role: str, content: str) -> None:
        """Append one conversation turn (user or assistant) to short-term memory."""
        self.stm.add_turn(role, content)

    def get_recent_turns(self, n: int = 20) -> List[Dict]:
        """Return the last n turns for building the LLM message list."""
        return self.stm.get_recent(n)

    async def store_memory(self, content: str, memory_type: str,
                           importance: float = 0.5) -> str:
        """Embed content and store it in long-term memory. Returns the new memory_id."""
        return await self.ltm.store(content, memory_type, importance)

    async def recall(self, query: str, n: int = 5) -> List[Dict]:
        """Semantic search: embed the query and retrieve the n most similar memories from ChromaDB."""
        return await self.ltm.query(query, n)

    async def extract_and_store_facts(self, user_message: str) -> None:
        """Heuristic fact extraction: if the user's message contains personal information keywords,
        store the whole message as a user_fact memory. Simple but effective for first-person statements."""
        keywords  = ["i am", "i work", "i like", "i hate", "my name",
                     "i live", "i have", "i prefer", "i use"]
        msg_lower = user_message.lower()
        # any() returns True if at least one element in the iterable is truthy —
        # equivalent to multiple `or` conditions but more concise.
        if any(kw in msg_lower for kw in keywords):
            await self.ltm.store(user_message, "user_fact", importance=0.7)