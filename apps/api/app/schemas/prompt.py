from datetime import datetime

from pydantic import BaseModel


class PromptCreate(BaseModel):
    agent_id: int

    name: str

    template: str


class PromptResponse(BaseModel):
    id: int

    agent_id: int

    name: str

    template: str

    version: int

    created_at: datetime

    model_config = {"from_attributes": True}
