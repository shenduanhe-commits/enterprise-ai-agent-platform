from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AgentCreate(BaseModel):
    name: str

    description: str | None = None

    provider: str

    model_name: str

    system_prompt: str

    created_by: int


class AgentResponse(BaseModel):
    id: int

    name: str

    description: str | None

    provider: str

    model_name: str

    system_prompt: str

    created_by: int

    created_at: datetime

    status: str

    model_config = ConfigDict(from_attributes=True)
