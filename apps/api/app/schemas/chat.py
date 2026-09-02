from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    conversation_id: int | None = None  # 如果为 None，则创建新对话
    variables: dict | None = None  # 如果为 None，则使用默认变量
    user_message: str
    model_config = ConfigDict(from_attributes=True)


class Citation(BaseModel):
    document_id: int
    title: str
    chunk_id: str


class ChatResponse(BaseModel):
    conversation_id: int
    role: str

    content: str | None = None

    created_at: datetime | None = None

    status: str = "completed"
    pending: dict | None = None
    citations: list[Citation] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
