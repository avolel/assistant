# Entry Point for the application
import asyncio, typer
import uvicorn
from rich.console import Console
from rich.prompt import Prompt
from assistant.core.assistant import AssistantCore
from assistant.core.identity import IdentityManager
from assistant.memory.summarizer import MemorySummarizer

# Initialize the application
app = typer.Typer(help="Always-On Personal AI Assistant")
console = Console()

# Define the CLI commands
# First-time setup wizard.
@app.command()
def setup():
    core = AssistantCore()
    core.setup()

# Export a conversation session to a file.
@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def export(ctx: typer.Context):
    """Export a conversation to ~/assistant_exports/. Usage: export --format text|json|markdown --session ID"""
    from assistant.database.connection import get_db_connection
    from assistant.conversation.history import ConversationHistory

    # Parse args manually from ctx.args
    args = ctx.args
    format_type = "text"
    session = None

    for i, arg in enumerate(args):
        if arg in ("--format", "--format-type") and i + 1 < len(args):
            format_type = args[i + 1]
        if arg == "--session" and i + 1 < len(args):
            session = args[i + 1]

    if format_type not in ("text", "json", "markdown"):
        console.print("[red]Invalid format. Choose: text, json, markdown[/red]")
        raise typer.Exit()

    with get_db_connection() as db:
        if session:
            row = db.execute(
                "SELECT session_id FROM sessions WHERE session_id = ?",
                (session,)
            ).fetchone()
        else:
            row = db.execute(
                "SELECT session_id FROM sessions ORDER BY started_at DESC LIMIT 1"
            ).fetchone()

    if not row:
        console.print("[red]No session found.[/red]")
        raise typer.Exit()

    session_id = row["session_id"]
    history = ConversationHistory(session_id)
    path = history.export(fmt=format_type)
    console.print(f"[green]✓ Exported to {path}[/green]")

# Start a text conversation session.
@app.command()
def chat():
    mgr = IdentityManager()
    if not mgr.is_configured():
        console.print("[red]Not configured. Run: python main.py setup[/red]")
        raise typer.Exit()
 
    core = AssistantCore()
    core.start()
    name = core.identity.name
    console.print(f"\n[bold blue]  {name} is ready. Type 'quit' to exit.[/bold blue]\n")
 
    async def loop():
        while True:
            user_input = Prompt.ask("[bold]You[/bold]")
            if user_input.lower() in ("quit", "exit", "bye"):
                console.print(f"[dim]{name}: Goodbye! Saving our conversation...[/dim]")
                summarizer = MemorySummarizer(core.engine.llm)
                turns = core.engine.memory.get_recent_turns(50)
                summary = await summarizer.summarize_session(turns)
                if summary:
                    await core.engine.memory.store_memory(
                        summary, "conversation_summary", importance=0.6
                    )
                    console.print(f"[dim]  ✓ Session saved to memory.[/dim]")
                break
            response = await core.engine.chat(user_input)
            console.print(f"[bold cyan]{name}:[/bold cyan] {response}\n")
 
    asyncio.run(loop()) # Run the async chat loop

# Start the FastAPI backend server.
@app.command()
def serve():    
    console.print("[bold blue]  Starting API server on http://localhost:8000[/bold blue]")
    uvicorn.run("assistant.api.app:app", host="127.0.0.1",
                port=8000, reload=True)

@app.command()
def sessions():
    """List past conversation sessions."""
    from assistant.core.identity import IdentityManager
    from assistant.core.session import SessionManager

    mgr = IdentityManager()
    identity = mgr.load()
    if not identity:
        console.print("[red]Not configured. Run: python main.py setup[/red]")
        raise typer.Exit()

    owner_id = identity.owners[0].owner_id
    sm = SessionManager()
    session_list = sm.list_sessions(owner_id)

    if not session_list:
        console.print("[dim]No sessions found.[/dim]")
        raise typer.Exit()

    from rich.table import Table
    table = Table(title="Past Sessions", show_header=True)
    table.add_column("Session ID",  style="dim",  width=38)
    table.add_column("Started",     style="cyan", width=20)
    table.add_column("Duration",    style="green",width=12)
    table.add_column("Turns",       style="white",width=6)
    table.add_column("Summary",     style="white")

    for s in session_list:
        started = s.started_at[:19].replace("T", " ")
        summary = (s.summary[:60] + "...") if s.summary and len(s.summary) > 60 else (s.summary or "—")
        table.add_row(s.session_id, started, s.duration,
                      str(s.turn_count), summary)

    console.print(table)


@app.command()
def resume(session_id: str):
    """Resume a previous conversation session."""
    from assistant.core.identity import IdentityManager
    from assistant.core.session import SessionManager
    from assistant.core.assistant import AssistantCore

    mgr = IdentityManager()
    identity = mgr.load()
    if not identity:
        console.print("[red]Not configured. Run: python main.py setup[/red]")
        raise typer.Exit()

    owner_id = identity.owners[0].owner_id
    sm = SessionManager()

    # Load the session and its turns
    session = sm.get_session(session_id)
    if not session or session.owner_id != owner_id:
        console.print(f"[red]Session '{session_id}' not found.[/red]")
        raise typer.Exit()

    resumed_id = sm.resume(session_id, owner_id)
    if not resumed_id:
        console.print("[red]Could not resume session.[/red]")
        raise typer.Exit()

    # Show previous turns
    turns = sm.get_turns(session_id)
    console.print(f"\n[bold blue]Resuming session from {session.started_at[:19].replace('T', ' ')}[/bold blue]")
    console.print(f"[dim]{len(turns)} previous turn(s)[/dim]\n")

    for t in turns[-6:]:   # show last 6 turns for context
        role = "[bold]You[/bold]" if t["role"] == "user" else "[bold cyan]Assistant[/bold cyan]"
        console.print(f"{role}: {t['content']}\n")

    # Start chat loop with existing session
    core = AssistantCore()
    core.start(session_id=resumed_id)
    name = core.identity.name

    async def loop():
        while True:
            user_input = console.input("[bold]You[/bold]: ")
            if user_input.lower() in ("quit", "exit", "bye"):
                console.print(f"[dim]{name}: Goodbye![/dim]")
                break
            response = await core.engine.chat(user_input)
            console.print(f"[bold cyan]{name}:[/bold cyan] {response}\n")

    import asyncio
    asyncio.run(loop())


@app.command()
def delete_session(session_id: str):
    """Delete a session and all its turns."""
    from assistant.core.identity import IdentityManager
    from assistant.core.session import SessionManager

    mgr = IdentityManager()
    identity = mgr.load()
    if not identity:
        console.print("[red]Not configured. Run: python main.py setup[/red]")
        raise typer.Exit()

    owner_id = identity.owners[0].owner_id
    sm = SessionManager()

    session = sm.get_session(session_id)
    if not session or session.owner_id != owner_id:
        console.print(f"[red]Session '{session_id}' not found.[/red]")
        raise typer.Exit()

    confirm = console.input(
        f"[yellow]Delete session with {session.turn_count} turns? (yes/no): [/yellow]"
    )
    if confirm.lower() != "yes":
        console.print("[dim]Cancelled.[/dim]")
        raise typer.Exit()

    deleted = sm.delete_session(session_id, owner_id)
    if deleted:
        console.print(f"[green]✓ Session deleted.[/green]")
    else:
        console.print(f"[red]Failed to delete session.[/red]")

if __name__ == "__main__":
    app()