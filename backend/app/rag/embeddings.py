from collections.abc import Sequence

import httpx


class EmbeddingError(RuntimeError):
    """Raised when the configured embedding service cannot return valid vectors."""


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

