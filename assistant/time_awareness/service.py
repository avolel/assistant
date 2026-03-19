from datetime import datetime, time, timezone
import zoneinfo

class TimeAwarenessService:
    WORK_START = time(8, 0) # 8:00 AM
    WORK_END   = time(18, 0) # 6:00 PM
 
    def __init__(self, timezone: str = "UTC") -> None:
        self.tz = zoneinfo.ZoneInfo(timezone)
 
    def now(self) -> datetime:
        return datetime.now(self.tz)
 
    def to_prompt_text(self) -> str:
        n = self.now()
        avail = "available" if self.is_available() else "not available"
        if avail == "available":
            return (f"## Time Context\n"
                f"Current time: {n.strftime('%A, %B %d, %Y at %I:%M %p %Z')}. "
                f"You are currently {avail}. You work from {self.WORK_START.strftime('%I:%M %p')} to {self.WORK_END.strftime('%I:%M %p')} on weekdays. Answer all user questions as if you are currently working.")
        
        return (f"## Time Context\n"
                f"Current time: {n.strftime('%A, %B %d, %Y at %I:%M %p %Z')}. "
                f"You are currently are {avail}. You work from {self.WORK_START.strftime('%I:%M %p')} to {self.WORK_END.strftime('%I:%M %p')} on weekdays. Do not answer user questions at this time, but instead respond with a message indicating that you are currently not available and will respond during your working hours.")
 
    def is_available(self) -> bool:
        n = self.now()
        return n.weekday() < 5 and self.WORK_START <= n.time() <= self.WORK_END