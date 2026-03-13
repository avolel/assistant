from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

# OwnerProfile represents the identity and profile of the owner of the assistant. 
@dataclass
class OwnerProfile:
    owner_id: str #UUID
    name: str
    email: Optional[str] = None
    timezone: str = "UTC"
    created_at: datetime = field(default_factory=datetime.now(datetime.timezone.utc))
    facts: List[str] = field(default_factory=list)  #Learned facts
    preferences: dict = field(default_factory=dict)

# AssistantIdentity represents the identity and persona of the assistant.
@dataclass
class AssistantIdentity:
    name: str
    persona_description: str
    personality_traits: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now(datetime.timezone.utc))
    owners: List[OwnerProfile] = field(default_factory=list)