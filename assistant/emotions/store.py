# EmotionalStateStore handles reading and writing emotional state snapshots to SQLite.
# Each assistant reply produces one row in emotional_states, linked to the session.
# On engine startup, the most recent row for this owner is loaded to restore continuity.
from datetime import datetime, timezone
from typing import Optional
from .state import EmotionalState
from ..database.connection import get_db_connection


class EmotionalStateStore:

    def save(self, owner_id: str, session_id: str, state: EmotionalState) -> None:
        """Persist the current emotional state snapshot after each assistant turn."""
        now = datetime.now(timezone.utc).isoformat()
        with get_db_connection() as db:
            db.execute(
                """INSERT INTO emotional_states
                       (owner_id, session_id, mood, trust, stress, engagement, recorded_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (owner_id, session_id, state.mood, state.trust,
                 state.stress, state.engagement, now)
            )

    def load_latest(self, owner_id: str) -> Optional[EmotionalState]:
        """Retrieve the most recent emotional state for an owner, surviving session deletion."""
        with get_db_connection() as db:
            row = db.execute(
                """SELECT mood, trust, stress, engagement
                   FROM emotional_states
                   WHERE owner_id = ?
                   ORDER BY recorded_at DESC
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