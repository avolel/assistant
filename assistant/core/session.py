import uuid
from datetime import datetime, timezone
from typing import List, Optional
from dataclasses import dataclass
from ..database.connection import get_db_connection

@dataclass
class SessionSummary:
    session_id: str
    owner_id: str
    started_at: str
    ended_at: Optional[str]
    turn_count: int
    summary: Optional[str]

    @property
    def duration(self) -> str:
        """Human readable duration of the session."""
        if not self.ended_at:
            return "In progress"
        start = datetime.fromisoformat(self.started_at)
        end   = datetime.fromisoformat(self.ended_at)
        secs  = int((end - start).total_seconds())
        if secs < 60:
            return f"{secs}s"
        if secs < 3600:
            return f"{secs // 60}m {secs % 60}s"
        return f"{secs // 3600}h {(secs % 3600) // 60}m"


class SessionManager:

    # ── List ──────────────────────────────────────────────────────────────

    def list_sessions(self,
                      owner_id: str,
                      limit: int = 20) -> List[SessionSummary]:
        """Return the most recent sessions for an owner."""
        with get_db_connection() as db:
            rows = db.execute(
                """SELECT
                       s.session_id,
                       s.owner_id,
                       s.started_at,
                       s.ended_at,
                       s.summary,
                       COUNT(t.turn_id) as turn_count
                   FROM sessions s
                   LEFT JOIN conversation_turns t
                       ON t.session_id = s.session_id
                   WHERE s.owner_id = ?
                   GROUP BY s.session_id
                   ORDER BY s.started_at DESC
                   LIMIT ?""",
                (owner_id, limit)
            ).fetchall()

        return [
            SessionSummary(
                session_id=r["session_id"],
                owner_id=r["owner_id"],
                started_at=r["started_at"],
                ended_at=r["ended_at"],
                turn_count=r["turn_count"],
                summary=r["summary"],
            )
            for r in rows
        ]

    # ── Resume ────────────────────────────────────────────────────────────

    def get_session(self, session_id: str) -> Optional[SessionSummary]:
        """Fetch a single session by ID."""
        with get_db_connection() as db:
            row = db.execute(
                """SELECT
                       s.session_id,
                       s.owner_id,
                       s.started_at,
                       s.ended_at,
                       s.summary,
                       COUNT(t.turn_id) as turn_count
                   FROM sessions s
                   LEFT JOIN conversation_turns t
                       ON t.session_id = s.session_id
                   WHERE s.session_id = ?
                   GROUP BY s.session_id""",
                (session_id,)
            ).fetchone()

        if not row:
            return None

        return SessionSummary(
            session_id=row["session_id"],
            owner_id=row["owner_id"],
            started_at=row["started_at"],
            ended_at=row["ended_at"],
            turn_count=row["turn_count"],
            summary=row["summary"],
        )

    def get_turns(self, session_id: str) -> List[dict]:
        """Fetch all turns for a session ordered oldest to newest."""
        with get_db_connection() as db:
            rows = db.execute(
                """SELECT role, content, timestamp
                   FROM conversation_turns
                   WHERE session_id = ?
                   ORDER BY timestamp ASC""",
                (session_id,)
            ).fetchall()
        return [{"role": r["role"], "content": r["content"],
                 "timestamp": r["timestamp"]} for r in rows]

    def resume(self, session_id: str,
               owner_id: str) -> Optional[str]:
        """
        Prepare a session for resumption.
        Reopens a closed session by clearing ended_at.
        Returns the session_id if found, None if not.
        """
        session = self.get_session(session_id)
        if not session:
            return None
        if session.owner_id != owner_id:
            return None

        # Reopen the session
        with get_db_connection() as db:
            db.execute(
                "UPDATE sessions SET ended_at = NULL WHERE session_id = ?",
                (session_id,)
            )

        return session_id

    def get_latest_session_id(self, owner_id: str) -> Optional[str]:
        """Return the most recent session ID for an owner."""
        with get_db_connection() as db:
            row = db.execute(
                """SELECT session_id FROM sessions
                   WHERE owner_id = ?
                   ORDER BY started_at DESC
                   LIMIT 1""",
                (owner_id,)
            ).fetchone()
        return row["session_id"] if row else None

    # ── Delete ────────────────────────────────────────────────────────────

    def delete_session(self, session_id: str,
                       owner_id: str) -> bool:
        """
        Delete a session and all its turns.
        Returns True if deleted, False if not found or wrong owner.
        """
        session = self.get_session(session_id)
        if not session or session.owner_id != owner_id:
            return False

        with get_db_connection() as db:
            db.execute(
                "DELETE FROM conversation_turns WHERE session_id = ?",
                (session_id,)
            )
            db.execute(
                "DELETE FROM emotional_states WHERE session_id = ?",
                (session_id,)
            )
            db.execute(
                "DELETE FROM sessions WHERE session_id = ?",
                (session_id,)
            )

        return True

    def delete_all_sessions(self, owner_id: str) -> int:
        """
        Delete all sessions for an owner.
        Returns the number of sessions deleted.
        """
        sessions = self.list_sessions(owner_id, limit=9999)
        count = 0
        for s in sessions:
            if self.delete_session(s.session_id, owner_id):
                count += 1
        return count