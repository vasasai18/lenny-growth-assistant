from pydantic import BaseModel, Field
from typing import Literal
class CreateSession(BaseModel): title: str = Field(default="New conversation", max_length=160)
class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1, max_length=4000)
    provider: Literal["ollama", "openai"] | None = None
    mode: Literal["answer", "ship30", "artifact"] = "answer"
class Source(BaseModel): title: str; guest: str = ""; timestamp: str = ""; url: str = ""
