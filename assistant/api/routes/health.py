# Health check endpoint — used to verify the server is running.
# Mounted at GET /api/health (note: no prefix added in app.py, the router uses /api directly).
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "Personal AI Assistant"}