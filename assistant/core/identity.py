import uuid, json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from ..database.connection import get_db_connection
from ..config.settings import settings

# OwnerProfile represents the identity and profile of the owner of the assistant. 
@dataclass
class OwnerProfile:
    owner_id: str #UUID
    name: str
    email: Optional[str] = None
    owner_timezone: str = settings.owner_timezone
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    facts: List[str] = field(default_factory=list)  #Learned facts
    preferences: dict = field(default_factory=dict)

# AssistantIdentity represents the identity and persona of the assistant.
@dataclass
class AssistantIdentity:
    name: str
    persona_description: str
    personality_traits: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    owners: List[OwnerProfile] = field(default_factory=list)

# IdentityManager handles the creation and management of the assistant's identity and owner profiles.
class IdentityManager:
    #Run on first launch to create identity and owner.
    def setup(self, assistant_name: str, owner_name: str,
        owner_email: str = None, owner_timezone: str = "UTC") -> AssistantIdentity:
        owner_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        traits = ["curious", "helpful", "consistent", "thoughtful"]
        persona = (f"You are {assistant_name}, a personal AI assistant. "
                   f"You are dedicated to helping {owner_name} with their work and life. "
                   f"You have a warm, professional tone and remember past conversations.")
        with get_db_connection() as db:
            db.execute(
                "INSERT INTO owners VALUES (?,?,?,?,?,?)",
                (owner_id, owner_name, owner_email, owner_timezone, "{}", now)
            )
            db.execute(
                "INSERT INTO assistant_identity VALUES (NULL,?,?,?,?)",
                (assistant_name, persona, json.dumps(traits), now)
            )
        return self.load()
    
    # Load identity from DB. Returns None if not set up yet.
    def load(self) -> Optional[AssistantIdentity]:
        with get_db_connection() as db:
            ai_row = db.execute("SELECT * FROM assistant_identity LIMIT 1").fetchone()
            if not ai_row:
                return None
            owner_rows = db.execute("SELECT * FROM owners").fetchall()
        owners = [OwnerProfile(owner_id=r["owner_id"], name=r["name"],
                               email=r["email"], owner_timezone=r["timezone"],
                               preferences=json.loads(r["preferences"])) for r in owner_rows]
        return AssistantIdentity(
            name=ai_row["name"],
            persona_description=ai_row["persona_description"],
            personality_traits=json.loads(ai_row["personality_traits"]),
            owners=owners
        )
    
    # Update the assistant's name and persona description.
    def update_name(self, new_name: str) -> AssistantIdentity:
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

    # Remove an owner by ID. Raises ValueError if it's the last owner.
    # Also removes the owner's sessions (+ turns + emotional states) and memories.
    def remove_owner(self, owner_id: str) -> AssistantIdentity:
        with get_db_connection() as db:
            count = db.execute("SELECT COUNT(*) FROM owners").fetchone()[0]
            if count <= 1:
                raise ValueError("Cannot remove the last owner")
            # Collect session IDs for this owner so we can delete dependents
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

    # Add a new owner profile.
    def add_owner(self, name: str, email: str = None, owner_timezone: str = "UTC") -> AssistantIdentity:
        owner_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with get_db_connection() as db:
            db.execute(
                "INSERT INTO owners VALUES (?,?,?,?,?,?)",
                (owner_id, name, email, owner_timezone, "{}", now)
            )
        return self.load()

    # Check if identity is configured by seeing if there's an entry in the assistant_identity table.
    def is_configured(self) -> bool:
        with get_db_connection() as db:
            return db.execute("SELECT COUNT(*) FROM assistant_identity").fetchone()[0] > 0