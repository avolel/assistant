# TimeAwarenessService gives the assistant a sense of the current time and whether it's "working hours".
# The prompt text it generates is injected into every system prompt so the LLM can respond accordingly.
from datetime import datetime, time, timezone
import zoneinfo   # Python 3.9+ stdlib; handles IANA timezone names like "America/New_York"


class TimeAwarenessService:
    WORK_START = time(8,  0)   # 08:00 AM — start of the simulated work day
    WORK_END   = time(18, 0)   # 06:00 PM — end of the simulated work day

    def __init__(self, timezone: str = "UTC") -> None:
        # ZoneInfo("America/New_York") creates a timezone-aware object from an IANA name.
        # Unlike pytz, zoneinfo is in the standard library from Python 3.9.
        self.tz = zoneinfo.ZoneInfo(timezone)

    def now(self) -> datetime:
        """Return the current datetime in the owner's configured timezone."""
        return datetime.now(self.tz)

    def to_prompt_text(self) -> str:
        """Format the current time and availability as a markdown block for the system prompt."""
        n     = self.now()
        avail = "available" if self.is_available() else "not available"
        if avail == "available":
            return (
                f"## Time Context\n"
                f"Current time: {n.strftime('%A, %B %d, %Y at %I:%M %p %Z')}. "
                f"You are currently {avail}. "
                f"You work from {self.WORK_START.strftime('%I:%M %p')} to "
                f"{self.WORK_END.strftime('%I:%M %p')} on weekdays. "
                f"Answer all user questions as if you are currently working."
            )
        return (
            f"## Time Context\n"
            f"Current time: {n.strftime('%A, %B %d, %Y at %I:%M %p %Z')}. "
            f"You are currently {avail}. "
            f"You work from {self.WORK_START.strftime('%I:%M %p')} to "
            f"{self.WORK_END.strftime('%I:%M %p')} on weekdays. "
            f"Do not answer user questions at this time, but instead respond with a message "
            f"indicating that you are currently not available and will respond during your working hours."
        )

    def is_available(self) -> bool:
        """Return True if the current time is within work hours on a weekday.
        weekday() returns 0 (Monday) through 6 (Sunday); < 5 means Mon–Fri."""
        n = self.now()
        return n.weekday() < 5 and self.WORK_START <= n.time() <= self.WORK_END