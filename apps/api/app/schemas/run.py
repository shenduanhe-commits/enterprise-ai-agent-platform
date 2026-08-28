from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ToolDecision(BaseModel):
    id: str
    approved: bool


class ResumeRequest(BaseModel):
    decisions: list[ToolDecision] = Field(min_length=1)


class RunResponse(BaseModel):
    run_id: str
    status: str
    pending: dict | None = None

    model_config = ConfigDict(from_attributes=True)


class RunSpanResponse(BaseModel):
    """一次图节点执行。不存完整 prompt / messages。"""

    id: int
    conversation_id: int
    node: str
    started_at: datetime
    duration_ms: int
    tool_name: str | None = None
    status: str
    error: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RunSpanCreate(BaseModel):
    conversation_id: int
    node: str
    started_at: datetime
    duration_ms: int
    tool_name: str | None = None
    status: str
    error: str | None = None
