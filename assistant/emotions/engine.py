from .state import EmotionalState
from datetime import datetime, timezone

class EmotionEngine:
    POS  = {"thank","great","love","perfect","brilliant","amazing","helpful"}
    NEG  = {"wrong","bad","useless","broken","terrible","awful","disappoint"}
    RUDE = {"idiot","stupid","dumb","shut up","worthless","hate you"}

    def update(self, state: EmotionalState,user_message: str) -> EmotionalState:
        msg = user_message.lower()
        if any(kw in msg for kw in self.POS):
            state.mood       += 0.05 
            state.trust      += 0.03
            state.engagement += 0.04
        if any(kw in msg for kw in self.NEG):
            state.mood   -= 0.04
            state.stress += 0.05
        if any(kw in msg for kw in self.RUDE):
            state.trust      -= 0.10
            state.engagement -= 0.08
            state.stress     += 0.08

        # Natural drift toward baseline
        state.mood       += (0.5 - state.mood)       * 0.02
        state.stress     += (0.2 - state.stress)     * 0.03
        state.engagement += (0.7 - state.engagement) * 0.01
        state.clamp()
        state.updated_at = datetime.now(timezone.utc)
        return state
    
    # Converts the emotional state into a textual description for prompting the assistant.
    def to_prompt_text(self, state: EmotionalState) -> str:
        mood_lbl  = "upbeat" if state.mood>0.6 else "neutral" if state.mood>0.35 else "subdued"
        trust_lbl = "trusting" if state.trust>0.6 else "cautious"
        stress_lbl= "calm" if state.stress<0.3 else "a bit stressed" if state.stress<0.6 else "stressed"
        return (f"## Emotional State\nYour current state: mood={mood_lbl}, "
                f"trust={trust_lbl}, stress={stress_lbl}. "
                f"Let this subtly color your tone. Do not mention it directly.")