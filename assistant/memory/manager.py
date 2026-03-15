from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict
from .short_term import ShortTermMemory
from .long_term import LongTermMemory
from .embeddings import EmbeddingService

# Define the MemoryType enum to categorize different types of memories
class MemoryType(Enum):
    CONVERSATION  = "conversation"
    USER_FACT     = "user_fact"
    PREFERENCE    = "preference"
    EVENT         = "event"
    SUMMARY       = "summary"

# Define the Memory dataclass to represent a memory entry in the system
@dataclass
class Memory:
    memory_id: str                     # UUID
    owner_id: str
    memory_type: MemoryType
    content: str                       # Raw text
    embedding: Optional[List[float]] = None
    importance: float = 0.5            # 0.0 – 1.0
    created_at: datetime = field(default_factory=datetime.now(timezone.utc))
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    metadata: dict = field(default_factory=dict)

# Define the ConversationTurn dataclass to represent a single turn in a conversation
@dataclass
class ConversationTurn:
    turn_id: str
    session_id: str
    role: str                          # "user" | "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now(timezone.utc))
    tool_calls: List[dict] = field(default_factory=list)
    emotional_snapshot: Optional[dict] = None

# MemoryManager class to handle both short-term and long-term memory operations
class MemoryManager:
    def __init__(self, owner_id: str, session_id: str) -> None:
        self.owner_id = owner_id
        self.session_id = session_id
        self.embed_svc = EmbeddingService()
        self.stm = ShortTermMemory(session_id)
        self.ltm = LongTermMemory(owner_id, self.embed_svc)

    # Add a conversation turn to short-term memory. 
    def add_turn(self, role: str, content: str) -> None:
        self.stm.add_turn(role, content)
 
    # Retrieve recent conversation turns from short-term memory (default last 20 turns).
    def get_recent_turns(self, n: int = 20) -> List[Dict]:
        return self.stm.get_recent(n)
    
    # Store a memory in long-term memory with the specified content, type, and importance (default 0.5).
    async def store_memory(self, content: str, memory_type: str,
                           importance: float = 0.5) -> str:
        return await self.ltm.store(content, memory_type, importance)
    
    # Query long-term memory for relevant memories based on a text query, 
    # returning the most relevant memories with their metadata and distance scores. 
    async def recall(self, query: str, n: int = 5) -> List[Dict]:
        return await self.ltm.query(query, n)
 
    # Simple heuristic: store user messages that mention personal info.
    async def extract_and_store_facts(self,
        user_message: str) -> None:
        keywords = ["i am", "i work", "i like", "i hate", "my name",
                    "i live", "i have", "i prefer", "i use"]
        msg_lower = user_message.lower()
        if any(kw in msg_lower for kw in keywords):
            await self.ltm.store(user_message, "user_fact", importance=0.7)