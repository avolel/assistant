from datetime import datetime
from typing import List, Optional
import uuid
from ..llm.base import LLMProvider, LLMMessage
from ..core.identity import AssistantIdentity
from ..memory.short_term import ShortTermMemory
from ..database.connection import get_db_connection
from .prompt_builder import PromptBuilder

class ConversationEngine:
    def __init__(self, llm: LLMProvider, identity: AssistantIdentity,
        owner_id: str) -> None:
        self.llm = llm
        self.identity = identity
        self.owner_id = owner_id
        self.session_id = str(uuid.uuid4())
        self.stm = ShortTermMemory(self.session_id)
        self.prompt_builder = PromptBuilder()
        self._init_session()

    # Initialize a new conversation session in the databaseS
    def _init_session(self) -> None:
        with get_db_connection() as db:
            db.execute("INSERT INTO sessions VALUES (?,?,?,?,?)",
                (self.session_id, self.owner_id,datetime.now(datetime.timezone.utc).isoformat(), None, None))

    # Main method to handle a user message and generate a response    
    async def chat(self, user_message: str, extra_context: str = "") -> str:
        self.stm.add("user", user_message)

        system = self.prompt_builder.build_system(self.identity, extra_context)
        history = self.stm.get_recent() # Get recent conversation history for context

        messages = [LLMMessage(role="system", content=system)]
        messages += [LLMMessage(role=t["role"], content=t["content"])
                    for t in history[:-1]]   # Exclude last (just added)
        messages.append(LLMMessage(role="user", content=user_message))

        response = await self.llm.complete(messages)
        self.stm.add("assistant", response.content)
        return response.content