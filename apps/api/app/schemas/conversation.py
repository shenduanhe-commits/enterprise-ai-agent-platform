from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConversationCreate(BaseModel):
    user_id: int
    agent_id: int
    name: str


class ConversationResponse(BaseModel):
    id: int
    name: str
    user_id: int
    agent_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
