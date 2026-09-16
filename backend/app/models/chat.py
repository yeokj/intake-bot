from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"] = Field(
        ..., description="Role of the message sender"
    )
    content: str = Field(..., description="Message text content")


class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(
        default="default-session", description="Session or prospect identifier"
    )
    messages: List[ChatMessage] = Field(
        ..., description="List of previous conversation messages"
    )


class ChatResponse(BaseModel):
    session_id: str
    message: ChatMessage
    is_ready_for_brief: bool = Field(
        default=False,
        description="Flag set when all essential scoping info has been gathered",
    )