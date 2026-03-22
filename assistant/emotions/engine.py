from .state import EmotionalState
from datetime import datetime, timezone

class EmotionEngine:

    def update(self, state: EmotionalState, sentiment: str) -> EmotionalState:
        msg_sentiment = sentiment.lower()
        if msg_sentiment == "positive":
            state.mood       += 0.05 
            state.trust      += 0.03
            state.engagement += 0.04
        if msg_sentiment == "negative":
            state.mood   -= 0.04
            state.stress += 0.05
        if msg_sentiment == "rude":
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
    
    # For saving/loading the emotional state, we can convert it to/from a dictionary.
    def to_dict(self) -> dict:
        return {
            "mood":       self.mood,
            "trust":      self.trust,
            "stress":     self.stress,
            "engagement": self.engagement,
        }
    
    # Create an EmotionalState from a dictionary, using defaults if keys are missing.
    @classmethod
    def from_dict(cls, data: dict) -> "EmotionalState":
        return cls(
            mood=       float(data.get("mood",       0.5)),
            trust=      float(data.get("trust",      0.5)),
            stress=     float(data.get("stress",     0.2)),
            engagement= float(data.get("engagement", 0.7)),
        )