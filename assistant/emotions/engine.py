# EmotionEngine applies sentiment-driven updates and natural drift to an EmotionalState.
# It does NOT store state — it takes a state in, modifies it, and returns it.
# Persistence is handled by EmotionalStateStore.
from .state import EmotionalState
from datetime import datetime, timezone


class EmotionEngine:

    def update(self, state: EmotionalState, sentiment: str) -> EmotionalState:
        """Apply sentiment-based deltas and then nudge all values toward their natural baselines.
        Modifies the state object in-place and also returns it (fluent pattern)."""
        msg_sentiment = sentiment.lower()

        # Each sentiment class has different effects across the four variables.
        if msg_sentiment == "positive":
            state.mood       += 0.05
            state.trust      += 0.03
            state.engagement += 0.04
        if msg_sentiment == "negative":
            state.mood   -= 0.04
            state.stress += 0.05
        if msg_sentiment == "rude":
            # Rudeness has the strongest negative effect — hits trust and engagement hardest.
            state.trust      -= 0.10
            state.engagement -= 0.08
            state.stress     += 0.08

        # Natural drift: each variable is pulled toward its baseline by 1–3% per turn.
        # Formula: current + (baseline - current) * rate
        # At rate=0.02, values move 2% of the gap toward baseline each turn — slow decay.
        state.mood       += (0.5 - state.mood)       * 0.02
        state.stress     += (0.2 - state.stress)     * 0.03
        state.engagement += (0.7 - state.engagement) * 0.01

        state.clamp()   # Ensure no value goes outside [0.0, 1.0]
        state.updated_at = datetime.now(timezone.utc)
        return state

    def to_prompt_text(self, state: EmotionalState) -> str:
        """Convert numeric state to descriptive labels for the system prompt.
        The LLM is told to let this 'subtly color' its tone — it should influence style, not content."""
        mood_lbl   = "upbeat"        if state.mood > 0.6   else "neutral"        if state.mood > 0.35   else "subdued"
        trust_lbl  = "trusting"      if state.trust > 0.6  else "cautious"
        stress_lbl = "calm"          if state.stress < 0.3 else "a bit stressed" if state.stress < 0.6  else "stressed"
        return (
            f"## Emotional State\nYour current state: mood={mood_lbl}, "
            f"trust={trust_lbl}, stress={stress_lbl}. "
            f"Let this subtly color your tone. Do not mention it directly."
        )

    def to_dict(self) -> dict:
        """Serialize the engine's current state for DB storage. Note: uses self attributes,
        so this only works when EmotionEngine is used as a stateful object (not the pattern here)."""
        return {
            "mood":       self.mood,
            "trust":      self.trust,
            "stress":     self.stress,
            "engagement": self.engagement,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EmotionalState":
        """@classmethod receives the class itself as `cls` instead of an instance as `self`.
        Used as an alternative constructor: EmotionEngine.from_dict({...}) returns an EmotionalState."""
        return cls(
            mood=       float(data.get("mood",       0.5)),
            trust=      float(data.get("trust",      0.5)),
            stress=     float(data.get("stress",     0.2)),
            engagement= float(data.get("engagement", 0.7)),
        )