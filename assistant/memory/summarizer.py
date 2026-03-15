from typing import List, Dict
from ..llm.base import LLMProvider, LLMMessage

# Memory summarizer that uses the LLM to generate concise summaries of a list of memories.
class MemorySummarizer:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm
 
    async def summarize_session(self,
                                turns: List[Dict]) -> str:
        if not turns:
            return ""
        transcript = "\n".join(f"{t['role'].upper()}: {t['content']}" for t in turns)
        prompt = (
            "Summarize this conversation in 3-5 sentences. "
            "Focus on: key topics discussed, decisions made, "
            "and any facts learned about the user.\n\n"
            f"CONVERSATION:\n{transcript}"
        )
        resp = await self.llm.complete([LLMMessage(role="user", content=prompt)],
                                        temperature=0.3)
        return resp.content