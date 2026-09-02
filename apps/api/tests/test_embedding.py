from types import SimpleNamespace

import pytest

from app.ai.knowledge import embedding as embedding_mod
from app.ai.knowledge.embedding import (
    HASH_VECTOR_SIZE,
    HashEmbeddingClient,
    OpenAICompatEmbeddingClient,
    build_embedding_client,
)
from app.ai.knowledge.retriever import KnowledgeRetriever
from app.ai.knowledge.store import ChunkRecord, InMemoryChunkStore


class _FakeEmbeddings:
    def __init__(self, vectors: list[list[float]]):
        self.vectors = vectors
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            data=[SimpleNamespace(embedding=vector) for vector in self.vectors]
        )


class _CountingEmbeddings:
    def __init__(self):
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        inputs = kwargs["input"]
        return SimpleNamespace(
            data=[SimpleNamespace(embedding=[1.0, 0.0]) for _ in inputs]
        )


class _KeywordEmbedder:
    size = 4
    use_lexical_gate = False

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            if "年假" in text:
                vectors.append([1.0, 0.0, 0.0, 0.0])
            else:
                vectors.append([0.0, 1.0, 0.0, 0.0])
        return vectors


def test_factory_uses_hash_without_keys(monkeypatch):
    embedding_mod._cached_client = None
    monkeypatch.setattr(embedding_mod.settings, "EMBEDDING_API_KEY", None)
    monkeypatch.setattr(embedding_mod.settings, "EMBEDDING_BASE_URL", None)
    monkeypatch.setattr(
        embedding_mod.settings, "EMBEDDING_MODEL", "qwen3.7-text-embedding"
    )
    client = build_embedding_client()
    assert isinstance(client, HashEmbeddingClient)
    assert client.size == HASH_VECTOR_SIZE
    assert client.use_lexical_gate is True


def test_factory_uses_hash_without_model(monkeypatch):
    embedding_mod._cached_client = None
    monkeypatch.setattr(embedding_mod.settings, "EMBEDDING_API_KEY", "k")
    monkeypatch.setattr(
        embedding_mod.settings, "EMBEDDING_BASE_URL", "http://example.test/v1"
    )
    monkeypatch.setattr(embedding_mod.settings, "EMBEDDING_MODEL", None)
    client = build_embedding_client()
    assert isinstance(client, HashEmbeddingClient)


def test_factory_uses_embedding_endpoint(monkeypatch):
    embedding_mod._cached_client = None
    monkeypatch.setattr(embedding_mod.settings, "EMBEDDING_API_KEY", "k")
    monkeypatch.setattr(
        embedding_mod.settings, "EMBEDDING_BASE_URL", "http://example.test/v1"
    )
    monkeypatch.setattr(
        embedding_mod.settings, "EMBEDDING_MODEL", "qwen3.7-text-embedding"
    )
    monkeypatch.setattr(embedding_mod.settings, "EMBEDDING_DIM", 1024)
    client = build_embedding_client()
    assert isinstance(client, OpenAICompatEmbeddingClient)
    assert client.model == "qwen3.7-text-embedding"
    assert client.size == 1024
    assert client._base_url == "http://example.test/v1"
    assert client.use_lexical_gate is False


def test_factory_allows_empty_base_url(monkeypatch):
    embedding_mod._cached_client = None
    monkeypatch.setattr(embedding_mod.settings, "EMBEDDING_API_KEY", "openai")
    monkeypatch.setattr(embedding_mod.settings, "EMBEDDING_BASE_URL", None)
    monkeypatch.setattr(embedding_mod.settings, "EMBEDDING_MODEL", "text-embedding-3-small")
    monkeypatch.setattr(embedding_mod.settings, "EMBEDDING_DIM", 1536)
    client = build_embedding_client()
    assert isinstance(client, OpenAICompatEmbeddingClient)
    assert client.model == "text-embedding-3-small"
    assert client.size == 1536
    assert client._base_url is None


@pytest.mark.asyncio
async def test_openai_compat_embedder_reads_response_vectors():
    client = OpenAICompatEmbeddingClient(
        api_key="k", model="text-embedding-v3", size=2
    )
    fake = _FakeEmbeddings([[1.0, 0.0], [0.0, 1.0]])
    client._client = SimpleNamespace(embeddings=fake)

    vectors = await client.embed(["a", "b"])

    assert vectors == [[1.0, 0.0], [0.0, 1.0]]
    assert fake.calls[0]["model"] == "text-embedding-v3"
    assert fake.calls[0]["dimensions"] == 2
    assert fake.calls[0]["input"] == ["a", "b"]


@pytest.mark.asyncio
async def test_embed_uses_embedding_batch(monkeypatch):
    monkeypatch.setattr(embedding_mod.settings, "EMBEDDING_BATCH", 2)
    client = OpenAICompatEmbeddingClient(
        api_key="k", model="text-embedding-v3", size=2
    )
    fake = _CountingEmbeddings()
    client._client = SimpleNamespace(embeddings=fake)

    vectors = await client.embed(["a", "b", "c", "d", "e"])

    assert len(vectors) == 5
    assert [call["input"] for call in fake.calls] == [
        ["a", "b"],
        ["c", "d"],
        ["e"],
    ]


@pytest.mark.asyncio
async def test_semantic_retriever_uses_score_not_lexical_gate():
    store = InMemoryChunkStore()
    await store.upsert(
        [
            ChunkRecord(
                document_id=9,
                user_id=7,
                agent_id=3,
                ordinal=0,
                text="员工手册规定年假为 15 天。",
                source="handbook",
                vector=[1.0, 0.0, 0.0, 0.0],
            )
        ]
    )
    retriever = KnowledgeRetriever(_KeywordEmbedder(), store)

    hits = await retriever.retrieve("年假几天", user_id=7, agent_id=3)
    assert hits and hits[0].document_id == 9

    assert await retriever.retrieve("12*7+5 等于多少", user_id=7, agent_id=3) == []
