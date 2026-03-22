from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://localhost/ai_employee"
    PORT: int = 8000
    VAULT_PATH: str = str(Path(__file__).resolve().parent.parent.parent / "AI-Employee-Vault")
    CORS_ORIGIN: str = "http://localhost:3000"
    GEMINI_API_KEY: str = ""
    GROK_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GROK_MODEL: str = "grok-2"
    AI_PROVIDER: str = "grok"  # grok or gemini

    # Gmail OAuth2
    GMAIL_CLIENT_ID: str = ""
    GMAIL_CLIENT_SECRET: str = ""
    GMAIL_REFRESH_TOKEN: str = ""
    GMAIL_USER: str = "me"
    GMAIL_TOKEN_FILE: str = str(Path(__file__).resolve().parent.parent.parent / "token.json")
    GMAIL_CREDENTIALS_FILE: str = str(Path(__file__).resolve().parent.parent.parent / "credentials.json")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


settings = Settings()
