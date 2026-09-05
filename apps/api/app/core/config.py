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
    POSTGRES_PORT: int
    DATABASE_URL: str

    # Redis
    REDIS_PORT: int
    REDIS_URL: str

    # Qdrant
    QDRANT_PORT: int
    QDRANT_URL: str

    # AI Providers
    OPENAI_API_KEY: str | None = None

    ANTHROPIC_API_KEY: str | None = None

    QWEN_API_KEY: str | None = None
    QWEN_BASE_URL: str | None = None

    EMBEDDING_API_KEY: str | None = None
    EMBEDDING_BASE_URL: str | None = None
    EMBEDDING_MODEL: str | None = None
    EMBEDDING_DIM: int = 1024
    EMBEDDING_BATCH: int = 16
    KNOWLEDGE_CONTEXT_TOKENS: int = 1024
    RERANK_API_KEY: str | None = None
    RERANK_BASE_URL: str | None = None
    RERANK_MODEL: str | None = None

    KNOWLEDGE_UPLOAD_DIR: str = str(
        Path(__file__).resolve().parents[2] / "data" / "knowledge"
    )

    # Backend
    API_PORT: int = 8000

    # R5 A2A：空 URL = Writer 进程内；有 URL 则 HTTP 信封调对端
    A2A_WRITER_URL: str | None = None
    A2A_INTERNAL_KEY: str = "dev-a2a-key"

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_IN: int = 15
    JWT_REFRESH_EXPIRES_IN: int = 7

    # Frontend
    WEB_PORT: int = 5173
    VITE_API_URL: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8"
    )


settings = Settings()
