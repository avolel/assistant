# In-memory session store: maps session_id strings to live ConversationEngine instances.
# This is appropriate for a single-user local app. A multi-user deployment would need
# a shared store (Redis, DB) and a way to handle engine serialisation.
from typing import Dict, Optional
from ..conversation.engine import ConversationEngine
from ..core.identity import IdentityManager
from ..llm.factory import create_llm_provider
from ..config import settings

# Module-level dict — persists for the lifetime of the process.
# Each tab/client that starts a new session gets its own ConversationEngine instance.
_sessions: Dict[str, ConversationEngine] = {}


async def get_or_create_engine(session_id: Optional[str]) -> ConversationEngine:
    """Return the existing engine for `session_id`, or create a new one if not found.
    A missing session_id (None) always creates a new engine and therefore a new session."""
    if session_id and session_id in _sessions:
        return _sessions[session_id]

    # Identity must already exist (setup has been run) before an engine can be created.
    mgr      = IdentityManager()
    identity = mgr.load()
    if not identity:
        raise ValueError("Assistant not configured. Run setup first.")

    llm      = create_llm_provider(settings.llm_provider, model=settings.llm_model)
    owner_id = identity.owners[0].owner_id
    timezone = identity.owners[0].owner_timezone   # Used for time-awareness in the engine

    engine = ConversationEngine(llm, identity, owner_id)
    # The engine generates its own session_id in __init__, so we store it under that key.
    _sessions[engine.session_id] = engine
    return engine