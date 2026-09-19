import asyncio
import json

import httpx
import pytest

from app.config import Settings
from app.providers.base import (
    ChatMessage,
    ProviderConfigurationError,
    ProviderResponseError,
    ProviderUnavailableError,
)
from app.providers.cloud_provider import AnthropicProvider
from app.providers.ollama_provider import OllamaProvider
from app.providers.provider_factory import create_provider


def run(coroutine):  # type: ignore[no-untyped-def]
    return asyncio.run(coroutine)


def make_ollama_client(lines: list[dict], status_code: int = 200) -> httpx.AsyncClient:
    body = "\n".join(json.dumps(line) for line in lines)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        return httpx.Response(status_code, text=body)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def test_ollama_provider_combines_streamed_text() -> None:
    async def scenario() -> str:
        client = make_ollama_client(
            [
                {"message": {"content": "Grounded "}, "done": False},
                {"message": {"content": "answer."}, "done": False},
                {"done": True},
            ]
        )
        try:
            provider = OllamaProvider("http://ollama.test", "llama3.2:3b", client=client)
            return await provider.generate(
                [ChatMessage(role="user", content="Question")], "Use sources only."
            )
        finally:
            await client.aclose()

    assert run(scenario()) == "Grounded answer."


def test_ollama_provider_rejects_malformed_stream() -> None:
    async def scenario() -> None:
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, text="not-json")
            )
        )
        try:
            provider = OllamaProvider("http://ollama.test", "llama3.2:3b", client=client)
            await provider.generate(
                [ChatMessage(role="user", content="Question")], "System"
            )
        finally:
            await client.aclose()

    with pytest.raises(ProviderResponseError, match="malformed"):
        run(scenario())


def test_ollama_provider_maps_http_failure() -> None:
    async def scenario() -> None:
        client = make_ollama_client([], status_code=503)
        try:
            provider = OllamaProvider("http://ollama.test", "llama3.2:3b", client=client)
            await provider.generate(
                [ChatMessage(role="user", content="Question")], "System"
            )
        finally:
            await client.aclose()

    with pytest.raises(ProviderUnavailableError, match="HTTP 503"):
        run(scenario())


class FakeTextStream:
    def __init__(self, parts: list[str]) -> None:
        self.parts = parts

    def __aiter__(self):  # type: ignore[no-untyped-def]
        self.iterator = iter(self.parts)
        return self

    async def __anext__(self) -> str:
        try:
            return next(self.iterator)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class FakeAnthropicStream:
    def __init__(self, parts: list[str]) -> None:
        self.text_stream = FakeTextStream(parts)

    async def __aenter__(self):  # type: ignore[no-untyped-def]
        return self

    async def __aexit__(self, *args):  # type: ignore[no-untyped-def]
        return False


class FakeMessages:
    def __init__(self, parts: list[str]) -> None:
        self.parts = parts
        self.last_request = None

    def stream(self, **kwargs):  # type: ignore[no-untyped-def]
        self.last_request = kwargs
        return FakeAnthropicStream(self.parts)


class FakeAnthropicClient:
    def __init__(self, parts: list[str]) -> None:
        self.messages = FakeMessages(parts)


def test_anthropic_provider_uses_same_interface() -> None:
    fake_client = FakeAnthropicClient(["Cloud ", "answer."])
    provider = AnthropicProvider(
        api_key="test-key",
        model="claude-sonnet-5",
        client=fake_client,
    )

    result = run(
        provider.generate(
            [ChatMessage(role="user", content="Question")],
            "Use transcript evidence.",
        )
    )

    assert result == "Cloud answer."
    assert fake_client.messages.last_request["model"] == "claude-sonnet-5"
    assert fake_client.messages.last_request["system"] == "Use transcript evidence."


def test_factory_switches_provider_at_runtime() -> None:
    settings = Settings(
        _env_file=None,
        anthropic_api_key="test-key",
        anthropic_model="claude-sonnet-5",
    )

    assert create_provider("ollama", settings).name == "ollama"
    assert create_provider("anthropic", settings).name == "anthropic"


def test_factory_rejects_missing_cloud_key() -> None:
    settings = Settings(_env_file=None, anthropic_api_key=None)

    with pytest.raises(ProviderConfigurationError, match="ANTHROPIC_API_KEY"):
        create_provider("anthropic", settings)


def test_factory_rejects_unknown_provider() -> None:
    settings = Settings(_env_file=None)

    with pytest.raises(ProviderConfigurationError, match="Unknown provider"):
        create_provider("mystery", settings)

