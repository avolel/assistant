import pathlib
from datetime import datetime
from .base import BaseTool, ToolResult
from .registry import register_tool

# Simple note-taking tool that saves notes as markdown files in a local directory. 
NOTES_DIR = pathlib.Path.home() / "assistant_notes"
 
@register_tool
class NotesTool(BaseTool):
    name = "notes"
    description = "Save or retrieve notes. Actions: save, list, read."
    parameters = {
        "action": {"type": "string", "description": "save | list | read"},
        "title":  {"type": "string", "description": "Note title (for save/read)", "optional": True},
        "content":{"type": "string", "description": "Note content (for save)", "optional": True}
    }
 
    async def run(self, action: str, title: str = "", content: str = "") -> ToolResult:
        NOTES_DIR.mkdir(exist_ok=True)
        if action == "save":
            path = NOTES_DIR / f"{title.replace(' ','_')}.md"
            path.write_text(f"# {title}\n_{datetime.now().strftime('%Y-%m-%d')}_\n\n{content}")
            return ToolResult(success=True, output=f"Note '{title}' saved.")
        if action == "list":
            files = list(NOTES_DIR.glob("*.md"))
            names = [f.stem.replace("_"," ") for f in files]
            return ToolResult(success=True, output="Notes: " + (", ".join(names) or "none"))
        if action == "read":
            path = NOTES_DIR / f"{title.replace(' ','_')}.md"
            if path.exists():
                return ToolResult(success=True, output=path.read_text())
            return ToolResult(success=False, output="", error=f"Note '{title}' not found.")
        return ToolResult(success=False, output="", error="Unknown action")