# Pydantic BaseSettings automatically reads values from environment variables and .env files.
# Each field maps to an env var: env_prefix "ASSISTANT_" + field name in uppercase.
# e.g. llm_model → ASSISTANT_LLM_MODEL. Fields with defaults are optional in .env.
# Optional[str] = None means the field can be a string or None (not set).
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    llm_provider:       str   = "ollama"
    llm_model:          str   = "gpt-oss:20b"
    llm_model_emotion:  str   = "llama3.1:8b"   # Smaller model used only for sentiment classification
    llm_base_url:       str   = "http://localhost:11434"
    llm_temperature:    float = 0.7

    embed_model:        str   = "nomic-embed-text:latest"
    stm_max_turns:      int   = 20               # How many turns to keep in short-term memory
    ltm_n_results:      int   = 5                # How many long-term memories to inject per request

    voice_enabled:      bool  = False
    stt_model_size:     str   = "base"           # Whisper model size: base/small/medium/large

    owner_name:         Optional[str] = None
    owner_email:        Optional[str] = None
    owner_timezone:     str   = "UTC"

    assistant_name:     str   = "Aria"

    class Config:
        env_file = ".env"        # Load from .env file in the working directory
        env_prefix = "ASSISTANT_"  # All env vars must be prefixed with ASSISTANT_

# Module-level singleton — import `settings` anywhere to access config values.
settings = Settings()