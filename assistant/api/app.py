from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import pathlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import chat, identity, health, voice, sessions

app = FastAPI(title="Personal AI Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(identity.router, prefix="/api/identity")
app.include_router(chat.router,     prefix="/api/chat")
app.include_router(voice.router,    prefix="/api/voice")
app.include_router(sessions.router, prefix="/api/sessions")
#app.include_router(memory.router,   prefix="/api/memory")

DIST = pathlib.Path(__file__).parent.parent.parent / "frontend" / "dist"

if DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST / "assets")), name="assets")

    # Catch-all — serve index.html for any non-API route
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        index = DIST / "index.html"
        return FileResponse(str(index))