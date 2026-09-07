import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base
class ChatSession(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(160), default="New conversation")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    sources: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
class Artifact(Base):
    __tablename__ = "artifacts"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id: Mapped[str] = mapped_column(ForeignKey("messages.id"))
    artifact_type: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
