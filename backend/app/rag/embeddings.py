import asyncio
from collections.abc import Sequence
from typing import Protocol

import httpx


class EmbeddingError(RuntimeError):
    """Raised when the configured embedding service cannot return valid vectors."""


class EmbeddingClient(Protocol):
    async def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class OllamaEmbeddingClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        expected_dimension: int,
        timeout_seconds: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.expected_dimension = expected_dimension
        self.timeout_seconds = timeout_seconds

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/api/embed",
                    json={"model": self.model, "input": list(texts)},
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise EmbeddingError(
                f"Ollama embedding request failed at {self.base_url}: {exc}"
            ) from exc

        payload = response.json()
        embeddings = payload.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise EmbeddingError("Ollama returned an unexpected number of embeddings.")

        for position, embedding in enumerate(embeddings):
            if not isinstance(embedding, list) or len(embedding) != self.expected_dimension:
                actual = len(embedding) if isinstance(embedding, list) else "invalid"
                raise EmbeddingError(
                    f"Embedding {position} has dimension {actual}; "
                    f"expected {self.expected_dimension}."
                )
        return embeddings


class FastEmbedClient:
    """Small CPU embedding runtime used by memory-constrained public hosting."""

    def __init__(
        self, model: str, expected_dimension: int, cache_dir: str | None = None
    ) -> None:
        from fastembed import TextEmbedding

        self.model_name = model
        self.expected_dimension = expected_dimension
        self._model = TextEmbedding(model_name=model, cache_dir=cache_dir)

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        def run() -> list[list[float]]:
            return [vector.tolist() for vector in self._model.embed(list(texts))]

        embeddings = await asyncio.to_thread(run)
        for position, embedding in enumerate(embeddings):
            if len(embedding) != self.expected_dimension:
                raise EmbeddingError(
                    f"Embedding {position} has dimension {len(embedding)}; "
                    f"expected {self.expected_dimension}."
                )
        return embeddings


def create_embedding_client(settings):  # type: ignore[no-untyped-def]
    if settings.embedding_provider == "fastembed":
        return FastEmbedClient(
            settings.fastembed_model,
            settings.embedding_dimension,
            settings.fastembed_cache_dir,
        )
    if settings.embedding_provider == "ollama":
        return OllamaEmbeddingClient(
            settings.ollama_base_url,
            settings.ollama_embedding_model,
            settings.embedding_dimension,
            settings.llm_timeout_seconds,
        )
    raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")
