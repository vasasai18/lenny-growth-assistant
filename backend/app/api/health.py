import httpx
from fastapi import APIRouter
from sqlalchemy import text

from app.config import get_settings
from app.database import engine
from app.models.schemas import ComponentHealth, HealthResponse


router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    database = ComponentHealth(status="unavailable", detail="Not checked")
    vector_store = ComponentHealth(status="unavailable", detail="Not checked")
    ollama = ComponentHealth(status="unavailable", detail="Not checked")

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            database = ComponentHealth(status="healthy")
            vector_version = (
                await connection.execute(
                    text("SELECT extversion FROM pg_extension WHERE extname='vector'")
                )
            ).scalar_one_or_none()
            chunk_count = (
                await connection.execute(text("SELECT count(*) FROM transcript_chunks"))
            ).scalar_one()
            if vector_version:
                vector_store = ComponentHealth(
                    status="healthy",
                    detail=f"pgvector {vector_version}; {chunk_count} chunks",
                )
            else:
                vector_store = ComponentHealth(
                    status="unavailable", detail="pgvector extension is missing"
                )
    except Exception as exc:
        database = ComponentHealth(status="unavailable", detail=type(exc).__name__)
        vector_store = ComponentHealth(status="unavailable", detail="Database unavailable")

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags")
            response.raise_for_status()
            model_names = [model["name"] for model in response.json().get("models", [])]
            ollama = ComponentHealth(
                status="healthy", detail=f"{len(model_names)} models available"
            )
    except Exception as exc:
        ollama = ComponentHealth(status="unavailable", detail=type(exc).__name__)

    overall = (
        "healthy"
        if all(
            component.status == "healthy"
            for component in (database, vector_store, ollama)
        )
        else "degraded"
    )
    return HealthResponse(
        status=overall,
        api=ComponentHealth(status="healthy"),
        database=database,
        ollama=ollama,
        vector_store=vector_store,
    )

