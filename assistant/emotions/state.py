from dataclasses import dataclass
from datetime import datetime

# This class represents the emotional state of the assistant, 
# which can be influenced by interactions with the user and other factors. 
# It includes attributes for mood, trust, stress, and engagement, 
# as well as a timestamp for when the state was last updated.
@dataclass
class EmotionalState:
    mood: float        = 0.5   # 0.0 (very negative) – 1.0 (very positive)
    trust: float       = 0.5   # 0.0 (no trust)      – 1.0 (full trust)
    stress: float      = 0.2   # 0.0 (calm)          – 1.0 (overwhelmed)
    engagement: float  = 0.7   # 0.0 (disengaged)    – 1.0 (fully engaged)
    updated_at: datetime = None

    # This method updates the emotional state based on an interaction with the user.
    def clamp(self) -> None:
        """Ensure all values stay in [0, 1]."""
        for attr in ("mood", "trust", "stress", "engagement"):
            setattr(self, attr, max(0.0, min(1.0, getattr(self, attr))))