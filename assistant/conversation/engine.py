# ConversationEngine is the heart of the system.
# It orchestrates a single chat turn: memory recall → emotion analysis → prompt building
# → LLM call → optional tool execution → memory storage → emotion persistence.
from datetime import datetime, timezone
from typing import List, Optional
from unittest import result
from urllib import response
import uuid
import re
from ..llm.base import LLMProvider, LLMMessage
from ..core.identity import AssistantIdentity
from ..memory.short_term import ShortTermMemory
from ..memory.manager import MemoryManager
from ..database.connection import get_db_connection
from ..config.settings import settings
from .prompt_builder import PromptBuilder
from ..emotions.state import EmotionalState
from ..emotions.engine import EmotionEngine
from ..time_awareness.service import TimeAwarenessService
from ..tools.registry import ToolRegistry
from .history import ConversationHistory
from ..emotions.store import EmotionalStateStore

# Importing these modules triggers their @register_tool decorators, which populate the ToolRegistry.
# There are no explicit symbols used — the side effect of importing IS the registration.
import assistant.tools.web_search
import assistant.tools.notes


class ConversationEngine:
    def __init__(self,
                 llm: LLMProvider,
                 identity: AssistantIdentity,
                 owner_id: str) -> None:
        self.llm = llm
        self.identity = identity
        self.owner_id = owner_id
        self.session_id = str(uuid.uuid4())   # New UUID per engine instance = new session per user/tab
        self.memory = MemoryManager(owner_id, self.session_id)
        self.prompt_builder = PromptBuilder()
        self.emotion_store  = EmotionalStateStore()
        self.emotion_engine = EmotionEngine()
        self.time_svc       = TimeAwarenessService(settings.owner_timezone)
        self.tools          = ToolRegistry()
        self.history        = ConversationHistory(self.session_id, max_turns=20)

        # Restore the owner's emotional state from their most recent previous session.
        # This makes mood/trust/stress persist across restarts rather than resetting every time.
        loaded = self.emotion_store.load_latest(owner_id)
        self.emotion_state = loaded if loaded else EmotionalState()

        if loaded:
            print(f"  [emotions] Restored: mood={loaded.mood:.2f} "
                  f"trust={loaded.trust:.2f} stress={loaded.stress:.2f} "
                  f"engagement={loaded.engagement:.2f}")

        self._init_session()

    def _init_session(self) -> None:
        """Create a new session row in the DB. Called once at engine startup."""
        with get_db_connection() as db:
            db.execute("INSERT INTO sessions VALUES (?,?,?,?,?)",
                (self.session_id, self.owner_id,
                 datetime.now(timezone.utc).isoformat(), None, None))

    # `async def` marks this as a coroutine — callers must `await` it.
    # FastAPI and Python's asyncio event loop handle scheduling without blocking the server.
    async def chat(self, user_message: str, extra_context: str = "") -> str:
        """Process one user message end-to-end and return the assistant's reply string."""

        # 1. Save the user turn immediately so it's in memory for context building.
        self.memory.add_turn("user", user_message)

        # 2. Semantic recall: embed the message and find similar past memories in ChromaDB.
        recalled = await self.memory.recall(user_message, n=4)
        memory_ctx = ""

        # 3. Classify the emotional tone of the message (POSITIVE / NEGATIVE / RUDE).
        #    Done in parallel with memory recall conceptually, but sequentially here.
        message_sentiment = await self.llm.emotion_analysis(user_message)

        # 4. Format recalled memories as a markdown block to include in the system prompt.
        if recalled:
            snippets = "\n".join(f"- {m['content']}" for m in recalled)
            memory_ctx = f"## Relevant Memories\n{snippets}\n"

        # 5. Assemble context: memories + current time + current emotional state.
        time_ctx    = self.time_svc.to_prompt_text()
        emotion_ctx = self.emotion_engine.to_prompt_text(self.emotion_state)
        full_ctx = f"{memory_ctx}\n\n{time_ctx}\n\n{emotion_ctx}\n\n{extra_context}"

        # 6. Build the system prompt (identity + persona + context).
        system = self.prompt_builder.build_system(self.identity, full_ctx)
        # Store system prompt on self so _execute_tool and _execute_native_tool can reuse it
        # without rebuilding it — they need the same context when sending tool results back.
        self._last_system = system

        # 7. Assemble the message list: [system] + [all recent turns except the last] + [current user msg].
        #    history[:-1] skips the last turn because we already added the user message above,
        #    and it appears explicitly as the final message.
        history  = self.memory.get_recent_turns()
        messages = [LLMMessage(role="system", content=system)]
        messages += [LLMMessage(role=t["role"], content=t["content"]) for t in history[:-1]]
        messages.append(LLMMessage(role="user", content=user_message))

        # 8. Call the LLM with all registered tools passed as JSON definitions.
        #    The model decides whether to respond directly or call a tool.
        response = await self.llm.complete(messages, tools=self.tools.to_ollama_tools())

        # 9a. Native tool calling: modern models return structured tool_calls in the response object.
        if response.tool_calls:
            response.content = await self._execute_native_tool(response.tool_calls)

        # 9b. Text-based fallback: older models that don't support native tool_calls
        #     may embed "TOOL_CALL: tool_name | param: value" directly in the response text.
        if "TOOL_CALL:" in response.content:
            response.content = await self._execute_tool(response.content)

        # 10. Persist the assistant's reply and trim history to stay within the turn limit.
        self.memory.add_turn("assistant", response.content)
        self.history.trim_if_needed()

        # 11. Update emotional state based on the classified sentiment and save it to DB.
        self.emotion_state = self.emotion_engine.update(self.emotion_state, message_sentiment)
        self.emotion_store.save(self.owner_id, self.session_id, self.emotion_state)

        # 12. Classify the message for long-term memory and store if meaningful.
        memory_type = await self.llm.classify_memory(user_message)
        if memory_type != "none":
            importance = {"user_fact": 0.8, "preference": 0.75, "event": 0.6, "summary": 0.5}.get(memory_type, 0.5)
            await self.memory.store_memory(user_message, memory_type, importance)

        return response.content

    async def _execute_tool(self, llm_output: str) -> str:
        """Parse TOOL_CALL: text syntax, run the tool, inject the result back into the LLM, and return the final reply.
        This is a fallback for models that don't support native structured tool_calls."""
        # re.search scans for the pattern anywhere in the string.
        # Group 1 = tool name, Group 2 = pipe-separated param string.
        match = re.search(r'TOOL_CALL: (\w+)\s*\|?(.*)', llm_output)
        if not match:
            return llm_output
        tool_name  = match.group(1).strip()
        params_str = match.group(2).strip()
        params = {}
        for part in params_str.split("|"):
            if ":" in part:
                k, v = part.split(":", 1)   # maxsplit=1 so values with colons aren't broken
                params[k.strip()] = v.strip()
        try:
            tool   = self.tools.get(tool_name)
            result = await tool.run(**params)   # ** unpacks the dict as keyword arguments
            inject = f"Tool result:\n{result.output}" if result.success else f"Tool error: {result.error}"
            # Rebuild the message list with the tool result injected, then call the LLM again
            # to get a natural language response that incorporates the tool output.
            history  = self.memory.get_recent_turns()
            messages = [LLMMessage(role="system", content=self._last_system)]
            messages += [LLMMessage(role=t["role"], content=t["content"]) for t in history[:-1]]
            messages.append(LLMMessage(role="user", content=inject))
            final = await self.llm.complete(messages)
            return final.content
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Tool execution failed: {e}", exc_info=True)
            return f"I tried to use the {tool_name} tool but ran into an error: {e}"

    async def _execute_native_tool(self, tool_calls: list) -> str:
        """Execute structured tool_calls returned by the LLM, collect all results,
        then send them back to the LLM for a final natural language response."""
        results = []
        for tc in tool_calls:
            # Ollama returns tool calls in OpenAI-compatible format:
            # { "function": { "name": "tool_name", "arguments": { ...params } } }
            func      = tc.get("function", {})
            tool_name = func.get("name", "")
            params    = func.get("arguments", {})

            try:
                tool   = self.tools.get(tool_name)
                result = await tool.run(**params)
                if result.success:
                    results.append(f"Tool '{tool_name}' result:\n{result.output}")
                else:
                    results.append(f"Tool '{tool_name}' error: {result.error}")
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Native tool execution failed: {e}", exc_info=True)
                results.append(f"Tool '{tool_name}' failed: {e}")

        if not results:
            return "I tried to use a tool but got no results."

        # Join all tool results into a single string and send back to the LLM.
        # The LLM then synthesises a natural-language answer using those results.
        inject   = "\n\n".join(results)
        history  = self.memory.get_recent_turns()
        messages = [LLMMessage(role="system", content=self._last_system)]
        messages += [LLMMessage(role=t["role"], content=t["content"]) for t in history[:-1]]
        messages.append(LLMMessage(role="user", content=inject))

        # Pass tools again so the LLM can chain tool calls if needed.
        final = await self.llm.complete(messages, tools=self.tools.to_ollama_tools())
        return final.content