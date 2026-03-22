# FastAPI application factory.
# Routers are defined in routes/ and mounted here with URL prefixes.
# Static files (React build) are served from frontend/dist/ for production use.
# In development, Vite's dev server (port 5173) handles the frontend.
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import pathlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import chat, identity, health, voice, sessions

app = FastAPI(title="Personal AI Assistant API", version="1.0.0")

# CORS middleware allows the React dev server (localhost:5173) to call this API.
# In production the frontend is served from this same origin, so CORS is only needed for local dev.
# allow_methods=["*"] and allow_headers=["*"] permit all methods and headers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],   # Vite dev server URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount each router under its URL prefix. All API routes start with /api/.
app.include_router(health.router,    prefix="/api")
app.include_router(identity.router,  prefix="/api/identity")
app.include_router(chat.router,      prefix="/api/chat")
app.include_router(voice.router,     prefix="/api/voice")
app.include_router(sessions.router,  prefix="/api/sessions")
# Memory router is commented out — the /api/memory endpoints exist in routes/memory.py
# but are not currently wired in. Uncomment to re-enable:
# app.include_router(memory.router, prefix="/api/memory")

# Resolve the path to the React build output relative to this file.
# __file__ is the absolute path of this module; .parent.parent.parent navigates up to the repo root.
DIST = pathlib.Path(__file__).parent.parent.parent / "frontend" / "dist"

if DIST.exists():
    # Serve static assets (JS bundles, CSS) under /assets/
    app.mount("/assets", StaticFiles(directory=str(DIST / "assets")), name="assets")

    # Catch-all route: any path that doesn't match an API route returns index.html.
    # This enables React Router's client-side navigation — the browser handles routing,
    # not the server. The {full_path:path} wildcard captures everything including slashes.
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        index = DIST / "index.html"
        return FileResponse(str(index))