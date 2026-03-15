from ..database.migrations import run_migrations
from ..core.identity import IdentityManager, AssistantIdentity
from ..conversation.engine import ConversationEngine
from ..llm.factory import create_llm_provider
from ..config.settings import settings

# The main assistant core class that manages identity and conversation engine.
class AssistantCore:
    def __init__(self) -> None:
        run_migrations()
        self.identity_mgr = IdentityManager()
        self.identity: AssistantIdentity = None
        self.engine: ConversationEngine = None

    # Interactive first-run wizard. 
    def setup(self) -> None:
        print("\n  Welcome! Let's set up your assistant.\n")
        a_name = input("  Assistant name (e.g. Aria): ").strip() or "Aria"
        o_name = input("  Your name: ").strip() or settings.owner_name
        o_email = input("  Your email (optional): ").strip() or None
        tz = input("  Your timezone (e.g. America/New_York) [UTC]: ").strip() or settings.owner_timezone
        self.identity = self.identity_mgr.setup(a_name, o_name, o_email, tz)
        print(f"\n  ✓ {a_name} is ready. Run: python main.py chat\n")

    # Load identity and prepare the engine.
    def start(self) -> None:
        self.identity = self.identity_mgr.load()
        llm = create_llm_provider(settings.llm_provider, model=settings.llm_model,
                                   base_url=settings.llm_base_url)
        owner_id = self.identity.owners[0].owner_id
        self.engine = ConversationEngine(llm, self.identity, owner_id)