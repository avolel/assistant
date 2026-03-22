# Entry point — starts the FastAPI server via uvicorn.
# `reload=True` watches for file changes and restarts automatically (dev only).
# The string "assistant.api.app:app" means: module path "assistant.api.app", object named "app".
# host="0.0.0.0" binds to all network interfaces, not just localhost.
import uvicorn

if __name__ == "__main__":
    uvicorn.run("assistant.api.app:app", host="0.0.0.0", port=8000, reload=True)