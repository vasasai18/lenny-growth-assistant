import asyncio

from sqlalchemy import func, select, text

from app.database import AsyncSessionFactory, close_database, create_database_schema, engine
from app.models.db_models import (
    Artifact,
    ArtifactType,
    Message,
    MessageRole,
    Session,
    TranscriptChunk,
)


async def main() -> None:
    await create_database_schema()

    async with engine.connect() as connection:
        postgres_version = (await connection.execute(text("SELECT version()"))).scalar_one()
        vector_version = (
            await connection.execute(
                text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            )
        ).scalar_one()
        tables = (
            await connection.execute(
                text(
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname = 'public' ORDER BY tablename"
                )
            )
        ).scalars().all()
        distance = (
            await connection.execute(
                text("SELECT '[1,0,0]'::vector <=> '[0,1,0]'::vector")
            )
        ).scalar_one()

    print(f"PostgreSQL: {postgres_version.split(',')[0]}")
    print(f"pgvector: {vector_version}")
    print(f"Tables: {', '.join(tables)}")
    print(f"Vector cosine distance check: {distance}")

    async with AsyncSessionFactory() as session:
        async with session.begin():
            test_session = Session(title="Database verification")
            test_message = Message(
                session=test_session,
                role=MessageRole.ASSISTANT,
                content="Temporary verification message",
                provider="ollama",
                mode="answer",
            )
            test_artifact = Artifact(
                message=test_message,
                artifact_type=ArtifactType.MARKDOWN,
                title="Temporary artifact",
                content="# Verification",
            )
            test_chunk = TranscriptChunk(
                episode_title="Temporary verification episode",
                source_url="https://example.invalid/verification",
                chunk_index=0,
                chunk_text="Temporary chunk used only during database verification.",
                content_hash="0" * 64,
                embedding_model="verification-only",
                embedding=[0.0] * 768,
            )
            session.add_all([test_session, test_artifact, test_chunk])
            await session.flush()

            counts = {
                model.__tablename__: (
                    await session.execute(select(func.count()).select_from(model))
                ).scalar_one()
                for model in (Session, Message, Artifact, TranscriptChunk)
            }
            print(
                "SQLAlchemy insert/read check: "
                + ", ".join(f"{name}={count}" for name, count in counts.items())
            )

            # This is verification data, so deliberately remove it before commit.
            await session.rollback()

    print("Database verification: PASS")

    await close_database()


if __name__ == "__main__":
    asyncio.run(main())
