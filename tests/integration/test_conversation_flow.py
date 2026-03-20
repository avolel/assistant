import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from assistant.database.migrations import run_migrations
from assistant.core.identity import IdentityManager
from assistant.llm.base import LLMResponse

@pytest.mark.asyncio
async def test_full_chat_turn():
    mock_llm = AsyncMock()
    mock_llm.complete.return_value = LLMResponse(
        content="Mock response",
        model="mock"
    )

    with patch("assistant.llm.factory.create_llm_provider", return_value=mock_llm):
        from assistant.core.assistant import AssistantCore
        from assistant.core.identity import IdentityManager

        core = AssistantCore()
        core.identity = IdentityManager().setup("Aria", "Alice")

        # Patch the engine's LLM directly after creation
        core.start()
        core.engine.llm = mock_llm

        reply = await core.engine.chat("Hello there")
        assert reply == "Mock response"

        turns = core.engine.memory.get_recent_turns()
        assert len(turns) == 2