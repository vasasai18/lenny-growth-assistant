from app.config import Settings


def test_ollama_defaults_match_local_demo() -> None:
    settings = Settings(_env_file=None)

    assert settings.ollama_base_url == "http://localhost:11434"
    assert settings.ollama_chat_model == "llama3.2:3b"
    assert settings.ollama_embedding_model == "nomic-embed-text"
    assert settings.embedding_dimension == 768
    assert settings.llm_timeout_seconds == 120.0

