# AssistantCore is the top-level orchestrator — it wires together all subsystems
# (identity, LLM, conversation engine) and is the entry point for server startup.
from ..database.migrations import run_migrations
from ..core.identity import IdentityManager, AssistantIdentity
from ..conversation.engine import ConversationEngine
from ..llm.factory import create_llm_provider
from ..config.settings import settings

class AssistantCore:
    def __init__(self) -> None:
        # Run migrations first so the DB schema always exists before any other code runs.
        run_migrations()
        self.identity_mgr = IdentityManager()
        self.identity: AssistantIdentity = None   # Populated by setup() or start()
        self.engine: ConversationEngine = None    # Populated by start()

    def setup(self) -> None:
        """Interactive first-run wizard. Collects identity config from stdin and persists it."""
        print("\n  Welcome! Let's set up your assistant.\n")
        a_name = input("  Assistant name (e.g. Aria): ").strip() or "Aria"
        o_name = input("  Your name: ").strip() or settings.owner_name
        o_email = input("  Your email (optional): ").strip() or None
        # zoneinfo requires IANA timezone strings like "America/New_York", not abbreviations like "EST"
        tz = input("  Your timezone (e.g. America/New_York) [UTC]: ").strip() or settings.owner_timezone
        self.identity = self.identity_mgr.setup(a_name, o_name, o_email, tz)
        print(f"\n  ✓ {a_name} is ready. Run: python run.py\n")

    def start(self) -> None:
        """Load identity from DB and initialise the conversation engine. Call this before serving."""
        self.identity = self.identity_mgr.load()
        # **kwargs passes model/base_url/emotion_model as keyword args to OllamaProvider.__init__
        llm = create_llm_provider(settings.llm_provider, model=settings.llm_model,
                                   base_url=settings.llm_base_url, emotion_model=settings.llm_model_emotion)
        # Always use the first owner for the default engine; multi-owner is handled per-request in session_store
        owner_id = self.identity.owners[0].owner_id
        self.engine = ConversationEngine(llm, self.identity, owner_id)