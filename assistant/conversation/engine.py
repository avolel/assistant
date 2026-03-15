from datetime import datetime, timezone
from typing import List, Optional
import uuid
from ..llm.base import LLMProvider, LLMMessage
from ..core.identity import AssistantIdentity
from ..memory.short_term import ShortTermMemory
from ..memory.manager import MemoryManager
from ..database.connection import get_db_connection
from .prompt_builder import PromptBuilder

class ConversationEngine:
    def __init__(self, llm: LLMProvider, identity: AssistantIdentity,
        owner_id: str) -> None:
        self.llm = llm
        self.identity = identity
        self.owner_id = owner_id
        self.session_id = str(uuid.uuid4())
        self.memory = MemoryManager(owner_id, self.session_id)
        self.prompt_builder = PromptBuilder()
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
        if recalled:
            snippets = "\n".join(f"- {m['content']}" for m in recalled)
            memory_ctx = f"## Relevant Memories\n{snippets}\n"

        # Build the system prompt with the assistant's identity and the relevant memory context, 
        # along with any extra context provided.
        system = self.prompt_builder.build_system(self.identity,
                                               memory_ctx + extra_context)
        history = self.memory.get_recent_turns() 
        messages = [LLMMessage(role="system", content=system)]
        messages += [LLMMessage(role=t["role"], content=t["content"])
                     for t in history[:-1]]   # Exclude last (just added)
        messages.append(LLMMessage(role="user", content=user_message))
 
        response = await self.llm.complete(messages)
        self.memory.add_turn("assistant", response.content)
        # Extract and store any relevant facts from the user's message for long-term memory storage.
        await self.memory.extract_and_store_facts(user_message)
        return response.content