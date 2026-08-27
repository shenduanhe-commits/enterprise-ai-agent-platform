import json
import re

from app.ai.llm.providers.base import BaseLLMProvider
from app.ai.type import AIMessage


class MockLLMProvider(BaseLLMProvider):
    """
    本地假模型：不打真实 API，用来测 Agent 工具循环。
    签名必须和 BaseLLMProvider.chat(model, messages, tools) 一致，
    否则 Gateway 一调用就会 TypeError。
    """

    async def chat(
        self,
        model: str,
        messages: list[AIMessage],
        tools: list[dict] | None = None,
        response_format: dict | None = None,
    ) -> AIMessage:
        last_message = messages[-1]
        _ = response_format

        # 上一轮已经执行过工具：Executor 会把 tool 结果追加进 messages。
        # 这时不能再返回 tool_calls，否则 run_loop 会一直转，直到超轮次。
        if last_message.role == "tool":
            content = last_message.content or ""
            if "已发送" in content or content == "user denied":
                return self._final(content)
            return self._final(f"计算结果是 {content}")

        if self._should_call_send_email(last_message, tools):
            return AIMessage(
                role="assistant",
                content=None,
                tool_calls=[
                    {
                        "id": "call_send_email_1",
                        "function": {
                            "name": "send_email",
                            "arguments": json.dumps(
                                {
                                    "to": "ops@eaap.com",
                                    "subject": last_message.content or "",
                                    "body": last_message.content or "",
                                },
                                ensure_ascii=False,
                            ),
                        },
                    }
                ],
            )

        # 用户提问 + 当前 Agent 挂了 calculator + 话里像算式
        # → 假装模型决定调工具。形状必须和 Qwen 解析出来的 tool_calls 一样，
        # execute_tools 才能用 function.name / function.arguments。
        if self._should_call_calculator(last_message, tools):
            expression = self._extract_expression(last_message.content or "")
            return AIMessage(
                role="assistant",
                content=None,
                tool_calls=[
                    {
                        "id": "call_calculator_1",
                        "function": {
                            "name": "calculator",
                            "arguments": json.dumps({"expression": expression}),
                        },
                    }
                ],
            )

        # 普通闲聊：只回 JSON 最终答案，run_loop 看到没有 tool_calls 就会结束。
        return self._final(f"Mock AI Response: received '{last_message.content}'")

    def _final(self, answer: str) -> AIMessage:
        return AIMessage(
            role="assistant",
            content=json.dumps({"answer": answer}, ensure_ascii=False),
        )

    def _should_call_send_email(
        self,
        last_message: AIMessage,
        tools: list[dict] | None,
    ) -> bool:
        if last_message.role != "user" or not tools:
            return False
        names = [
            tool.get("function", tool).get("name")
            for tool in tools
            if isinstance(tool, dict)
        ]
        if "send_email" not in names:
            return False
        text = (last_message.content or "").lower()
        return "邮件" in text or "email" in text or "发信" in text

    def _should_call_calculator(
        self,
        last_message: AIMessage,
        tools: list[dict] | None,
    ) -> bool:
        # 只有「用户刚说的话」才考虑调工具；tool / assistant 消息不该再触发。
        if last_message.role != "user" or not tools:
            return False

        # tools 是 OpenAI function schema：{"type":"function","function":{"name":...}}
        names = [
            tool.get("function", tool).get("name")
            for tool in tools
            if isinstance(tool, dict)
        ]
        if "calculator" not in names:
            return False

        # 最小启发式：话里有数字才当成计算题，避免「你好」也去调计算器。
        return bool(re.search(r"\d", last_message.content or ""))

    def _extract_expression(self, content: str) -> str:
        # 从「12*7+5 等于多少」里抽出算式；抽不到就整句交给 calculator（可能算失败）。
        match = re.search(r"[\d+\-*/().]+(?:\s*[\d+\-*/().]+)*", content)
        if not match:
            return content.strip()
        return re.sub(r"\s+", "", match.group(0))
