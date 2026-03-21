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
        self.session_id = str(uuid.uuid4())
        self.memory = MemoryManager(owner_id, self.session_id)
        self.prompt_builder = PromptBuilder()
        self.emotion_state  = EmotionalState()
        self.emotion_engine = EmotionEngine()
        self.time_svc       = TimeAwarenessService(settings.owner_timezone)
        self.tools          = ToolRegistry()
        self.history = ConversationHistory(self.session_id, max_turns=20)
        self._init_session()

    # Initialize a new conversation session in the databaseS
    def _init_session(self) -> None:
        with get_db_connection() as db:
            db.execute("INSERT INTO sessions VALUES (?,?,?,?,?)",
                (self.session_id, self.owner_id,datetime.now(timezone.utc).isoformat(), None, None))

    # Main method to handle a user message and generate a response    
    async def chat(self, user_message: str, extra_context: str = "") -> str:
        self.memory.add_turn("user", user_message)
        recalled = await self.memory.recall(user_message, n=4)
        memory_ctx = ""

        message_sentiment = await self.llm.emotion_analysis(user_message)

        # If relevant memories are recalled, 
        # format them into a context string to include in the system prompt.
        if recalled:
            snippets = "\n".join(f"- {m['content']}" for m in recalled)
            memory_ctx = f"## Relevant Memories\n{snippets}\n"

        time_ctx    = self.time_svc.to_prompt_text()
        emotion_ctx = self.emotion_engine.to_prompt_text(self.emotion_state)
        full_ctx = f"{memory_ctx}\n\n{time_ctx}\n\n{emotion_ctx}\n\n{extra_context}"

        # Build the system prompt with the assistant's identity and the relevant memory context, 
        # along with any extra context provided.
        system = self.prompt_builder.build_system(self.identity, full_ctx)
        self._last_system = system # Store the last system prompt for potential reuse during tool execution.
        
        history = self.memory.get_recent_turns() 
        messages = [LLMMessage(role="system", content=system)]
        messages += [LLMMessage(role=t["role"], content=t["content"])
                     for t in history[:-1]]   # Exclude last (just added)
        messages.append(LLMMessage(role="user", content=user_message))
 
        response = await self.llm.complete(messages, tools=self.tools.to_ollama_tools())

        # Handle native tool_calls (structured JSON from model)
        if response.tool_calls:
            response.content = await self._execute_native_tool(response.tool_calls)
     
        #Check for TOOL_CALL in the response and execute if present, 
        # replacing the response content with the tool output.
        # Keep the old TOOL_CALL: text fallback for other models that don't support structured tool_calls yet.
        if "TOOL_CALL:" in response.content:
            response.content = await self._execute_tool(response.content)

        self.memory.add_turn("assistant", response.content)
        self.history.trim_if_needed()

        # Update emotional state based on the conversation and response.
        self.emotion_state = self.emotion_engine.update(self.emotion_state, message_sentiment)

        # Extract and store any relevant facts from the user's message for long-term memory storage.
        await self.memory.extract_and_store_facts(user_message)
        return response.content
    
    # Parse TOOL_CALL: syntax, execute, inject result, get final reply.
    async def _execute_tool(self, llm_output: str) -> str:
        match = re.search(r'TOOL_CALL: (\w+)\s*\|?(.*)', llm_output)
        if not match:
            return llm_output
        tool_name = match.group(1).strip()
        params_str = match.group(2).strip()
        params = {}
        for part in params_str.split("|"):
            if ":" in part:
                k, v = part.split(":", 1)
                params[k.strip()] = v.strip()
        try:
            tool = self.tools.get(tool_name)
            result = await tool.run(**params)
            inject = f"Tool result:\n{result.output}" if result.success else f"Tool error: {result.error}"
            history = self.memory.get_recent_turns()
            messages = [LLMMessage(role="system", content=self._last_system)]  # ← now defined
            messages += [LLMMessage(role=t["role"], content=t["content"]) for t in history[:-1]]  # ← fixed
            messages.append(LLMMessage(role="user", content=inject))
            final = await self.llm.complete(messages)
            return final.content
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Tool execution failed: {e}", exc_info=True)
            return f"I tried to use the {tool_name} tool but ran into an error: {e}"

    # Execute native tool calls defined in the LLM response's tool_calls field,
    # gather results, and send them back to the LLM for a final response generation.    
    async def _execute_native_tool(self, tool_calls: list) -> str:
        results = []
        for tc in tool_calls:
            func = tc.get("function", {})
            tool_name = func.get("name", "")
            params = func.get("arguments", {})

            try:
                tool = self.tools.get(tool_name)
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

        # Send tool results back to the LLM for a final natural language response
        inject = "\n\n".join(results)
        history = self.memory.get_recent_turns()
        messages = [LLMMessage(role="system", content=self._last_system)]
        messages += [LLMMessage(role=t["role"], content=t["content"]) for t in history[:-1]]
        messages.append(LLMMessage(role="user", content=inject))

        final = await self.llm.complete(messages, tools=self.tools.to_ollama_tools())
        return final.content