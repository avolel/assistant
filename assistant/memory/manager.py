from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

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