CREATE TABLE IF NOT EXISTS owners (
    owner_id    TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT,
    timezone    TEXT DEFAULT "UTC",
    preferences TEXT DEFAULT "{}",   -- JSON blob
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assistant_identity (
    id                   INTEGER PRIMARY KEY,
    name                 TEXT NOT NULL,
    persona_description  TEXT,
    personality_traits   TEXT DEFAULT "[]",  -- JSON array
    created_at           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id   TEXT PRIMARY KEY,
    owner_id     TEXT NOT NULL REFERENCES owners(owner_id),
    started_at   TEXT NOT NULL,
    ended_at     TEXT,
    summary      TEXT
);

CREATE TABLE IF NOT EXISTS conversation_turns (
    turn_id             TEXT PRIMARY KEY,
    session_id          TEXT NOT NULL REFERENCES sessions(session_id),
    role                TEXT NOT NULL,   -- "user" | "assistant"
    content             TEXT NOT NULL,
    tool_calls          TEXT DEFAULT "[]",
    emotional_snapshot  TEXT DEFAULT "{}",
    timestamp           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memories (
    memory_id      TEXT PRIMARY KEY,
    owner_id       TEXT NOT NULL REFERENCES owners(owner_id),
    memory_type    TEXT NOT NULL,
    content        TEXT NOT NULL,
    importance     REAL DEFAULT 0.5,
    chroma_id      TEXT,   -- Cross-reference to ChromaDB document
    access_count   INTEGER DEFAULT 0,
    last_accessed  TEXT,
    created_at     TEXT NOT NULL,
    metadata       TEXT DEFAULT "{}"
);

CREATE TABLE IF NOT EXISTS emotional_states (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id    TEXT NOT NULL REFERENCES owners(owner_id),
    session_id  TEXT,   -- nullable: retained even after session deletion
    mood        REAL NOT NULL,
    trust       REAL NOT NULL,
    stress      REAL NOT NULL,
    engagement  REAL NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_turns_session   ON conversation_turns(session_id);
CREATE INDEX IF NOT EXISTS idx_memories_owner  ON memories(owner_id);
CREATE INDEX IF NOT EXISTS idx_memories_type   ON memories(memory_type);