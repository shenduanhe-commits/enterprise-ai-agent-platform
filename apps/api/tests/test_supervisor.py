from types import SimpleNamespace

import httpx
import pytest

from app.ai.a2a.client import A2A_KEY_HEADER, send_a2a
from app.ai.a2a.protocol import A2AMessage, A2AReply
from app.ai.knowledge.store import SearchHit
from app.ai.llm.gateway import LLMGateway
from app.ai.llm.providers.mock import MockLLMProvider
from app.ai.runtime.agent_executor import AgentExecutor
from app.ai.runtime.supervisor import SupervisorGraph, wants_supervisor
from app.ai.tools.manager import ToolManager


class FakeRetriever:
    def __init__(self, hits=None):
        self.hits = hits or [
            SearchHit(
                document_id=9,
                user_id=7,
                agent_id=3,
                ordinal=0,
                text="年假为 15 天。",
                source="handbook",
                score=1.0,
                chunk_id="c1",
            )
        ]

    async def retrieve(self, query, *, user_id, agent_id):
        _ = query, user_id, agent_id
        return self.hits


def _agent():
    return SimpleNamespace(
        id=3, provider="mock", model_name="mock-model", name="ops"
    )


def test_wants_supervisor_only_for_brief():
    assert wants_supervisor("根据知识库写一页年假简报")
    assert wants_supervisor("请写一页给领导")
    assert not wants_supervisor("12*7+5 等于多少")
    assert not wants_supervisor("年假几天")


@pytest.mark.asyncio
async def test_supervisor_runs_knowledge_then_writer():
    graph = SupervisorGraph(
        LLMGateway({"mock": MockLLMProvider()}),
        _agent(),
        knowledge_retriever=FakeRetriever(),
        user_id=7,
        agent_id=3,
        writer_url=None,
    )
    result = await graph.run("根据知识库写一页年假简报")
    assert result.status == "completed"
    assert result.agents == ["knowledge", "writer"]
    assert "简报" in (result.message.content or "")
    assert "年假" in (result.message.content or "")
    assert graph.citations[0].document_id == 9


@pytest.mark.asyncio
async def test_writer_failure_aborts():
    async def boom(url, message, *, api_key, timeout=30.0, client=None):
        _ = url, message, api_key, timeout, client
        return A2AReply(
            from_agent="writer",
            task_id="t",
            content="model down",
            status="failed",
        )

    graph = SupervisorGraph(
        LLMGateway({"mock": MockLLMProvider()}),
        _agent(),
        knowledge_retriever=FakeRetriever(),
        user_id=7,
        agent_id=3,
        writer_url="http://writer.test/api/v1/a2a/message",
        a2a_key="k",
        a2a_send=boom,
    )
    result = await graph.run("写一页简报")
    assert result.status == "failed"
    assert result.agents == ["knowledge", "writer"]
    assert "model down" in (result.message.content or "")


@pytest.mark.asyncio
async def test_a2a_client_posts_envelope():
    recorded = {}

    def handler(request: httpx.Request) -> httpx.Response:
        recorded["url"] = str(request.url)
        recorded["key"] = request.headers.get(A2A_KEY_HEADER)
        body = A2AMessage.model_validate_json(request.content)
        recorded["to"] = body.to_agent
        return httpx.Response(
            200,
            json=A2AReply(
                from_agent="writer",
                task_id=body.task_id,
                content="ok-brief",
                status="completed",
            ).model_dump(),
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        reply = await send_a2a(
            "http://writer.test/api/v1/a2a/message",
            A2AMessage(
                from_agent="supervisor",
                to_agent="writer",
                task_id="task-1",
                content="notes",
            ),
            api_key="secret",
            client=client,
        )
    assert reply.content == "ok-brief"
    assert recorded["to"] == "writer"
    assert recorded["key"] == "secret"


@pytest.mark.asyncio
async def test_executor_brief_exposes_two_agent_names():
    saved = {}

    async def create_message(db, conversation_id, user_message, assistant_message):
        saved["content"] = assistant_message
        return SimpleNamespace(created_at=None)

    executor = AgentExecutor(
        llm_gateway=LLMGateway({"mock": MockLLMProvider()}),
        prompt_manager=None,
        memory_manager=SimpleNamespace(create_message=create_message),
        tool_manager=ToolManager(),
        knowledge_retriever=FakeRetriever(),
    )
    result = await executor.execute(
        db=None,
        agent=_agent(),
        conversation=SimpleNamespace(id=1, user_id=7, agent_id=3),
        user_message="根据知识库写一页年假简报",
    )
    assert result.status == "completed"
    assert result.agents == ["knowledge", "writer"]
    assert result.agent_name == "writer"
    assert "简报" in (result.content or "")
    assert saved["content"]
