from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated application settings loaded from environment variables."""

    app_env: str = "development"
    log_level: str = "INFO"
    frontend_origin: str = "http://localhost:5173"
    database_url: str = Field(
        default="postgresql+asyncpg://lenny:change-me-locally@localhost:5433/lenny_growth"
    )
    embedding_dimension: int = Field(default=768, gt=0)
    embedding_provider: str = "ollama"
    fastembed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    fastembed_cache_dir: str | None = None
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.2:3b"
    ollama_embedding_model: str = "nomic-embed-text"
    llm_timeout_seconds: float = Field(default=120.0, gt=0, le=600)
    default_llm_provider: str = "ollama"
    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = "claude-sonnet-4-6"
    transcript_repository_url: str = (
        "https://github.com/LennysNewsletter/lennys-newsletterpodcastdata.git"
    )
    transcript_data_dir: str = "data/raw/lennys-newsletterpodcastdata"
    chunk_target_tokens: int = Field(default=650, ge=100, le=2000)
    chunk_overlap_tokens: int = Field(default=100, ge=0, le=500)
    embedding_batch_size: int = Field(default=16, ge=1, le=128)
    retrieval_top_k: int = Field(default=5, ge=1, le=20)
    retrieval_score_threshold: float = Field(default=0.52, ge=0.0, le=1.0)
    static_dir: str | None = None

    @field_validator("database_url")
    @classmethod
    def use_async_postgres_driver(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
