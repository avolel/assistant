# Entry Point for the application
import asyncio, typer
from rich.console import Console
from rich.prompt import Prompt
from assistant.core.assistant import AssistantCore
from assistant.core.identity import IdentityManager

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
                console.print(f"[dim]{name}: Goodbye![/dim]")
                break
            response = await core.engine.chat(user_input)
            console.print(f"[bold cyan]{name}:[/bold cyan] {response}\n")
 
    asyncio.run(loop()) # Run the async chat loop

if __name__ == "__main__":
    app()