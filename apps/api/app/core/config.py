from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    """配置类"""

    # Application
    NODE_ENV: str = "development"

    # PostgreSQL
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432

    DATABASE_URL: str

    # Redis
    REDIS_PORT: int = 6379
    REDIS_URL: str

    # Qdrant
    QDRANT_PORT: int = 6333
    QDRANT_URL: str

    # Backend
    API_PORT: int = 8000

    # Frontend
    WEB_PORT: int = 5173
    VITE_API_URL: str = "http://localhost:8000"

    # AI Providers
    OPENAI_API_KEY: str | None = None

    ANTHROPIC_API_KEY: str | None = None

    QWEN_API_KEY: str | None = None
    QWEN_BASE_URL: str | None = None

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8"
    )


settings = Settings()
