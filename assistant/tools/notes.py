# Notes tool: saves, lists, and reads plain markdown files in ~/assistant_notes/.
# All file I/O uses pathlib.Path for clean cross-platform path handling.
import pathlib
from datetime import datetime
from .base import BaseTool, ToolResult
from .registry import register_tool

NOTES_DIR = pathlib.Path.home() / "assistant_notes"   # ~/assistant_notes/


@register_tool
class NotesTool(BaseTool):
    name        = "notes"
    description = "Save or retrieve notes. Actions: save, list, read."
    parameters  = {
        "action":  {"type": "string", "description": "save | list | read"},
        "title":   {"type": "string", "description": "Note title (for save/read)", "optional": True},
        "content": {"type": "string", "description": "Note content (for save)",    "optional": True}
    }

    async def run(self, action: str, title: str = "", content: str = "") -> ToolResult:
        # mkdir(exist_ok=True) creates the directory only if it doesn't already exist.
        NOTES_DIR.mkdir(exist_ok=True)

        if action == "save":
            # Sanitise the title for use as a filename by replacing spaces with underscores.
            path = NOTES_DIR / f"{title.replace(' ', '_')}.md"
            path.write_text(f"# {title}\n_{datetime.now().strftime('%Y-%m-%d')}_\n\n{content}")
            return ToolResult(success=True, output=f"Note '{title}' saved.")

        if action == "list":
            # glob("*.md") returns all .md files in the directory as Path objects.
            files = list(NOTES_DIR.glob("*.md"))
            # .stem is the filename without extension. Reverse the filename sanitisation.
            names = [f.stem.replace("_", " ") for f in files]
            return ToolResult(success=True, output="Notes: " + (", ".join(names) or "none"))

        if action == "read":
            path = NOTES_DIR / f"{title.replace(' ', '_')}.md"
            if path.exists():
                return ToolResult(success=True, output=path.read_text())
            return ToolResult(success=False, output="", error=f"Note '{title}' not found.")

        return ToolResult(success=False, output="", error="Unknown action")