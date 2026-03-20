from datetime import datetime
import zoneinfo
from unittest.mock import patch
from assistant.time_awareness.service import TimeAwarenessService

# Tests for the TimeAwarenessService, which provides time context to the assistant. 
def make_svc(): return TimeAwarenessService(timezone="UTC")

# Test that the context string includes the current day of the week, which is important for time awareness. 
def test_context_string_contains_day():
    svc = make_svc()
    ctx = svc.to_prompt_text()
    assert "Time Context" in ctx

# Test that the service correctly identifies when it's a weekend, which may affect the assistant's behavior. 
def test_weekend_not_available():
    svc = make_svc()
    # Patch to a Saturday
    saturday = datetime(2024, 3, 16, 12, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
    with patch.object(svc, "now", return_value=saturday):
        assert svc.is_available() is False