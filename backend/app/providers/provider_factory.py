from app.config import Settings, get_settings
from app.providers.base import BaseLLMProvider, ProviderConfigurationError
from app.providers.cloud_provider import AnthropicProvider
from app.providers.ollama_provider import OllamaProvider


SUPPORTED_PROVIDERS = ("ollama", "anthropic")


def create_provider(
    provider_name: str | None = None,
    settings: Settings | None = None,
) -> BaseLLMProvider:
    config = settings or get_settings()
    selected = (provider_name or config.default_llm_provider).strip().lower()

    if selected == "ollama":
        return OllamaProvider(
            base_url=config.ollama_base_url,
            model=config.ollama_chat_model,
            timeout_seconds=config.llm_timeout_seconds,
        )

    if selected == "anthropic":
        if config.anthropic_api_key is None or not config.anthropic_api_key.get_secret_value():
            raise ProviderConfigurationError(
                "Cloud mode is not configured. Add ANTHROPIC_API_KEY to .env or "
                "choose Local Ollama."
            )
        return AnthropicProvider(
            api_key=config.anthropic_api_key.get_secret_value(),
            model=config.anthropic_model or "claude-sonnet-5",
            timeout_seconds=config.llm_timeout_seconds,
        )

    supported = ", ".join(SUPPORTED_PROVIDERS)
    raise ProviderConfigurationError(
        f"Unknown provider '{selected}'. Supported providers: {supported}."
    )

