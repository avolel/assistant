# Identity layer: defines what the assistant IS and who OWNS it.
# One assistant identity can have multiple owner profiles (multi-user).
import uuid, json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from ..database.connection import get_db_connection
from ..config.settings import settings

# @dataclass auto-generates __init__, __repr__, and __eq__ from the field annotations.
# It's like a C# record or Kotlin data class — avoids writing boilerplate constructors.
@dataclass
class OwnerProfile:
    owner_id: str                   # UUID stored as a string — SQLite has no native UUID type
    name: str
    email: Optional[str] = None
    owner_timezone: str = settings.owner_timezone
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    facts: List[str] = field(default_factory=list)        # Accumulated facts learned about this owner
    preferences: dict = field(default_factory=dict)       # Key/value preferences

# field(default_factory=...) is required for mutable defaults (list, dict).
# Writing `facts: List[str] = []` would share one list across all instances — a classic Python gotcha.
@dataclass
class AssistantIdentity:
    name: str
    persona_description: str                              # Full persona injected into every system prompt
    personality_traits: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    owners: List[OwnerProfile] = field(default_factory=list)


class IdentityManager:
    """Handles all DB reads/writes for assistant identity and owner profiles."""

    def setup(self, assistant_name: str, owner_name: str,
              owner_email: str = None, owner_timezone: str = "UTC") -> AssistantIdentity:
        """First-time setup: insert both an owner row and an assistant_identity row, then return the loaded identity."""
        owner_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()   # ISO 8601 string — SQLite stores datetimes as text
        traits = ["curious", "helpful", "consistent", "thoughtful"]
        persona = (f"You are {assistant_name}, a personal AI assistant. "
                   f"You are dedicated to helping {owner_name} with their work and life. "
                   f"You have a warm, professional tone and remember past conversations.")
        # `with get_db_connection() as db:` uses a context manager that auto-commits or rolls back.
        # See database/connection.py for the implementation.
        with get_db_connection() as db:
            db.execute(
                "INSERT INTO owners VALUES (?,?,?,?,?,?)",
                (owner_id, owner_name, owner_email, owner_timezone, "{}", now)
            )
            db.execute(
                "INSERT INTO assistant_identity VALUES (NULL,?,?,?,?)",
                (assistant_name, persona, json.dumps(traits), now)   # json.dumps converts list → JSON string for storage
            )
        return self.load()

    def load(self) -> Optional[AssistantIdentity]:
        """Load identity from DB. Returns None if setup has not been run yet."""
        with get_db_connection() as db:
            ai_row = db.execute("SELECT * FROM assistant_identity LIMIT 1").fetchone()
            if not ai_row:
                return None
            owner_rows = db.execute("SELECT * FROM owners").fetchall()
        # sqlite3.Row objects support column access by name (e.g. r["email"]) because
        # we set conn.row_factory = sqlite3.Row in the connection setup.
        owners = [OwnerProfile(owner_id=r["owner_id"], name=r["name"],
                               email=r["email"], owner_timezone=r["timezone"],
                               preferences=json.loads(r["preferences"])) for r in owner_rows]
        return AssistantIdentity(
            name=ai_row["name"],
            persona_description=ai_row["persona_description"],
            personality_traits=json.loads(ai_row["personality_traits"]),  # JSON string → Python list
            owners=owners
        )

    def update_name(self, new_name: str) -> AssistantIdentity:
        """Rename the assistant and regenerate its persona description to match."""
        identity = self.load()
        owner_name = identity.owners[0].name if identity.owners else "the owner"
        persona = (f"You are {new_name}, a personal AI assistant. "
                   f"You are dedicated to helping {owner_name} with their work and life. "
                   f"You have a warm, professional tone and remember past conversations.")
        with get_db_connection() as db:
            db.execute(
                "UPDATE assistant_identity SET name=?, persona_description=?",
                (new_name, persona)
            )
        return self.load()

    def remove_owner(self, owner_id: str) -> AssistantIdentity:
        """Remove an owner and cascade-delete all their sessions, turns, emotional states, and memories.
        Raises ValueError if this would remove the last owner."""
        with get_db_connection() as db:
            count = db.execute("SELECT COUNT(*) FROM owners").fetchone()[0]
            if count <= 1:
                raise ValueError("Cannot remove the last owner")
            # Collect all session IDs for this owner before deleting,
            # so we can clean up child rows (turns and emotional states).
            session_ids = [r[0] for r in db.execute(
                "SELECT session_id FROM sessions WHERE owner_id=?", (owner_id,)
            ).fetchall()]
            for sid in session_ids:
                db.execute("DELETE FROM emotional_states WHERE session_id=?", (sid,))
                db.execute("DELETE FROM conversation_turns WHERE session_id=?", (sid,))
            db.execute("DELETE FROM sessions WHERE owner_id=?", (owner_id,))
            db.execute("DELETE FROM memories WHERE owner_id=?", (owner_id,))
            db.execute("DELETE FROM owners WHERE owner_id=?", (owner_id,))
        return self.load()

    def add_owner(self, name: str, email: str = None, owner_timezone: str = "UTC") -> AssistantIdentity:
        """Insert a new owner profile and return the updated identity."""
        owner_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with get_db_connection() as db:
            db.execute(
                "INSERT INTO owners VALUES (?,?,?,?,?,?)",
                (owner_id, name, email, owner_timezone, "{}", now)
            )
        return self.load()

    def is_configured(self) -> bool:
        """Returns True if setup has been run (assistant_identity table has at least one row)."""
        with get_db_connection() as db:
            return db.execute("SELECT COUNT(*) FROM assistant_identity").fetchone()[0] > 0