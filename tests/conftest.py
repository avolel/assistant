import pytest, asyncio
from unittest.mock import AsyncMock
from assistant.llm.base import LLMMessage, LLMResponse

@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.complete.return_value = LLMResponse(content="Mock response", model="mock")
    return llm
# tests/unit/test_emotion_engine.py
import pytest
from assistant.emotions.state import EmotionalState
from assistant.emotions.engine import EmotionEngine
 
@pytest.fixture
def engine(): return EmotionEngine()
 
@pytest.fixture
def state(): return EmotionalState() # Start with a neutral emotional state for testing.

# Test that positive inputs increase mood, which is a core function of the emotional engine. 
def test_positive_raises_mood(engine, state):
    new = engine.update(state, "thank you, that was amazing!")
    assert new.mood > 0.5

# Test that rude inputs reduce trust, which is a key aspect of the emotional state. 
def test_rude_reduces_trust(engine, state):
    new = engine.update(state, "you are so stupid")
    assert new.trust < 0.5

# Test that the emotional state is always clamped between 0 and 1, even after extreme inputs. 
def test_state_always_clamped(engine, state):
    for _ in range(30):
        state = engine.update(state, "you are worthless shut up")
    assert 0.0 <= state.trust <= 1.0
    assert 0.0 <= state.stress <= 1.0

@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    """Redirect DB to a temp path for each test."""
    db_path = tmp_path / "test.db"
    import assistant.database.connection as conn_mod
    monkeypatch.setattr(conn_mod, "DB_PATH", db_path)
    from assistant.database.migrations import run_migrations
    run_migrations()
    yield

@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.complete.return_value = LLMResponse(content="Mock response", model="mock")
    return llm