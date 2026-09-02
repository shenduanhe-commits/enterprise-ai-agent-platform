from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeDocumentCreate(BaseModel):
    owner_user_id: int
    agent_id: int
    title: str = Field(min_length=1)
    source_uri: str
    status: str
    error: str | None = None


class KnowledgeDocumentResponse(BaseModel):
    id: int
    owner_user_id: int
    agent_id: int
    title: str
    source_uri: str
    status: str
    error: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
