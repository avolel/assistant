from typing import List
from ..core.identity import AssistantIdentity

class PromptBuilder:
    # This class is responsible for constructing the system prompt based on the assistant's identity and any additional context.
    def build_system(self, identity: AssistantIdentity,
                     extra_context: str = "") -> str:
        traits = ", ".join(identity.personality_traits)
        owner_name = identity.owners[0].name if identity.owners else "the user"
        return (
            f"## Identity\n"
            f"You are {identity.name}. {identity.persona_description}\n\n"
            f"## Personality\nTraits: {traits}\n\n"
            f"## Owner\nYou are assisting {owner_name}.\n"
            + (f"\n{extra_context}" if extra_context else "")
        )