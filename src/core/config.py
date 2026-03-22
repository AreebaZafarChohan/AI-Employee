from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/gold_tier"
    SQLITE_URL: str = "sqlite:///./dashboard.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-me-to-a-random-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # Logging
    LOG_LEVEL: str = "INFO"

    # Pipeline
    STAGE_TIMEOUT_SECONDS: int = 30
    MAX_RETRIES: int = 3
    RETRY_BACKOFF: list[int] = [60, 300, 900]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    # Data Retention
    RETENTION_DAYS: int = 90

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Vault
    VAULT_PATH: str = "./AI-Employee-Vault"

    # AI Keys
    GEMINI_API_KEY: str = ""
    GROK_API_KEY: str = ""

    # AI Models
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GROK_MODEL: str = "grok-3"

    # Server
    PORT: int = 8000

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
