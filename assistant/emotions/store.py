from datetime import datetime, timezone
from typing import Optional
from .state import EmotionalState
from ..database.connection import get_db_connection

# This store manages the persistence of emotional states for users across sessions.
class EmotionalStateStore:

    def save(self, owner_id: str, session_id: str,
             state: EmotionalState) -> None:
        """Persist the current emotional state for an owner."""
        now = datetime.now(timezone.utc).isoformat()
        with get_db_connection() as db:
            db.execute(
                """INSERT INTO emotional_states
                       (session_id, mood, trust, stress, engagement, recorded_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (session_id, state.mood, state.trust,
                 state.stress, state.engagement, now)
            )

    def load_latest(self, owner_id: str) -> Optional[EmotionalState]:
        """
        Load the most recent emotional state for an owner across all sessions.
        Returns None if no state has ever been saved.
        """
        with get_db_connection() as db:
            row = db.execute(
                """SELECT e.mood, e.trust, e.stress, e.engagement
                   FROM emotional_states e
                   JOIN sessions s ON s.session_id = e.session_id
                   WHERE s.owner_id = ?
                   ORDER BY e.recorded_at DESC
                   LIMIT 1""",
                (owner_id,)
            ).fetchone()

        if not row:
            return None

        return EmotionalState(
            mood=       row["mood"],
            trust=      row["trust"],
            stress=     row["stress"],
            engagement= row["engagement"],
        )