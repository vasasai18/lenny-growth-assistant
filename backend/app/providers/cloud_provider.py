from collections.abc import AsyncIterator, Sequence
from typing import Any

import anthropic

from app.providers.base import (
    BaseLLMProvider,
    ChatMessage,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)


class AnthropicProvider(BaseLLMProvider):
    name = "anthropic"

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: float = 120.0,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._client = client or anthropic.AsyncAnthropic(
            api_key=api_key,
            timeout=timeout_seconds,
        )

    async def stream(
        self,
        messages: Sequence[ChatMessage],
        system_prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        received_text = False
        try:
            async with self._client.messages.stream(
                model=self.model,
                system=system_prompt,
                messages=[
                    {"role": message.role, "content": message.content}
                    for message in messages
                ],
                max_tokens=max_tokens,
            ) as stream:
                async for text in stream.text_stream:
                    if text:
                        received_text = True
                        yield text
            if not received_text:
                raise ProviderResponseError("Anthropic returned an empty response.")
        except ProviderResponseError:
            raise
        except anthropic.APITimeoutError as exc:
            raise ProviderTimeoutError(
                f"Anthropic did not respond within {self.timeout_seconds} seconds."
            ) from exc
        except (anthropic.APIConnectionError, anthropic.APIStatusError) as exc:
            raise ProviderUnavailableError(
                "Anthropic is unavailable or rejected the request."
            ) from exc
