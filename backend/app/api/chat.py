import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.service import AgentService, get_agent_service
from app.database import get_db_session
from app.models.db_models import Artifact, ArtifactType, Message, MessageRole, Session
from app.models.schemas import ArtifactRead, ChatRequest, ChatResponse, MessageRead
from app.providers import ChatMessage
from app.skills.artifact_generator import prepare_artifact


router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db_session),
    agent_service: AgentService = Depends(get_agent_service),
) -> ChatResponse:
    chat_session = await db.get(Session, payload.session_id)
    if chat_session is None:
        raise HTTPException(status_code=404, detail="Chat session not found.")

    history_rows = (
        await db.execute(
            select(Message)
            .where(Message.session_id == payload.session_id)
            .order_by(Message.created_at.asc())
            .limit(20)
        )
    ).scalars().all()
    history = [
        ChatMessage(role=row.role.value, content=row.content) for row in history_rows
    ]

    user_message = Message(
        session_id=payload.session_id,
        role=MessageRole.USER,
        content=payload.message,
        provider=payload.provider,
        mode=payload.mode,
    )
    db.add(user_message)
    if chat_session.title == "New chat":
        chat_session.title = payload.message.strip()[:80]
    await db.commit()

    logger.info(
        "chat_generation_started",
        extra={
            "session_id": str(payload.session_id),
            "provider": payload.provider,
            "mode": payload.mode,
        },
    )
    result = await agent_service.run(
        payload.provider,
        payload.message,
        payload.mode,
        history,
    )
    final_content = result.content
    if payload.mode in {"markdown", "html"}:
        final_content = prepare_artifact(payload.mode, final_content).content

    assistant_message = Message(
        session_id=payload.session_id,
        role=MessageRole.ASSISTANT,
        content=final_content,
        provider=result.provider,
        mode=payload.mode,
        sources=result.sources,
    )
    db.add(assistant_message)
    await db.flush()

    artifact = None
    if payload.mode in {"markdown", "html"}:
        artifact = Artifact(
            message_id=assistant_message.id,
            artifact_type=(
                ArtifactType.MARKDOWN if payload.mode == "markdown" else ArtifactType.HTML
            ),
            title=chat_session.title,
            content=result.content,
        )
        db.add(artifact)
        await db.flush()

    await db.commit()
    await db.refresh(assistant_message, attribute_names=["artifacts"])
    if artifact is not None:
        await db.refresh(artifact)

    logger.info(
        "chat_generation_completed",
        extra={
            "session_id": str(payload.session_id),
            "provider": result.provider,
            "mode": payload.mode,
        },
    )
    return ChatResponse(
        session_id=payload.session_id,
        message=MessageRead.model_validate(assistant_message),
        provider=payload.provider,
        model=result.model,
        artifact=ArtifactRead.model_validate(artifact) if artifact else None,
    )
