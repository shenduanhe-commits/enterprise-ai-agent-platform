from app.schemas.agent import AgentCreate

agent = AgentCreate(
    name="合同助手", model_name="gpt-5", system_prompt="你是合同专家", created_by=1
)


print(agent)
