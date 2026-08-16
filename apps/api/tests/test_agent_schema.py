from app.schemas.agent import AgentCreate


def test_agent_create_does_not_accept_created_by():
    agent = AgentCreate(
        name="合同助手",
        provider="mock",
        model_name="mock-model",
        system_prompt="你是合同专家",
    )
    assert agent.provider == "mock"
    assert not hasattr(agent, "created_by") or "created_by" not in agent.model_fields
