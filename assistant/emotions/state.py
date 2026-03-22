# EmotionalState is a simple value object that holds the four mood variables.
# All four values are floats in [0.0, 1.0] and drift back toward their baselines over time.
from dataclasses import dataclass
from datetime import datetime


@dataclass
class EmotionalState:
    mood:       float = 0.5   # 0.0 = very negative, 1.0 = very positive. Baseline: 0.5
    trust:      float = 0.5   # 0.0 = no trust, 1.0 = full trust. Baseline: 0.5
    stress:     float = 0.2   # 0.0 = calm, 1.0 = overwhelmed. Baseline: 0.2 (low by default)
    engagement: float = 0.7   # 0.0 = disengaged, 1.0 = fully engaged. Baseline: 0.7
    updated_at: datetime = None

    def clamp(self) -> None:
        """Ensure all four values stay within [0.0, 1.0] after updates.
        Uses setattr/getattr to apply the same logic to all fields without repetition.
        `setattr(obj, 'mood', val)` is equivalent to `obj.mood = val` but works with a string name."""
        for attr in ("mood", "trust", "stress", "engagement"):
            setattr(self, attr, max(0.0, min(1.0, getattr(self, attr))))

    def to_dict(self) -> dict:
        """Serialize to a plain dict for JSON responses and DB storage."""
        return {
            "mood":       self.mood,
            "trust":      self.trust,
            "stress":     self.stress,
            "engagement": self.engagement
        }