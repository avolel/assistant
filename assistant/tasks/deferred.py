# DeferredTaskManager: enqueues off-clock user messages and retrieves them for replay.
import uuid
from datetime import datetime, timezone
from ..database.connection import get_db_connection


class DeferredTaskManager:

    def enqueue(self, owner_id: str, session_id: str, message: str) -> str:
        """Insert a pending task. Returns the new task_id."""
        task_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with get_db_connection() as db:
            db.execute(
                "INSERT INTO deferred_tasks VALUES (?,?,?,?,?,?,?)",
                (task_id, owner_id, session_id, message, "pending", now, None)
            )
        return task_id

    def get_pending(self, owner_id: str) -> list[dict]:
        """Return all pending tasks for an owner, oldest first."""
        with get_db_connection() as db:
            rows = db.execute(
                "SELECT task_id, session_id, message, created_at "
                "FROM deferred_tasks WHERE owner_id=? AND status='pending' "
                "ORDER BY created_at ASC",
                (owner_id,)
            ).fetchall()
        return [{"task_id": r[0], "session_id": r[1],
                 "message": r[2], "created_at": r[3]} for r in rows]

    def mark_done(self, task_id: str) -> None:
        with get_db_connection() as db:
            db.execute(
                "UPDATE deferred_tasks SET status='done', executed_at=? WHERE task_id=?",
                (datetime.now(timezone.utc).isoformat(), task_id)
            )

    def mark_failed(self, task_id: str) -> None:
        with get_db_connection() as db:
            db.execute(
                "UPDATE deferred_tasks SET status='failed', executed_at=? WHERE task_id=?",
                (datetime.now(timezone.utc).isoformat(), task_id)
            )
