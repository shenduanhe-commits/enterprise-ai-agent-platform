from pydantic import BaseModel, ConfigDict, Field


class ToolResponse(BaseModel):
    id: int
    name: str
    description: str
    # ORM 列仍叫 schema；字段避开 BaseModel.schema()
    input_schema: dict = Field(validation_alias="schema")
    source: str
    mcp_url: str | None
    requires_hitl: bool
    enabled: bool

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AgentToolsUpdate(BaseModel):
    tool_ids: list[int] = Field(default_factory=list)
