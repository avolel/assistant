import os
from .connection import get_db_connection

base_dir = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(base_dir, 'schema.sql')

with open(schema_path, 'r') as f:
    SCHEMA = f.read()

# Run this function to create the database schema if it doesn't exist.
def run_migrations() -> None:
    with get_db_connection() as conn:
        conn.executescript(SCHEMA)
    print("✓ Database schema ready.")