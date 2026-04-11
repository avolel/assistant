# AssistantCore is the top-level orchestrator — it wires together all subsystems
# (identity, LLM, conversation engine) and is the entry point for server startup.
import asyncio
from ..database.migrations import run_migrations
from ..core.identity import IdentityManager, AssistantIdentity
from ..conversation.engine import ConversationEngine
from ..llm.factory import create_llm_provider
from ..config.settings import settings

class AssistantCore:
    def __init__(self) -> None:
        run_migrations()
        self.identity_mgr = IdentityManager()
        self.identity: AssistantIdentity = None
        self.engine: ConversationEngine = None

    def setup(self) -> None:
        """Interactive first-run wizard."""
        print("\n  Welcome! Let's set up your assistant.\n")
        a_name  = input("  Assistant name (e.g. Aria): ").strip() or "Aria"
        o_name  = input("  Your name: ").strip() or settings.owner_name
        o_email = input("  Your email (optional): ").strip() or None
        tz      = input("  Your timezone (e.g. America/New_York) [UTC]: ").strip() or settings.owner_timezone
        self.identity = self.identity_mgr.setup(a_name, o_name, o_email, tz)
        print(f"\n  ✓ {a_name} is ready. Run: python run.py\n")

    def start(self) -> None:
        """Load identity from DB and initialise the conversation engine."""
        self.identity = self.identity_mgr.load()
        llm = create_llm_provider(settings.llm_provider, model=settings.llm_model,
                                   base_url=settings.llm_base_url,
                                   emotion_model=settings.llm_model_emotion)
        owner_id = self.identity.owners[0].owner_id
        self.engine = ConversationEngine(llm, self.identity, owner_id)

    async def start_scheduler(self) -> None:
        """Launch the deferred-task background scheduler as an asyncio task."""
        from ..tasks.scheduler import run_deferred_scheduler
        from ..api.session_store import get_or_create_engine
        owner_id = self.identity.owners[0].owner_id
        asyncio.create_task(run_deferred_scheduler(get_or_create_engine, owner_id))
