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
    print("✓ Database schema ready.")