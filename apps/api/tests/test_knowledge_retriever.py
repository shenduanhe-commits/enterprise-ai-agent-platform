from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.ai.knowledge.embedding import HashEmbeddingClient
from app.ai.knowledge.reranker import CrossEncoderReranker
from app.ai.knowledge.retriever import KnowledgeRetriever
from app.ai.knowledge.store import ChunkRecord, InMemoryChunkStore
from app.ai.llm.gateway import LLMGateway
from app.ai.llm.providers.base import BaseLLMProvider
from app.ai.llm.providers.mock import MockLLMProvider
from app.ai.runtime.agent_executor import AgentExecutor
from app.ai.runtime.agent_graph import run_graph
from app.ai.tools.builtin.calculator import CalculatorTool
from app.ai.tools.manager import ToolManager
from app.ai.type import AIMessage
from langgraph.checkpoint.memory import InMemorySaver


def _record(**overrides) -> ChunkRecord:
    data = {
        "document_id": 9,
        "user_id": 7,
        "agent_id": 3,
        "ordinal": 0,
        "text": "年假为 15 天。",
        "source": "handbook",
        "vector": [1.0] + [0.0] * 63,
    }
    data.update(overrides)
    return ChunkRecord(**data)


async def _indexed_store(*records: ChunkRecord) -> InMemoryChunkStore:
    store = InMemoryChunkStore()
    embedder = HashEmbeddingClient()
    indexed = []
    for record in records:
        vector = (await embedder.embed([record.text]))[0]
        indexed.append(
            ChunkRecord(
                document_id=record.document_id,
                user_id=record.user_id,
                agent_id=record.agent_id,
                ordinal=record.ordinal,
                text=record.text,
                source=record.source,
                vector=vector,
            )
        )
    await store.upsert(indexed)
    return store


@pytest.mark.asyncio
async def test_inmemory_search_filters_by_user_and_agent():
    store = await _indexed_store(
        _record(),
        _record(document_id=10, user_id=8, text="别人的年假 99 天。"),
        _record(document_id=11, agent_id=4, text="另一个 Agent 的年假 3 天。"),
    )
    hits = await store.search([1.0] + [0.0] * 63, user_id=7, agent_id=3, limit=8)
    assert [hit.document_id for hit in hits] == [9]


@pytest.mark.asyncio
async def test_retriever_keeps_handbook_and_drops_calculator_query():
    store = await _indexed_store(_record())
    retriever = KnowledgeRetriever(HashEmbeddingClient(), store)

    hits = await retriever.retrieve("年假几天", user_id=7, agent_id=3)
    assert len(hits) == 1
    assert hits[0].document_id == 9
    assert "15" in hits[0].text

    assert await retriever.retrieve("12*7+5 等于多少", user_id=7, agent_id=3) == []
    assert await retriever.retrieve("年假几天", user_id=8, agent_id=3) == []


@pytest.mark.asyncio
async def test_hybrid_keeps_keyword_hit_when_dense_prefers_distractor():
    store = InMemoryChunkStore()
    await store.upsert(
        [
            ChunkRecord(
                document_id=1,
                user_id=7,
                agent_id=3,
                ordinal=0,
                text="今天天气很好，适合散步。",
                source="weather",
                vector=[1.0, 0.0, 0.0, 0.0],
            ),
            ChunkRecord(
                document_id=2,
                user_id=7,
                agent_id=3,
                ordinal=0,
                text="工单号 ABC-123 已关闭。",
                source="ticket",
                vector=[0.0, 1.0, 0.0, 0.0],
            ),
        ]
    )

    class _AlignedEmbedder:
        size = 4
        use_lexical_gate = False

        async def embed(self, texts: list[str]) -> list[list[float]]:
            return [[1.0, 0.0, 0.0, 0.0] for _ in texts]

    retriever = KnowledgeRetriever(_AlignedEmbedder(), store)
    hits = await retriever.retrieve("ABC-123", user_id=7, agent_id=3)
    assert hits[0].document_id == 2
    assert "ABC-123" in hits[0].text


@pytest.mark.asyncio
async def test_retrieve_respects_context_token_budget(monkeypatch):
    from app.ai.knowledge import retriever as retriever_mod
    from app.ai.knowledge.budget import estimate_tokens

    monkeypatch.setattr(retriever_mod.settings, "KNOWLEDGE_CONTEXT_TOKENS", 8)
    store = InMemoryChunkStore()
    await store.upsert(
        [
            ChunkRecord(
                document_id=1,
                user_id=7,
                agent_id=3,
                ordinal=0,
                text="年假为十五天必须提前报备审批办理完成",
                source="handbook",
                vector=[1.0] + [0.0] * 63,
            )
        ]
    )
    hits = await KnowledgeRetriever(HashEmbeddingClient(), store).retrieve(
        "年假几天", user_id=7, agent_id=3
    )
    assert len(hits) == 1
    assert estimate_tokens(hits[0].text) <= 8


@pytest.mark.asyncio
async def test_rerank_prefers_specific_chunk_over_dense_overview():
    store = InMemoryChunkStore()
    await store.upsert(
        [
            ChunkRecord(
                document_id=1,
                user_id=7,
                agent_id=3,
                ordinal=0,
                text="年假制度见人力资源部通知。",
                source="overview",
                vector=[1.0, 0.0, 0.0, 0.0],
            ),
            ChunkRecord(
                document_id=2,
                user_id=7,
                agent_id=3,
                ordinal=0,
                text="年假多少天：15 天。年假需提前申请。",
                source="detail",
                vector=[0.35, 0.94, 0.0, 0.0],
            ),
        ]
    )

    class _AlignedEmbedder:
        size = 4
        use_lexical_gate = False

        async def embed(self, texts: list[str]) -> list[list[float]]:
            return [[1.0, 0.0, 0.0, 0.0] for _ in texts]

    hits = await KnowledgeRetriever(_AlignedEmbedder(), store).retrieve(
        "年假多少天", user_id=7, agent_id=3
    )
    assert hits[0].document_id == 2
    assert "15" in hits[0].text


@pytest.mark.asyncio
async def test_retriever_uses_injected_cross_encoder_order():
    store = InMemoryChunkStore()
    await store.upsert(
        [
            ChunkRecord(
                document_id=1,
                user_id=7,
                agent_id=3,
                ordinal=0,
                text="年假多少天：15 天。年假需提前申请。",
                source="detail",
                vector=[1.0, 0.0, 0.0, 0.0],
            ),
            ChunkRecord(
                document_id=2,
                user_id=7,
                agent_id=3,
                ordinal=0,
                text="年假制度见人力资源部通知。",
                source="overview",
                vector=[0.9, 0.1, 0.0, 0.0],
            ),
        ]
    )

    class _AlignedEmbedder:
        size = 4
        use_lexical_gate = False

        async def embed(self, texts: list[str]) -> list[list[float]]:
            return [[1.0, 0.0, 0.0, 0.0] for _ in texts]

    async def score_fn(query: str, documents: list[str]) -> list[float]:
        return [0.1 if "15" in text else 0.9 for text in documents]

    hits = await KnowledgeRetriever(
        _AlignedEmbedder(),
        store,
        CrossEncoderReranker(
            api_key="k",
            model="bge-reranker",
            base_url="http://example.test/v1",
            score_fn=score_fn,
        ),
    ).retrieve("年假多少天", user_id=7, agent_id=3)
    assert hits[0].document_id == 2


@pytest.mark.asyncio
async def test_delete_then_chat_has_no_citations():
    store = await _indexed_store(_record(), _record(document_id=10, user_id=8, text="别人的年假 99 天。"))
    await store.delete_by_document(9, user_id=7)
    retriever = KnowledgeRetriever(HashEmbeddingClient(), store)

    assert await retriever.retrieve("年假几天", user_id=7, agent_id=3) == []
    others = await retriever.retrieve("年假几天", user_id=8, agent_id=3)
    assert [hit.document_id for hit in others] == [10]

    result = await _chat_executor(retriever).execute(
        None,
        SimpleNamespace(id=3, provider="mock", model_name="mock-model"),
        SimpleNamespace(id=1, user_id=7, agent_id=3),
        user_message="年假几天",
    )
    assert result.citations == []
    assert "15" not in (result.content or "")


def _chat_executor(retriever: KnowledgeRetriever | None = None) -> AgentExecutor:
    tools = ToolManager()
    tools.register(CalculatorTool())
    executor = AgentExecutor(
        llm_gateway=LLMGateway({"mock": MockLLMProvider()}),
        prompt_manager=SimpleNamespace(),
        memory_manager=SimpleNamespace(),
        tool_manager=tools,
        knowledge_retriever=retriever,
    )

    async def build_prompt(db, agent, variables=None):
        return AIMessage(role="system", content="you are helpful")

    async def recent_messages(db, conversation_id, limit=10):
        return []

    async def save_message(db, conversation_id, user_message, assistant_message):
        return SimpleNamespace(created_at=datetime.now(timezone.utc))

    executor.prompt_manager.build = build_prompt
    executor.memory_manager.get_recent_messages = recent_messages
    executor.memory_manager.create_message = save_message
    return executor


@pytest.mark.asyncio
async def test_chat_returns_citations_and_uses_handbook():
    store = await _indexed_store(_record())
    executor = _chat_executor(KnowledgeRetriever(HashEmbeddingClient(), store))

    result = await executor.execute(
        None,
        SimpleNamespace(id=3, provider="mock", model_name="mock-model"),
        SimpleNamespace(id=1, user_id=7, agent_id=3),
        user_message="年假几天",
    )

    assert result.citations
    assert result.citations[0].document_id == 9
    assert result.citations[0].title == "handbook"
    assert "15" in (result.content or "")


@pytest.mark.asyncio
async def test_calculator_chat_keeps_empty_citations():
    store = await _indexed_store(_record())
    executor = _chat_executor(KnowledgeRetriever(HashEmbeddingClient(), store))

    result = await executor.execute(
        None,
        SimpleNamespace(id=3, provider="mock", model_name="mock-model"),
        SimpleNamespace(id=1, user_id=7, agent_id=3),
        user_message="12*7+5 等于多少",
    )

    assert result.content == "计算结果是 89"
    assert result.citations == []


@pytest.mark.asyncio
async def test_checkpointer_second_turn_appends_knowledge_context():
    saver = InMemorySaver()

    class Recorder(BaseLLMProvider):
        def __init__(self):
            self.seen: list[list[str | None]] = []

        async def chat(self, model, messages, tools=None, response_format=None):
            self.seen.append([message.content for message in messages])
            last = messages[-1].content or ""
            return AIMessage(role="assistant", content=f"ack:{last}")

    recorder = Recorder()
    tools = ToolManager()
    tools.register(CalculatorTool())
    agent = SimpleNamespace(provider="mock", model_name="mock-model")
    gateway = LLMGateway({"mock": recorder})

    await run_graph(
        gateway,
        tools,
        agent,
        [AIMessage(role="user", content="hello")],
        thread_id="conv-rag",
        checkpointer=saver,
    )
    await run_graph(
        gateway,
        tools,
        agent,
        [
            AIMessage(role="system", content="you are helpful"),
            AIMessage(role="system", content="【知识库】\n年假为 15 天。"),
            AIMessage(role="user", content="年假几天"),
        ],
        thread_id="conv-rag",
        checkpointer=saver,
    )

    assert recorder.seen[1][-2] == "【知识库】\n年假为 15 天。"
    assert recorder.seen[1][-1] == "年假几天"
