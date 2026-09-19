import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ProviderName = Literal["ollama", "anthropic"]
ChatMode = Literal["answer", "ship30", "markdown", "html"]


class SessionCreate(BaseModel):
    title: str = Field(default="New chat", min_length=1, max_length=200)
    user_metadata: dict = Field(default_factory=dict)


class ArtifactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    message_id: uuid.UUID
    artifact_type: Literal["markdown", "html"]
    title: str
    content: str
    created_at: datetime


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    role: Literal["user", "assistant"]
    content: str
    provider: str | None
    mode: str | None
    sources: list[dict]
    created_at: datetime
    artifacts: list[ArtifactRead] = Field(default_factory=list)


class SessionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    user_metadata: dict
    created_at: datetime
    updated_at: datetime


class SessionRead(SessionSummary):
    messages: list[MessageRead] = Field(default_factory=list)


class ChatRequest(BaseModel):
    session_id: uuid.UUID
    message: str = Field(min_length=1, max_length=10000)
    provider: ProviderName = "ollama"
    mode: ChatMode = "answer"


class ChatResponse(BaseModel):
    session_id: uuid.UUID
    message: MessageRead
    provider: ProviderName
    model: str
    artifact: ArtifactRead | None = None


class ComponentHealth(BaseModel):
    status: Literal["healthy", "unavailable", "degraded"]
    detail: str | None = None


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded"]
    api: ComponentHealth
    database: ComponentHealth
    ollama: ComponentHealth
    vector_store: ComponentHealth

