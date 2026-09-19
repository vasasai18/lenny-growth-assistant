import json
from collections.abc import AsyncIterator, Sequence

import httpx

from app.providers.base import (
    BaseLLMProvider,
    ChatMessage,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)


class OllamaProvider(BaseLLMProvider):
    name = "ollama"

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_seconds: float = 120.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._client = client

    async def stream(
        self,
        messages: Sequence[ChatMessage],
        system_prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        client = self._client or httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_seconds, connect=5.0)
        )
        owns_client = self._client is None
        received_text = False
        try:
            payload_messages = [
                {"role": "system", "content": system_prompt},
                *[
                    {"role": message.role, "content": message.content}
                    for message in messages
                ],
            ]
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": payload_messages,
                    "stream": True,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ProviderResponseError(
                            "Ollama returned malformed streaming JSON."
                        ) from exc
                    if event.get("error"):
                        raise ProviderResponseError(f"Ollama error: {event['error']}")
                    content = event.get("message", {}).get("content", "")
                    if content:
                        received_text = True
                        yield content
                    if event.get("done"):
                        break
            if not received_text:
                raise ProviderResponseError("Ollama returned an empty response.")
        except httpx.ConnectError as exc:
            raise ProviderUnavailableError(
                f"Ollama is not reachable at {self.base_url}. Start Ollama and retry."
            ) from exc
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                f"Ollama did not respond within {self.timeout_seconds} seconds."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise ProviderUnavailableError(
                f"Ollama returned HTTP {exc.response.status_code}."
            ) from exc
        finally:
            if owns_client:
                await client.aclose()

