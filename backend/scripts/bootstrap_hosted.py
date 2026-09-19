"""Seed an empty hosted database before starting the public web service."""

import asyncio
from pathlib import Path

from sqlalchemy import func, select

from app.config import get_settings
from app.database import AsyncSessionFactory, close_database, create_database_schema
from app.models.db_models import TranscriptChunk
from scripts.download_transcripts import download
from scripts.ingest import ingest


async def chunk_count() -> int:
    await create_database_schema()
    async with AsyncSessionFactory() as session:
        return int(
            (
                await session.execute(
                    select(func.count()).select_from(TranscriptChunk)
                )
            ).scalar_one()
        )


async def bootstrap() -> None:
    settings = get_settings()
    try:
        existing = await chunk_count()
        if existing:
            print(f"Hosted bootstrap: {existing} transcript chunks already present; skipping ingestion.")
            return

        print("Hosted bootstrap: vector store is empty; downloading transcripts.")
        dataset_dir = Path(settings.transcript_data_dir)
        download(settings.transcript_repository_url, dataset_dir)
        await ingest()
        print("Hosted bootstrap: PASS")
    finally:
        await close_database()


if __name__ == "__main__":
    asyncio.run(bootstrap())
