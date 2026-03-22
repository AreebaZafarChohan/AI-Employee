from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    # AI Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROK_API_KEY: str = os.getenv("GROK_API_KEY", "")

    # Vault
    VAULT_PATH: str = os.getenv("VAULT_PATH", "./AI-Employee-Vault")

    # Odoo
    ODOO_URL: str = os.getenv("ODOO_URL", "")
    ODOO_DB: str = os.getenv("ODOO_DB", "odoo")
    ODOO_USERNAME: str = os.getenv("ODOO_USERNAME", "admin")
    ODOO_PASSWORD: str = os.getenv("ODOO_PASSWORD", "admin")

    # Server
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # AI Models
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GROK_MODEL: str = "grok-3"

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
