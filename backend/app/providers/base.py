from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ChatMessage:
    role: Literal["user", "assistant"]
    content: str


class ProviderError(RuntimeError):
    code = "PROVIDER_ERROR"


class ProviderConfigurationError(ProviderError):
    code = "PROVIDER_NOT_CONFIGURED"


class ProviderUnavailableError(ProviderError):
    code = "PROVIDER_UNAVAILABLE"


class ProviderTimeoutError(ProviderError):
    code = "PROVIDER_TIMEOUT"


class ProviderResponseError(ProviderError):
    code = "PROVIDER_BAD_RESPONSE"


class BaseLLMProvider(ABC):
    name: str
    model: str

    @abstractmethod
    def stream(
        self,
        messages: Sequence[ChatMessage],
        system_prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """Stream text tokens from the selected provider."""

    async def generate(
        self,
        messages: Sequence[ChatMessage],
        system_prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        parts = [
            part
            async for part in self.stream(
                messages,
                system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        ]
        result = "".join(parts).strip()
        if not result:
            raise ProviderResponseError(f"{self.name} returned an empty response.")
        return result

