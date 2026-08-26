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
