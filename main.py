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

if __name__ == "__main__":
    app()