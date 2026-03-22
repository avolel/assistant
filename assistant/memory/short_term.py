# Short-term memory stores conversation turns for the current session in SQLite.
# It's "short-term" because it's bounded (max_turns) and session-scoped.
# For cross-session recall, see long_term.py.
import uuid
from datetime import datetime, timezone
from typing import List, Dict
from ..database.connection import get_db_connection
from ..config.settings import settings


class ShortTermMemory:
    def __init__(self, session_id: str, max_turns: int = settings.stm_max_turns) -> None:
        self.session_id = session_id
        self.max_turns  = max_turns

    def add_turn(self, role: str, content: str) -> None:
        """Insert a conversation turn into the DB. tool_calls and emotional_snapshot stored as JSON strings."""
        with get_db_connection() as db:
            db.execute(
                "INSERT INTO conversation_turns VALUES (?,?,?,?,?,?,?)",
                (
                    str(uuid.uuid4()),          # turn_id — unique primary key
                    self.session_id,
                    role,
                    content,
                    "[]",                       # tool_calls — empty JSON array placeholder
                    "{}",                       # emotional_snapshot — empty JSON object placeholder
                    datetime.now(timezone.utc).isoformat()
                )
            )

    def get_recent(self, n: int = None) -> List[Dict]:
        """Return the last n turns ordered oldest-to-newest (so the LLM sees the conversation in order).
        Returns plain dicts with 'role' and 'content' — matches the LLMMessage format."""
        limit = n or self.max_turns
        with get_db_connection() as db:
            rows = db.execute(
                "SELECT role, content FROM conversation_turns "
                "WHERE session_id=? ORDER BY timestamp ASC LIMIT ?",
                (self.session_id, limit)
            ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in rows]