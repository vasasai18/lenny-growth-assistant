import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import TranscriptChunk
from app.rag.embeddings import OllamaEmbeddingClient


INSUFFICIENT_INFORMATION_MESSAGE = (
    "I do not have sufficient information in Lenny's Podcast archive to answer this."
)


@dataclass(frozen=True)
class RetrievedChunk:
    id: uuid.UUID
    episode_title: str
    guest_name: str | None
    publication_date: date | None
    timestamp_ref: str | None
    source_url: str
    chunk_text: str
    similarity: float

    def citation(self, citation_number: int) -> dict[str, object]:
        return {
            "citation_number": citation_number,
            "chunk_id": str(self.id),
            "episode_title": self.episode_title,
            "guest_name": self.guest_name,
            "publication_date": (
                self.publication_date.isoformat() if self.publication_date else None
            ),
            "timestamp_ref": self.timestamp_ref,
            "source_url": self.source_url,
            "similarity": round(self.similarity, 4),
        }


def filter_by_relevance(
    candidates: list[RetrievedChunk], threshold: float
) -> list[RetrievedChunk]:
    """Keep only evidence whose cosine similarity reaches the configured threshold."""

    return [candidate for candidate in candidates if candidate.similarity >= threshold]


class TranscriptRetriever:
    def __init__(
        self,
        embedding_client: OllamaEmbeddingClient,
        score_threshold: float = 0.52,
        default_top_k: int = 5,
    ) -> None:
        if not 0.0 <= score_threshold <= 1.0:
            raise ValueError("Retrieval score threshold must be between 0 and 1.")
        if not 1 <= default_top_k <= 20:
            raise ValueError("Default top_k must be between 1 and 20.")
        self.embedding_client = embedding_client
        self.score_threshold = score_threshold
        self.default_top_k = default_top_k

    async def search(
        self,
        session: AsyncSession,
        query: str,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        clean_query = query.strip()
        if not clean_query:
            raise ValueError("Retrieval query cannot be empty.")

        result_limit = top_k or self.default_top_k
        if not 1 <= result_limit <= 20:
            raise ValueError("top_k must be between 1 and 20.")

        query_embedding = (await self.embedding_client.embed([clean_query]))[0]
        distance = TranscriptChunk.embedding.cosine_distance(query_embedding)
        statement = (
            select(TranscriptChunk, distance.label("distance"))
            .order_by(distance)
            .limit(result_limit)
        )
        rows = (await session.execute(statement)).all()

        candidates = [
            RetrievedChunk(
                id=chunk.id,
                episode_title=chunk.episode_title,
                guest_name=chunk.guest_name,
                publication_date=chunk.publication_date,
                timestamp_ref=chunk.timestamp_ref,
                source_url=chunk.source_url,
                chunk_text=chunk.chunk_text,
                similarity=max(0.0, min(1.0, 1.0 - float(row_distance))),
            )
            for chunk, row_distance in rows
        ]
        return filter_by_relevance(candidates, self.score_threshold)


def build_grounded_context(chunks: list[RetrievedChunk]) -> str:
    """Format evidence as quoted data, never as agent instructions."""

    sections: list[str] = []
    for position, chunk in enumerate(chunks, start=1):
        label = f"SOURCE {position}"
        metadata = (
            f"Episode: {chunk.episode_title}\n"
            f"Guest: {chunk.guest_name or 'Unknown'}\n"
            f"Timestamp: {chunk.timestamp_ref or 'Not available'}\n"
            f"URL: {chunk.source_url}\n"
            f"Chunk ID: {chunk.id}"
        )
        sections.append(
            f"<{label}>\n{metadata}\n<TRANSCRIPT_QUOTE>\n"
            f"{chunk.chunk_text}\n</TRANSCRIPT_QUOTE>\n</{label}>"
        )
    return "\n\n".join(sections)
