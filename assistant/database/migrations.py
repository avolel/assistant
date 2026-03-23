# Database migration runner.
# Reads schema.sql from the same directory and executes it against the SQLite database.
# schema.sql uses CREATE TABLE IF NOT EXISTS, so running this multiple times is safe —
# it won't overwrite existing data or raise errors on subsequent startups.
import os
from .connection import get_db_connection

# __file__ is the absolute path of this module file.
# os.path.dirname(__file__) is the directory containing it (database/).
# This ensures schema.sql is found regardless of the working directory.
base_dir    = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(base_dir, 'schema.sql')

with open(schema_path, 'r') as f:
    SCHEMA = f.read()   # Read once at import time and cache as a module constant


def run_migrations() -> None:
    """Execute the schema SQL against the database.
    executescript() runs multiple SQL statements separated by semicolons in one call."""
    with get_db_connection() as conn:
        conn.executescript(SCHEMA)
        _add_owner_id_to_emotional_states(conn)
    print("✓ Database schema ready.")


def _add_owner_id_to_emotional_states(conn) -> None:
    """One-time migration: add owner_id column to emotional_states and backfill from sessions.
    Safe to run multiple times — the ALTER TABLE is skipped if the column already exists."""
    cols = [row[1] for row in conn.execute("PRAGMA table_info(emotional_states)").fetchall()]
    if "owner_id" in cols:
        return
    conn.execute("ALTER TABLE emotional_states ADD COLUMN owner_id TEXT")
    conn.execute(
        """UPDATE emotional_states
           SET owner_id = (
               SELECT owner_id FROM sessions WHERE sessions.session_id = emotional_states.session_id
           )
           WHERE owner_id IS NULL"""
    )
    conn.commit()