from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
 
class ChatResponse(BaseModel):
    reply: str
    session_id: str
    emotional_state: dict
 
class SetupRequest(BaseModel):
    assistant_name: str
    owner_name: str
    owner_email: Optional[str] = None
    timezone: str = "UTC"
 
class IdentityResponse(BaseModel):
    assistant_name: str
    owner_name: str
    configured: bool
 
class MemoryItem(BaseModel):
    memory_id: str
    content: str
    memory_type: str
    importance: float
 
class EmotionalStateResponse(BaseModel):
    mood: float
    trust: float
    stress: float
    engagement: float