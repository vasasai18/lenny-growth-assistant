import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db_session
from app.models.db_models import Message, Session
from app.models.schemas import SessionCreate, SessionRead, SessionSummary


router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionSummary, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    db: AsyncSession = Depends(get_db_session),
) -> Session:
    chat_session = Session(title=payload.title, user_metadata=payload.user_metadata)
    db.add(chat_session)
    await db.commit()
    await db.refresh(chat_session)
    return chat_session


@router.get("", response_model=list[SessionSummary])
async def list_sessions(
    db: AsyncSession = Depends(get_db_session),
) -> list[Session]:
    result = await db.execute(select(Session).order_by(Session.updated_at.desc()).limit(100))
    return list(result.scalars())


@router.get("/{session_id}", response_model=SessionRead)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> Session:
    statement = (
        select(Session)
        .where(Session.id == session_id)
        .options(selectinload(Session.messages).selectinload(Message.artifacts))
    )
    chat_session = (await db.execute(statement)).scalar_one_or_none()
    if chat_session is None:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    return chat_session

