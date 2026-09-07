from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite+aiosqlite:///./lenny.db"
    default_llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    retrieval_top_k: int = 5
    retrieval_min_score: float = 0.18
    cors_origins: str = "http://localhost:3000"
settings = Settings()
