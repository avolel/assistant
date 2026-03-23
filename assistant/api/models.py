# Pydantic models define the shape of every API request and response body.
# FastAPI uses these for automatic JSON parsing, validation, and OpenAPI documentation.
# Optional[str] = None means the field can be omitted from the JSON payload entirely.
from pydantic import BaseModel
from typing import List, Optional


class ChatRequest(BaseModel):
    message:    str
    session_id: Optional[str] = None   # Omit to start a new session; include to continue an existing one


class ChatResponse(BaseModel):
    reply:          str
    session_id:     str            # Always returned so the frontend can resume the same session
    emotional_state: dict          # { mood, trust, stress, engagement } floats


class SetupRequest(BaseModel):
    assistant_name: str
    owner_name:     str
    owner_email:    Optional[str] = None
    timezone:       str = "UTC"


class UpdateNameRequest(BaseModel):
    assistant_name: str


class UpdateOwnerRequest(BaseModel):
    name:  Optional[str] = None
    email: Optional[str] = None


class OwnerInfo(BaseModel):
    owner_id: str
    name:     str
    email:    Optional[str] = None


class IdentityResponse(BaseModel):
    assistant_name: str
    owner_name:     str
    owners:         List[OwnerInfo] = []
    configured:     bool            # False when setup has not been run yet


class MemoryItem(BaseModel):
    memory_id:   str
    content:     str
    memory_type: str
    importance:  float


class EmotionalStateResponse(BaseModel):
    mood:       float
    trust:      float
    stress:     float
    engagement: float