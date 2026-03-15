import uuid
from datetime import datetime
from typing import List, Dict
from ..database.connection import get_db_connection
from config.settings import settings

class ShortTermMemory:
    def __init__(self, session_id: str, max_turns: int = settings.stm_max_turns) -> None:
        self.session_id = session_id
        self.max_turns = max_turns

    # Inserting the most recent conversation turn for the session
    def add_turn(self, role: str, content: str) -> None:
        with get_db_connection() as db:
            db.execute(
                "INSERT INTO conversation_turns VALUES (?,?,?,?,?,?,?)",
                (str(uuid.uuid4()), self.session_id, role, content, "[]", "{}", datetime.now(datetime.timezone.utc).isoformat())
            )

    # Retrieving the most recent conversation turns for the session, up to the specified limit (20 by default)
    def get_recent(self, n: int = None) -> List[Dict]:
        limit = n or self.max_turns
        with get_db_connection() as db:
            rows = db.execute(
                "SELECT role, content FROM conversation_turns "
                "WHERE session_id=? ORDER BY timestamp ASC LIMIT ?",
                (self.session_id, limit)
            ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in rows]