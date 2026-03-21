import json
import pathlib
from datetime import datetime
from typing import List, Dict
from ..database.connection import get_db_connection

EXPORTS_DIR = pathlib.Path.home() / "assistant_exports"

# ConversationHistory manages the storage, trimming, and exporting of conversation turns for a session.
class ConversationHistory:
    def __init__(self, session_id: str, max_turns: int = 20) -> None:
        self.session_id = session_id
        self.max_turns = max_turns

    # ── Trim ──────────────────────────────────────────────────────────────
    # This method deletes the oldest turns when the total number of turns exceeds max_turns.
    def trim(self) -> int:
        """
        Delete oldest turns when history exceeds max_turns.
        Always keeps the most recent max_turns turns.
        Returns the number of turns deleted.
        """
        with get_db_connection() as db:
            total = db.execute(
                "SELECT COUNT(*) FROM conversation_turns WHERE session_id = ?",
                (self.session_id,)
            ).fetchone()[0]

            excess = total - self.max_turns
            if excess <= 0:
                return 0

            # Get the IDs of the oldest excess turns
            oldest = db.execute(
                """SELECT turn_id FROM conversation_turns
                   WHERE session_id = ?
                   ORDER BY timestamp ASC
                   LIMIT ?""",
                (self.session_id, excess)
            ).fetchall()

            ids = [row["turn_id"] for row in oldest]
            placeholders = ",".join("?" * len(ids))
            db.execute(
                f"DELETE FROM conversation_turns WHERE turn_id IN ({placeholders})",
                ids
            )

        return excess

    def trim_if_needed(self) -> None:
        """Call this after every turn to keep history within limits."""
        removed = self.trim()
        if removed > 0:
            print(f"  [history] Trimmed {removed} old turn(s) from session.")

    # ── Export ────────────────────────────────────────────────────────────

    def get_all_turns(self) -> List[Dict]:
        """Fetch all turns for this session ordered oldest to newest."""
        with get_db_connection() as db:
            rows = db.execute(
                """SELECT role, content, timestamp
                   FROM conversation_turns
                   WHERE session_id = ?
                   ORDER BY timestamp ASC""",
                (self.session_id,)
            ).fetchall()
        return [{"role": r["role"], "content": r["content"],
                 "timestamp": r["timestamp"]} for r in rows]

    def export_as_text(self, filepath: pathlib.Path) -> None:
        """Export conversation as a readable plain text file."""
        turns = self.get_all_turns()
        lines = [
            f"Conversation Export",
            f"Session : {self.session_id}",
            f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Turns   : {len(turns)}",
            "=" * 60,
            ""
        ]
        for turn in turns:
            timestamp = turn["timestamp"][:19].replace("T", " ")
            role = "You" if turn["role"] == "user" else "Assistant"
            lines.append(f"[{timestamp}] {role}:")
            lines.append(turn["content"])
            lines.append("")

        filepath.write_text("\n".join(lines), encoding="utf-8")

    def export_as_json(self, filepath: pathlib.Path) -> None:
        """Export conversation as a JSON file."""
        turns = self.get_all_turns()
        data = {
            "session_id": self.session_id,
            "exported_at": datetime.now().isoformat(),
            "turn_count": len(turns),
            "turns": turns
        }
        filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def export_as_markdown(self, filepath: pathlib.Path) -> None:
        """Export conversation as a Markdown file."""
        turns = self.get_all_turns()
        lines = [
            f"# Conversation Export",
            f"",
            f"- **Session:** `{self.session_id}`",
            f"- **Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **Turns:** {len(turns)}",
            f"",
            "---",
            ""
        ]
        for turn in turns:
            timestamp = turn["timestamp"][:19].replace("T", " ")
            if turn["role"] == "user":
                lines.append(f"**You** — *{timestamp}*")
            else:
                lines.append(f"**Assistant** — *{timestamp}*")
            lines.append("")
            lines.append(turn["content"])
            lines.append("")
            lines.append("---")
            lines.append("")

        filepath.write_text("\n".join(lines), encoding="utf-8")

    def export(self, fmt: str = "text", filename: str = None) -> pathlib.Path:
        """
        Export the conversation to ~/assistant_exports/.
        fmt: "text" | "json" | "markdown"
        Returns the path of the exported file.
        """
        EXPORTS_DIR.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extensions = {"text": "txt", "json": "json", "markdown": "md"}
        ext = extensions.get(fmt, "txt")

        name = filename or f"conversation_{timestamp}.{ext}"
        filepath = EXPORTS_DIR / name

        if fmt == "json":
            self.export_as_json(filepath)
        elif fmt == "markdown":
            self.export_as_markdown(filepath)
        else:
            self.export_as_text(filepath)

        return filepath