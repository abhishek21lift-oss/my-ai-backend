from pydantic import BaseModel, Field
from typing import List, Optional


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    model: str = "claude-opus-4-8"
    max_tokens: int = Field(default=1024, gt=0, le=8096)
    system: Optional[str] = None


class UsageStats(BaseModel):
    input_tokens: int
    output_tokens: int


class ChatResponse(BaseModel):
    content: str
    model: str
    usage: Optional[UsageStats] = None
