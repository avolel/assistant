# Keeps one engine per session_id in memory (single-user local app)
from typing import Dict, Optional
from ..conversation.engine import ConversationEngine
from ..core.identity import IdentityManager
from ..llm.factory import create_llm_provider
from ..config import settings
 
_sessions: Dict[str, ConversationEngine] = {}
 
 # Returns existing engine for session_id or creates a new one if not found.
async def get_or_create_engine(session_id: Optional[str]) -> ConversationEngine:
    if session_id and session_id in _sessions:
        return _sessions[session_id]
    mgr = IdentityManager()
    identity = mgr.load()
    if not identity:
        raise ValueError("Assistant not configured. Run setup first.")
    llm = create_llm_provider(settings.llm_provider, model=settings.llm_model)
    owner_id = identity.owners[0].owner_id
    timezone = identity.owners[0].timezone
    engine = ConversationEngine(llm, identity, owner_id, timezone)
    _sessions[engine.session_id] = engine
    return engine