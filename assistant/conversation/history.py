# ConversationHistory manages trimming (keeping sessions within the turn limit)
# and exporting sessions to file in various formats.
import json
import pathlib
from datetime import datetime
from typing import List, Dict
from ..database.connection import get_db_connection

# pathlib.Path is the modern way to work with filesystem paths in Python.
# Path.home() returns the user's home directory (~). / operator joins path segments.
EXPORTS_DIR = pathlib.Path.home() / "assistant_exports"


class ConversationHistory:
    def __init__(self, session_id: str, max_turns: int = 20) -> None:
        self.session_id = session_id
        self.max_turns  = max_turns

    def trim(self) -> int:
        """Delete the oldest turns when total exceeds max_turns.
        Always keeps the most recent max_turns turns. Returns the count deleted."""
        with get_db_connection() as db:
            total = db.execute(
                "SELECT COUNT(*) FROM conversation_turns WHERE session_id = ?",
                (self.session_id,)
            ).fetchone()[0]   # fetchone() returns a Row; [0] gets the first column (the count)

            excess = total - self.max_turns
            if excess <= 0:
                return 0

            # Fetch IDs of the oldest `excess` turns to delete them by primary key.
            oldest = db.execute(
                """SELECT turn_id FROM conversation_turns
                   WHERE session_id = ?
                   ORDER BY timestamp ASC
                   LIMIT ?""",
                (self.session_id, excess)
            ).fetchall()

            ids          = [row["turn_id"] for row in oldest]
            # Build a parameterised IN clause with the right number of ? placeholders.
            # Never interpolate values directly into SQL — always use ? placeholders to prevent injection.
            placeholders = ",".join("?" * len(ids))
            db.execute(
                f"DELETE FROM conversation_turns WHERE turn_id IN ({placeholders})",
                ids
            )

        return excess

    def trim_if_needed(self) -> None:
        """Convenience wrapper: trim after each turn and log if anything was removed."""
        removed = self.trim()
        if removed > 0:
            print(f"  [history] Trimmed {removed} old turn(s) from session.")

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
        # Convert sqlite3.Row objects to plain dicts for easier use outside this module.
        return [{"role": r["role"], "content": r["content"],
                 "timestamp": r["timestamp"]} for r in rows]

    def export_as_text(self, filepath: pathlib.Path) -> None:
        """Write conversation as a readable plain text file."""
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
            timestamp = turn["timestamp"][:19].replace("T", " ")   # Trim microseconds, replace ISO T separator
            role      = "You" if turn["role"] == "user" else "Assistant"
            lines.append(f"[{timestamp}] {role}:")
            lines.append(turn["content"])
            lines.append("")
        # Path.write_text() creates or overwrites the file. Always specify encoding explicitly.
        filepath.write_text("\n".join(lines), encoding="utf-8")

    def export_as_json(self, filepath: pathlib.Path) -> None:
        """Write conversation as a structured JSON file."""
        turns = self.get_all_turns()
        data  = {
            "session_id":  self.session_id,
            "exported_at": datetime.now().isoformat(),
            "turn_count":  len(turns),
            "turns":       turns
        }
        # json.dumps converts a Python dict/list to a JSON string. indent=2 pretty-prints it.
        filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def export_as_markdown(self, filepath: pathlib.Path) -> None:
        """Write conversation as a Markdown file."""
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
        """Export the conversation to ~/assistant_exports/.
        fmt: "text" | "json" | "markdown". Returns the path of the exported file."""
        # mkdir(exist_ok=True) is like `mkdir -p` — creates the dir if it doesn't exist, no error if it does.
        EXPORTS_DIR.mkdir(exist_ok=True)

        timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
        extensions = {"text": "txt", "json": "json", "markdown": "md"}
        ext        = extensions.get(fmt, "txt")   # dict.get(key, default) avoids KeyError

        name     = filename or f"conversation_{timestamp}.{ext}"
        filepath = EXPORTS_DIR / name

        if fmt == "json":
            self.export_as_json(filepath)
        elif fmt == "markdown":
            self.export_as_markdown(filepath)
        else:
            self.export_as_text(filepath)

        return filepath