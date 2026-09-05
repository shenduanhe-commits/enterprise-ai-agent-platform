from pydantic import BaseModel, Field


class A2AMessage(BaseModel):
    """Minimal A2A-shaped envelope. Not the full Google A2A card/task spec."""

    protocol: str = "eaap-a2a/v0"
    from_agent: str
    to_agent: str
    task_id: str
    content: str
    metadata: dict = Field(default_factory=dict)


class A2AReply(BaseModel):
    protocol: str = "eaap-a2a/v0"
    from_agent: str
    task_id: str
    content: str
    status: str = "completed"
