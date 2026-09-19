import argparse
import asyncio
from pathlib import Path

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.dialects.postgresql import insert

from app.config import get_settings
from app.database import AsyncSessionFactory, close_database, create_database_schema
from app.models.db_models import TranscriptChunk
from app.rag.embeddings import OllamaEmbeddingClient
from app.rag.ingestion import chunk_all, load_transcripts, source_revision


SOURCE_PREFIX = "github:LennysNewsletter/lennys-newsletterpodcastdata@"


async def ingest(limit: int | None = None) -> None:
    settings = get_settings()
    dataset_dir = Path(settings.transcript_data_dir)
    transcripts = load_transcripts(dataset_dir)
    if limit is not None:
        transcripts = transcripts[:limit]

    prepared_chunks = chunk_all(
        transcripts,
        target_tokens=settings.chunk_target_tokens,
        overlap_tokens=settings.chunk_overlap_tokens,
    )
    chunks_by_hash = {chunk.content_hash: chunk for chunk in prepared_chunks}
    chunks = list(chunks_by_hash.values())
    revision = SOURCE_PREFIX + source_revision(dataset_dir)
    all_hashes = {chunk.content_hash for chunk in chunks}

    print(f"Parsed transcripts: {len(transcripts)}")
    print(f"Prepared chunks: {len(prepared_chunks)}")
    print(f"Duplicate chunks skipped: {len(prepared_chunks) - len(chunks)}")
    print(f"Unique chunks: {len(chunks)}")
    print(f"Source revision: {revision}")

    await create_database_schema()
    async with AsyncSessionFactory() as session:
        existing_hashes = set(
            (
                await session.execute(
                    select(TranscriptChunk.content_hash).where(
                        TranscriptChunk.content_hash.in_(all_hashes)
                    )
                )
            ).scalars()
        )

    new_chunks = [chunk for chunk in chunks if chunk.content_hash not in existing_hashes]
    print(f"Unchanged chunks: {len(existing_hashes)}")
    print(f"New chunks to embed: {len(new_chunks)}")

    embedder = OllamaEmbeddingClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_embedding_model,
        expected_dimension=settings.embedding_dimension,
    )

    inserted = 0
    async with AsyncSessionFactory() as session:
        for offset in range(0, len(new_chunks), settings.embedding_batch_size):
            batch = new_chunks[offset : offset + settings.embedding_batch_size]
            embeddings = await embedder.embed([chunk.chunk_text for chunk in batch])
            values = [
                {
                    "episode_title": chunk.episode_title,
                    "guest_name": chunk.guest_name,
                    "publication_date": chunk.publication_date,
                    "timestamp_ref": chunk.timestamp_ref,
                    "source_url": chunk.source_url,
                    "source_revision": revision,
                    "chunk_index": chunk.chunk_index,
                    "chunk_text": chunk.chunk_text,
                    "content_hash": chunk.content_hash,
                    "embedding_model": settings.ollama_embedding_model,
                    "embedding": embedding,
                }
                for chunk, embedding in zip(batch, embeddings, strict=True)
            ]
            statement = insert(TranscriptChunk).values(values)
            await session.execute(
                statement.on_conflict_do_nothing(index_elements=["content_hash"])
            )
            await session.commit()
            inserted += len(batch)
            print(f"Embedded and stored: {inserted}/{len(new_chunks)}")

        await session.execute(
            update(TranscriptChunk)
            .where(TranscriptChunk.content_hash.in_(all_hashes))
            .values(source_revision=revision)
        )

        if limit is None:
            await session.execute(
                delete(TranscriptChunk).where(
                    TranscriptChunk.source_revision.like(f"{SOURCE_PREFIX}%"),
                    TranscriptChunk.content_hash.not_in(all_hashes),
                )
            )
        await session.commit()

        total = (
            await session.execute(select(func.count()).select_from(TranscriptChunk))
        ).scalar_one()
        episodes = (
            await session.execute(
                select(func.count(func.distinct(TranscriptChunk.episode_title)))
            )
        ).scalar_one()

        await session.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_transcript_chunks_embedding_hnsw "
                "ON transcript_chunks USING hnsw (embedding vector_cosine_ops)"
            )
        )
        await session.commit()

    print(f"Database transcript chunks: {total}")
    print(f"Database episodes: {episodes}")
    print("HNSW cosine index: ready")
    print("Ingestion: PASS")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest podcast transcripts into pgvector.")
    parser.add_argument(
        "--limit",
        type=int,
        help="Ingest only the first N transcripts for a quick development check.",
    )
    args = parser.parse_args()
    async def run() -> None:
        try:
            await ingest(args.limit)
        finally:
            await close_database()

    asyncio.run(run())


if __name__ == "__main__":
    main()
