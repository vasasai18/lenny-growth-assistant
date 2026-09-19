import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models.db_models import Artifact
from app.models.schemas import ArtifactRead


router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


@router.get("/{artifact_id}", response_model=ArtifactRead)
async def get_artifact(
    artifact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> Artifact:
    artifact = await db.get(Artifact, artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found.")
    return artifact

