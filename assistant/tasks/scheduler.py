# Background scheduler: polls every 5 minutes; when the clock flips to "on",
# replays all pending deferred tasks through their original conversation engine.
import asyncio
import logging
from ..time_awareness.service import TimeAwarenessService
from .deferred import DeferredTaskManager
from ..config.settings import settings

log = logging.getLogger(__name__)
POLL_INTERVAL = 300   # seconds (5 minutes)


async def run_deferred_scheduler(get_engine_fn, owner_id: str) -> None:
    """
    Continuously polls for pending tasks and executes them when the assistant is on-clock.
    
    get_engine_fn: async callable that takes a session_id and returns a ConversationEngine.
                   Pass `get_or_create_engine` from session_store.
    owner_id:      The primary owner's ID (tasks are per-owner).
    """
    time_svc = TimeAwarenessService(settings.owner_timezone)
    deferred = DeferredTaskManager()
    was_available = time_svc.is_available()

    log.info("[scheduler] Deferred task scheduler started.")

    while True:
        await asyncio.sleep(POLL_INTERVAL)
        try:
            now_available = time_svc.is_available()

            # Fire when transitioning from off → on, OR on every poll while on-clock
            # so tasks queued during a long off period don't wait another 5 minutes.
            if now_available:
                pending = deferred.get_pending(owner_id)
                if pending:
                    log.info(f"[scheduler] Processing {len(pending)} deferred task(s).")
                for task in pending:
                    try:
                        engine = await get_engine_fn(task["session_id"])
                        await engine.chat(task["message"])
                        deferred.mark_done(task["task_id"])
                        log.info(f"[scheduler] Task {task['task_id']} completed.")
                    except Exception as e:
                        deferred.mark_failed(task["task_id"])
                        log.error(f"[scheduler] Task {task['task_id']} failed: {e}", exc_info=True)

            was_available = now_available
        except Exception as e:
            log.error(f"[scheduler] Unexpected error: {e}", exc_info=True)
