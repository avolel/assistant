from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

# Define the Settings class using Pydantic's BaseSettings
class Settings(BaseSettings):
    llm_provider: str = "ollama"
    llm_model: str = "gpt-oss:20b"
    llm_base_url:   str   = "http://localhost:11434"
    llm_temperature:float = 0.7

    embed_model:    str   = "nomic-embed-text:latest"
    stm_max_turns:  int   = 20
    ltm_n_results:  int   = 5

    voice_enabled:  bool  = False
    stt_model_size: str   = "base"
 
    owner_name:     Optional[str] = None
    owner_email:    Optional[str] = None
    owner_timezone: str   = "UTC"
 
    smtp_host:      str   = "smtp.gmail.com"
    smtp_port:      int   = 587
    smtp_user:      Optional[str] = None
    smtp_pass:      Optional[str] = None

    # Pydantic settings configuration
    class Config:
        env_file = ".env"
        env_prefix = "ASSISTANT_"

# Create a global settings instance
settings = Settings()