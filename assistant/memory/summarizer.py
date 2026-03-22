# MemorySummarizer compresses a session's turns into a short summary using the LLM.
# The summary can be stored as a long-term memory or attached to the session record.
from typing import List, Dict
from ..llm.base import LLMProvider, LLMMessage


class MemorySummarizer:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def summarize_session(self, turns: List[Dict]) -> str:
        """Generate a 3–5 sentence summary of a list of conversation turns.
        Returns an empty string if there are no turns to summarize."""
        if not turns:
            return ""
        # Build a plain-text transcript from the turns list.
        # t['role'].upper() makes it read like "USER: ..." / "ASSISTANT: ..."
        transcript = "\n".join(f"{t['role'].upper()}: {t['content']}" for t in turns)
        prompt = (
            "Summarize this conversation in 3-5 sentences. "
            "Focus on: key topics discussed, decisions made, "
            "and any facts learned about the user.\n\n"
            f"CONVERSATION:\n{transcript}"
        )
        # Low temperature (0.3) makes the output more deterministic and factual.
        # For summarization we want accuracy, not creativity.
        resp = await self.llm.complete(
            [LLMMessage(role="user", content=prompt)],
            temperature=0.3
        )
        return resp.content