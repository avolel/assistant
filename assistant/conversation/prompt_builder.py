# PromptBuilder constructs the system prompt that is sent to the LLM at the start of every request.
# The system prompt defines WHO the assistant is — it's the LLM's persistent "identity" for the session.
from typing import List
from ..core.identity import AssistantIdentity

class PromptBuilder:

    def build_system(self, identity: AssistantIdentity, extra_context: str = "") -> str:
        """Assemble the system prompt from identity fields and any runtime context
        (recalled memories, emotional state, time awareness).

        The extra_context block is pre-formatted markdown injected after the base identity.
        It typically contains:  ## Relevant Memories / ## Time Context / ## Emotional State
        """
        # ", ".join([...]) converts a list to a comma-separated string — Python equivalent of Array.join()
        traits     = ", ".join(identity.personality_traits)
        owner_name = identity.owners[0].name if identity.owners else "the user"
        return (
            f"## Identity\n"
            f"You are {identity.name}. {identity.persona_description}\n\n"
            f"## Personality\nTraits: {traits}\n\n"
            f"## Owner\nYou are assisting {owner_name}.\n"
            # Conditional string append: only include extra_context if it's not empty.
            # In Python, empty string is falsy, so `if extra_context` guards against blank sections.
            + (f"\n{extra_context}" if extra_context else "")
        )