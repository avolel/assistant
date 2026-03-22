# Sessions routes: list, retrieve, and delete conversation sessions.
from fastapi import APIRouter, HTTPException
from ...core.session import SessionManager
from ...core.identity import IdentityManager

router = APIRouter()


def _get_owner_id() -> str:
    """Load the identity and return the first owner's ID.
    Raises 400 if the assistant hasn't been configured yet."""
    mgr      = IdentityManager()
    identity = mgr.load()
    if not identity:
        raise HTTPException(400, "Assistant not configured.")
    return identity.owners[0].owner_id


@router.get("/")
async def list_sessions(limit: int = 20):
    """Return up to `limit` most recent sessions for the current owner.
    `limit` is a query parameter: GET /api/sessions/?limit=50"""
    owner_id = _get_owner_id()
    sm       = SessionManager()
    sessions = sm.list_sessions(owner_id, limit=limit)
    # Return a plain dict — FastAPI serialises it to JSON automatically.
    return {
        "sessions": [
            {
                "session_id": s.session_id,
                "started_at": s.started_at,
                "ended_at":   s.ended_at,
                "duration":   s.duration,    # Computed @property on SessionSummary
                "turn_count": s.turn_count,
                "summary":    s.summary,
            }
            for s in sessions
        ],
        "total": len(sessions)
    }


@router.get("/{session_id}")
async def get_session(session_id: str):
    """Return a session's metadata plus all its turns with emotional state snapshots.
    Returns 404 if the session doesn't exist or belongs to a different owner."""
    owner_id = _get_owner_id()
    sm       = SessionManager()
    session  = sm.get_session(session_id)
    if not session or session.owner_id != owner_id:
        raise HTTPException(404, f"Session '{session_id}' not found.")
    turns = sm.get_turns(session_id)
    return {
        "session_id": session.session_id,
        "started_at": session.started_at,
        "ended_at":   session.ended_at,
        "duration":   session.duration,
        "turn_count": session.turn_count,
        "summary":    session.summary,
        "turns":      turns,
    }


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and all its turns. Returns 404 if not found or wrong owner."""
    owner_id = _get_owner_id()
    sm       = SessionManager()
    deleted  = sm.delete_session(session_id, owner_id)
    if not deleted:
        raise HTTPException(404, f"Session '{session_id}' not found.")
    return {"deleted": True, "session_id": session_id}