from types import SimpleNamespace

import pytest

from app.ai.llm.gateway import LLMGateway
from app.ai.llm.providers.base import BaseLLMProvider
from app.ai.llm.providers.mock import MockLLMProvider
from app.ai.runtime.agent_executor import AgentExecutor
from app.ai.runtime.agent_graph import AgentGraph, run_graph, stream_graph
from langgraph.checkpoint.memory import InMemorySaver
from app.ai.tools.builtin.calculator import CalculatorTool
from app.ai.tools.builtin.send_email import SendEmailTool
from app.ai.tools.manager import ToolManager
from app.ai.type import AIMessage
from app.core.exceptions import AgentRuntimeException, BusinessException


def _hitl_tools() -> tuple[ToolManager, SendEmailTool]:
    tools = ToolManager()
    email = SendEmailTool()
    tools.register(CalculatorTool())
    tools.register(email)
    return tools, email


def _tools() -> ToolManager:
    tools = ToolManager()
    tools.register(CalculatorTool())
    return tools


def _agent():
    return SimpleNamespace(provider="mock", model_name="mock-model")


async def _run(provider, user_message: str) -> AIMessage:
    return await run_graph(
        LLMGateway({"mock": provider}),
        _tools(),
        _agent(),
        [AIMessage(role="user", content=user_message)],
    )


class AlwaysToolLLMProvider(BaseLLMProvider):
    async def chat(
        self,
        model: str,
        messages: list[AIMessage],
        tools: list[dict] | None = None,
    ) -> AIMessage:
        return AIMessage(
            role="assistant",
            tool_calls=[
                {
                    "id": "call_loop",
                    "function": {
                        "name": "calculator",
                        "arguments": '{"expression": "1+1"}',
                    },
                }
            ],
        )


class ScriptedLLMProvider(BaseLLMProvider):
    def __init__(self, responses: list[AIMessage]):
        self.responses = list(responses)
        self.index = 0

    async def chat(
        self,
        model: str,
        messages: list[AIMessage],
        tools: list[dict] | None = None,
    ) -> AIMessage:
        response = self.responses[min(self.index, len(self.responses) - 1)]
        self.index += 1
        return response


@pytest.mark.asyncio
async def test_run_graph_returns_text_without_tools():
    result = await _run(MockLLMProvider(), "你好")

    assert "Mock AI Response" in (result.content or "")
    assert not result.tool_calls


@pytest.mark.asyncio
async def test_run_graph_executes_calculator():
    result = await _run(MockLLMProvider(), "12*7+5 等于多少")

    assert result.content == "计算结果是 89"


@pytest.mark.asyncio
async def test_run_graph_unknown_tool_does_not_crash():
    result = await _run(
        ScriptedLLMProvider(
            [
                AIMessage(
                    role="assistant",
                    tool_calls=[
                        {
                            "id": "call_1",
                            "function": {
                                "name": "not_a_real_tool",
                                "arguments": "{}",
                            },
                        }
                    ],
                ),
                AIMessage(role="assistant", content="tool was missing"),
            ]
        ),
        "do something",
    )

    assert result.content == "tool was missing"


@pytest.mark.asyncio
async def test_run_graph_exceeds_max_iterations():
    with pytest.raises(AgentRuntimeException, match="max iterations"):
        await _run(AlwaysToolLLMProvider(), "loop")


@pytest.mark.asyncio
async def test_execute_uses_graph_not_loop():
    executor = AgentExecutor(
        llm_gateway=LLMGateway({"mock": MockLLMProvider()}),
        prompt_manager=None,
        memory_manager=None,
        tool_manager=_tools(),
    )

    async def fake_build(db, agent, conversation, user_message, variables):
        return [AIMessage(role="user", content=user_message)]

    saved: dict = {}

    async def fake_save(db, conversation_id, user_message, assistant_message):
        saved["content"] = assistant_message
        return SimpleNamespace(created_at=None)

    async def loop_should_not_run(*args, **kwargs):
        raise AssertionError("非流式 /chat 不应再走 run_loop")

    executor._build_messages = fake_build
    executor.memory_manager = SimpleNamespace(create_message=fake_save)
    executor.run_loop = loop_should_not_run

    result = await executor.execute(
        db=None,
        agent=_agent(),
        conversation=SimpleNamespace(id=1),
        user_message="12*7+5 等于多少",
    )

    assert result.content == "计算结果是 89"
    assert saved["content"] == "计算结果是 89"


async def _collect_graph_stream(user_message: str):
    events: list[tuple[str, dict]] = []
    async for event in stream_graph(
        LLMGateway({"mock": MockLLMProvider()}),
        _tools(),
        _agent(),
        [AIMessage(role="user", content=user_message)],
    ):
        events.append(event)
    return events


@pytest.mark.asyncio
async def test_stream_graph_chunks_plain_text():
    events = await _collect_graph_stream("你好")
    tokens = [data["text"] for event, data in events if event == "token"]

    assert all(event == "token" for event, _ in events)
    assert len(tokens) > 1
    assert "Mock AI Response" in "".join(tokens)


@pytest.mark.asyncio
async def test_stream_graph_emits_tool_then_tokens():
    events = await _collect_graph_stream("12*7+5 等于多少")
    kinds = [event for event, _ in events]

    assert kinds[:2] == ["tool", "tool"]
    assert events[0][1] == {
        "id": "call_calculator_1",
        "name": "calculator",
        "status": "start",
    }
    assert events[1][1]["status"] == "result"
    assert events[1][1]["content"] == "89"
    assert "".join(data["text"] for event, data in events if event == "token") == (
        "计算结果是 89"
    )


@pytest.mark.asyncio
async def test_execute_stream_uses_graph_not_loop():
    executor = AgentExecutor(
        llm_gateway=LLMGateway({"mock": MockLLMProvider()}),
        prompt_manager=None,
        memory_manager=None,
        tool_manager=_tools(),
    )

    async def fake_build(db, agent, conversation, user_message, variables):
        return [AIMessage(role="user", content=user_message)]

    saved: dict = {}

    async def fake_save(db, conversation_id, user_message, assistant_message):
        saved["content"] = assistant_message
        return SimpleNamespace(created_at=None)

    async def loop_should_not_run(*args, **kwargs):
        raise AssertionError("SSE /chat/stream 不应再走 stream_loop")
        yield

    executor._build_messages = fake_build
    executor.memory_manager = SimpleNamespace(create_message=fake_save)
    executor.stream_loop = loop_should_not_run

    events: list[tuple[str, dict]] = []
    async for event in executor.execute_stream(
        db=None,
        agent=_agent(),
        conversation=SimpleNamespace(id=1),
        user_message="你好",
    ):
        events.append(event)

    assert events[-1] == ("done", {"conversation_id": 1, "status": "completed"})
    assert "Mock AI Response" in saved["content"]


class RecordingLLMProvider(BaseLLMProvider):
    def __init__(self):
        self.seen: list[list[str | None]] = []

    async def chat(
        self,
        model: str,
        messages: list[AIMessage],
        tools: list[dict] | None = None,
    ) -> AIMessage:
        self.seen.append([message.content for message in messages])
        last = messages[-1].content or ""
        return AIMessage(role="assistant", content=f"ack:{last}")


@pytest.mark.asyncio
async def test_checkpointer_second_turn_keeps_graph_history():
    saver = InMemorySaver()
    recorder = RecordingLLMProvider()
    thread_id = "conv-42"

    await run_graph(
        LLMGateway({"mock": recorder}),
        _tools(),
        _agent(),
        [AIMessage(role="user", content="hello")],
        thread_id=thread_id,
        checkpointer=saver,
    )
    await run_graph(
        LLMGateway({"mock": recorder}),
        _tools(),
        _agent(),
        [AIMessage(role="user", content="again")],
        thread_id=thread_id,
        checkpointer=saver,
    )

    assert recorder.seen[0] == ["hello"]
    assert recorder.seen[1] == ["hello", "ack:hello", "again"]


@pytest.mark.asyncio
async def test_checkpointer_survives_new_graph_instance():
    saver = InMemorySaver()
    thread_id = "conv-restart"
    await run_graph(
        LLMGateway({"mock": MockLLMProvider()}),
        _tools(),
        _agent(),
        [AIMessage(role="user", content="ping")],
        thread_id=thread_id,
        checkpointer=saver,
    )

    restarted = AgentGraph(
        LLMGateway({"mock": MockLLMProvider()}),
        _tools(),
        _agent(),
        checkpointer=saver,
    )
    snapshot = await restarted._graph.aget_state(
        {"configurable": {"thread_id": thread_id}}
    )
    contents = [message.content for message in snapshot.values["messages"]]
    assert "ping" in contents
    assert any("Mock AI Response" in (content or "") for content in contents)


@pytest.mark.asyncio
async def test_checkpointer_isolates_threads():
    saver = InMemorySaver()
    recorder = RecordingLLMProvider()

    await run_graph(
        LLMGateway({"mock": recorder}),
        _tools(),
        _agent(),
        [AIMessage(role="user", content="from-a")],
        thread_id="thread-a",
        checkpointer=saver,
    )
    await run_graph(
        LLMGateway({"mock": recorder}),
        _tools(),
        _agent(),
        [AIMessage(role="user", content="from-b")],
        thread_id="thread-b",
        checkpointer=saver,
    )

    assert recorder.seen[1] == ["from-b"]


def _decisions(pending: dict, approved: bool = True) -> list[dict]:
    return [
        {"id": item["id"], "approved": approved} for item in pending["pending"]
    ]


class TwoEmailsLLMProvider(BaseLLMProvider):
    async def chat(
        self,
        model: str,
        messages: list[AIMessage],
        tools: list[dict] | None = None,
    ) -> AIMessage:
        if messages[-1].role == "tool":
            results = [message.content for message in messages if message.role == "tool"]
            return AIMessage(role="assistant", content=" | ".join(results[-2:]))
        return AIMessage(
            role="assistant",
            content=None,
            tool_calls=[
                {
                    "id": "call_send_email_1",
                    "function": {
                        "name": "send_email",
                        "arguments": '{"to": "a@eaap.com", "subject": "a", "body": "a"}',
                    },
                },
                {
                    "id": "call_send_email_2",
                    "function": {
                        "name": "send_email",
                        "arguments": '{"to": "b@eaap.com", "subject": "b", "body": "b"}',
                    },
                },
            ],
        )


@pytest.mark.asyncio
async def test_hitl_pauses_before_send_email():
    saver = InMemorySaver()
    tools, email = _hitl_tools()
    graph = AgentGraph(
        LLMGateway({"mock": MockLLMProvider()}),
        tools,
        _agent(),
        checkpointer=saver,
    )
    result = await graph.run(
        [AIMessage(role="user", content="请发邮件给老板")],
        thread_id="hitl-1",
    )

    assert result.status == "interrupted"
    assert result.pending["pending"][0]["name"] == "send_email"
    assert email.sent == []


@pytest.mark.asyncio
async def test_hitl_resume_approved_sends_email():
    saver = InMemorySaver()
    tools, email = _hitl_tools()
    graph = AgentGraph(
        LLMGateway({"mock": MockLLMProvider()}),
        tools,
        _agent(),
        checkpointer=saver,
    )
    result = await graph.run(
        [AIMessage(role="user", content="请发邮件给老板")],
        thread_id="hitl-2",
    )
    result = await graph.resume("hitl-2", _decisions(result.pending, True))

    assert result.status == "completed"
    assert email.sent
    assert "已发送" in (result.message.content or "")


@pytest.mark.asyncio
async def test_hitl_resume_denied_does_not_send():
    saver = InMemorySaver()
    tools, email = _hitl_tools()
    graph = AgentGraph(
        LLMGateway({"mock": MockLLMProvider()}),
        tools,
        _agent(),
        checkpointer=saver,
    )
    paused = await graph.run(
        [AIMessage(role="user", content="请发邮件给老板")],
        thread_id="hitl-3",
    )
    result = await graph.resume("hitl-3", _decisions(paused.pending, False))

    assert result.status == "completed"
    assert email.sent == []
    assert "user denied" in (result.message.content or "")


@pytest.mark.asyncio
async def test_hitl_resume_requires_every_pending_id():
    saver = InMemorySaver()
    tools, _ = _hitl_tools()
    graph = AgentGraph(
        LLMGateway({"mock": TwoEmailsLLMProvider()}),
        tools,
        _agent(),
        checkpointer=saver,
    )
    paused = await graph.run(
        [AIMessage(role="user", content="请发两封邮件")],
        thread_id="hitl-missing",
    )

    with pytest.raises(BusinessException, match="每个待审批工具"):
        await graph.resume(
            "hitl-missing",
            [{"id": paused.pending["pending"][0]["id"], "approved": True}],
        )


@pytest.mark.asyncio
async def test_hitl_mixed_decisions_in_one_resume():
    saver = InMemorySaver()
    tools, email = _hitl_tools()
    graph = AgentGraph(
        LLMGateway({"mock": TwoEmailsLLMProvider()}),
        tools,
        _agent(),
        checkpointer=saver,
    )
    paused = await graph.run(
        [AIMessage(role="user", content="请发两封邮件")],
        thread_id="hitl-mixed",
    )
    assert [item["id"] for item in paused.pending["pending"]] == [
        "call_send_email_1",
        "call_send_email_2",
    ]

    result = await graph.resume(
        "hitl-mixed",
        [
            {"id": "call_send_email_1", "approved": True},
            {"id": "call_send_email_2", "approved": False},
        ],
    )

    assert result.status == "completed"
    assert email.sent == [{"to": "a@eaap.com", "subject": "a", "body": "a"}]
    assert "已发送" in (result.message.content or "")
    assert "user denied" in (result.message.content or "")


@pytest.mark.asyncio
async def test_hitl_survives_new_graph_instance():
    saver = InMemorySaver()
    tools, email = _hitl_tools()
    first = AgentGraph(
        LLMGateway({"mock": MockLLMProvider()}),
        tools,
        _agent(),
        checkpointer=saver,
    )
    paused = await first.run(
        [AIMessage(role="user", content="请发邮件给老板")],
        thread_id="hitl-4",
    )

    restarted = AgentGraph(
        LLMGateway({"mock": MockLLMProvider()}),
        tools,
        _agent(),
        checkpointer=saver,
    )
    status = await restarted.get_status("hitl-4")
    assert status["status"] == "interrupted"
    result = await restarted.resume("hitl-4", _decisions(paused.pending, True))

    assert result.status == "completed"
    assert email.sent


@pytest.mark.asyncio
async def test_calculator_does_not_require_approval():
    saver = InMemorySaver()
    tools, email = _hitl_tools()
    graph = AgentGraph(
        LLMGateway({"mock": MockLLMProvider()}),
        tools,
        _agent(),
        checkpointer=saver,
    )
    result = await graph.run(
        [AIMessage(role="user", content="12*7+5")],
        thread_id="hitl-calc",
    )

    assert result.status == "completed"
    assert result.message.content == "计算结果是 89"
    assert email.sent == []


@pytest.mark.asyncio
async def test_hitl_without_checkpointer_raises():
    tools, _ = _hitl_tools()
    with pytest.raises(AgentRuntimeException, match="checkpointer"):
        await run_graph(
            LLMGateway({"mock": MockLLMProvider()}),
            tools,
            _agent(),
            [AIMessage(role="user", content="请发邮件给老板")],
        )


@pytest.mark.asyncio
async def test_hitl_blocks_new_turn_until_resume():
    saver = InMemorySaver()
    tools, _ = _hitl_tools()
    graph = AgentGraph(
        LLMGateway({"mock": MockLLMProvider()}),
        tools,
        _agent(),
        checkpointer=saver,
    )
    await graph.run(
        [AIMessage(role="user", content="请发邮件给老板")],
        thread_id="hitl-block",
    )

    with pytest.raises(BusinessException, match="待审批"):
        await graph.run(
            [AIMessage(role="user", content="再聊一句")],
            thread_id="hitl-block",
        )


def _fake_memory():
    saved = {"user": [], "assistant": [], "pairs": []}

    async def create_user_message(db, conversation_id, user_message):
        saved["user"].append(user_message)
        return SimpleNamespace(created_at=None)

    async def create_assistant_message(db, conversation_id, assistant_message):
        saved["assistant"].append(assistant_message)
        return SimpleNamespace(created_at=None)

    async def create_message(db, conversation_id, user_message, assistant_message):
        saved["pairs"].append((user_message, assistant_message))
        return SimpleNamespace(created_at=None)

    async def fake_build(db, agent, conversation, user_message, variables):
        return [AIMessage(role="user", content=user_message)]

    return saved, SimpleNamespace(
        create_user_message=create_user_message,
        create_assistant_message=create_assistant_message,
        create_message=create_message,
    ), fake_build


@pytest.mark.asyncio
async def test_execute_pauses_then_resume_saves_assistant_only():
    saver = InMemorySaver()
    tools, email = _hitl_tools()
    saved, memory, fake_build = _fake_memory()
    executor = AgentExecutor(
        llm_gateway=LLMGateway({"mock": MockLLMProvider()}),
        prompt_manager=None,
        memory_manager=memory,
        tool_manager=tools,
        checkpointer=saver,
    )
    executor._build_messages = fake_build
    conversation = SimpleNamespace(id=7)

    paused = await executor.execute(
        db=None,
        agent=_agent(),
        conversation=conversation,
        user_message="请发邮件给老板",
    )

    assert paused.status == "interrupted"
    assert paused.pending["pending"][0]["name"] == "send_email"
    assert email.sent == []
    assert saved["user"] == ["请发邮件给老板"]
    assert saved["pairs"] == []
    assert saved["assistant"] == []

    done = await executor.resume(
        None,
        _agent(),
        conversation,
        _decisions(paused.pending, True),
    )

    assert done.status == "completed"
    assert email.sent
    assert saved["assistant"]
    assert "已发送" in saved["assistant"][0]


@pytest.mark.asyncio
async def test_execute_stream_emits_interrupt_and_saves_user_only():
    saver = InMemorySaver()
    tools, email = _hitl_tools()
    saved, memory, fake_build = _fake_memory()
    executor = AgentExecutor(
        llm_gateway=LLMGateway({"mock": MockLLMProvider()}),
        prompt_manager=None,
        memory_manager=memory,
        tool_manager=tools,
        checkpointer=saver,
    )
    executor._build_messages = fake_build

    events: list[tuple[str, dict]] = []
    async for event in executor.execute_stream(
        db=None,
        agent=_agent(),
        conversation=SimpleNamespace(id=8),
        user_message="请发邮件给老板",
    ):
        events.append(event)

    kinds = [event for event, _ in events]
    assert kinds.count("interrupt") == 1
    assert events[-1] == (
        "done",
        {"conversation_id": 8, "status": "interrupted"},
    )
    assert email.sent == []
    assert saved["user"] == ["请发邮件给老板"]
    assert saved["pairs"] == []
