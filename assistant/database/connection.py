# SQLite connection helper using a context manager for safe transaction handling.
# Every DB operation in this project uses `with get_db_connection() as db:` to ensure
# commits on success and rollbacks on failure with no boilerplate at call sites.
import sqlite3, pathlib
from contextlib import contextmanager
from typing import Generator

DB_PATH = pathlib.Path.home() / ".assistant" / "assistant.db"


# @contextmanager turns a generator function into a context manager usable with `with`.
# The code before `yield` runs on entry (__enter__), the code after runs on exit (__exit__).
# This is Python's equivalent of a C# `using` block or a Go `defer`.
@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    # Create parent directories if they don't exist (e.g. on first run).
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)

    # row_factory = sqlite3.Row allows column access by name: row["column_name"]
    # instead of by index: row[0]. Much safer when column order might change.
    conn.row_factory = sqlite3.Row

    # WAL (Write-Ahead Logging) mode improves concurrent read performance.
    # Reads don't block writes and vice versa — important when multiple requests hit the DB.
    conn.execute("PRAGMA journal_mode=WAL")
    # Enforce foreign key constraints (SQLite disables them by default for backward compatibility).
    conn.execute("PRAGMA foreign_keys=ON")

    try:
        yield conn          # Hand the connection to the `with` block body
        conn.commit()       # Auto-commit if the block exits normally
    except Exception:
        conn.rollback()     # Roll back all changes if anything raised inside the block
        raise               # Re-raise so the caller sees the original exception
    finally:
        conn.close()        # Always close, even if commit or rollback raised