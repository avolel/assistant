import sqlite3, pathlib
from contextlib import contextmanager
from typing import Generator

DB_PATH = pathlib.Path.home() / ".assistant" / "assistant.db"

# This function provides a context manager for managing SQLite database connections. 
# It ensures that the connection is properly opened, committed, and closed, 
# while also handling exceptions and rolling
@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)

    # Set the row factory to sqlite3.Row to allow accessing columns by name
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL") # Enable Write-Ahead Logging for better concurrency
    conn.execute("PRAGMA foreign_keys=ON") # Enable foreign key constraints
    try:
        yield conn # Yield the connection to the caller
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()