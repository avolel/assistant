from fastapi import APIRouter, HTTPException
from ..models import ChatRequest, ChatResponse
from ..session_store import get_or_create_engine

router = APIRouter() # This router will be included in the main app with prefix "/api/chat"

@router.post("/", response_model=ChatResponse)
async def send_message(req: ChatRequest):
    try:
        engine = await get_or_create_engine(req.session_id)
        # This will call the chat method of the engine, which should return a reply string.
        reply = await engine.chat(req.message) 
        return ChatResponse(
            reply=reply,
            session_id=engine.session_id,
            emotional_state=engine.emotion_state.to_dict()
        )
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(500, str(e))