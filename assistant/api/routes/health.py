# Health check endpoint — used to verify the server is running.
# Mounted at GET /api/health (note: no prefix added in app.py, the router uses /api directly).
import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ...config.settings import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    ollama_up = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{settings.llm_base_url}/api/tags")
            ollama_up = r.status_code == 200
    except Exception:
        ollama_up = False

    body = {"status": "ok" if ollama_up else "degraded", "service": "Personal AI Assistant", "ollama": ollama_up}
    return JSONResponse(content=body, status_code=200 if ollama_up else 503)