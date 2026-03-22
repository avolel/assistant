# Chat route: single POST endpoint that accepts a message and returns the assistant's reply.
from fastapi import APIRouter, HTTPException
from ..models import ChatRequest, ChatResponse
from ..session_store import get_or_create_engine

# APIRouter groups related endpoints. It's mounted in app.py with prefix="/api/chat".
router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def send_message(req: ChatRequest):
    """Receive a user message, route it through the conversation engine, and return the reply.
    FastAPI automatically deserialises the JSON body into a ChatRequest object.
    The response_model=ChatResponse causes FastAPI to validate and serialise the return value."""
    try:
        # If req.session_id is None, get_or_create_engine starts a fresh session.
        # If it matches an existing in-memory engine, that engine is reused.
        engine = await get_or_create_engine(req.session_id)
        reply  = await engine.chat(req.message)
        return ChatResponse(
            reply           = reply,
            session_id      = engine.session_id,
            emotional_state = engine.emotion_state.to_dict()
        )
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(500, str(e))