from app.ai.llm.gateway import LLMGateway
from app.ai.structured import parse_final_answer
from app.ai.type import AIMessage

WRITER_SYSTEM = (
    "【Writer】你是专职写作者。根据检索笔记写一页简报。"
    "不要编造笔记里没有的内容。只输出 JSON {\"answer\": \"...\"}。"
)


async def write_brief(
    llm_gateway: LLMGateway,
    *,
    provider: str,
    model: str,
    user_message: str,
    notes: str,
) -> str:
    response = await llm_gateway.chat(
        provider=provider,
        model=model,
        messages=[
            AIMessage(role="system", content=WRITER_SYSTEM),
            AIMessage(
                role="user",
                content=f"用户要求：{user_message}\n\n检索笔记：\n{notes}",
            ),
        ],
        tools=None,
    )
    return parse_final_answer(response.content).answer
