import pytest

from app.ai.knowledge import reranker as reranker_mod
from app.ai.knowledge.reranker import (
    CrossEncoderReranker,
    FeatureReranker,
    _parse_rerank_scores,
    _rerank_payload,
    _rerank_url,
    build_reranker,
)
from app.ai.knowledge.store import SearchHit


def _hit(document_id: int, text: str, *, dense_score: float) -> SearchHit:
    return SearchHit(
        document_id=document_id,
        user_id=7,
        agent_id=3,
        ordinal=0,
        text=text,
        source="doc",
        score=dense_score,
        chunk_id=str(document_id),
        dense_score=dense_score,
    )


@pytest.mark.asyncio
async def test_feature_reranker_prefers_higher_query_coverage():
    overview = _hit(1, "年假制度见人力资源部通知。", dense_score=0.95)
    detail = _hit(2, "年假多少天：15 天。年假需提前申请。", dense_score=0.35)
    reranked = await FeatureReranker().rerank("年假多少天", [overview, detail])
    assert [hit.document_id for hit in reranked] == [2, 1]


@pytest.mark.asyncio
async def test_feature_reranker_skips_single_hit():
    only = _hit(1, "年假为 15 天。", dense_score=0.1)
    assert await FeatureReranker().rerank("年假几天", [only]) == [only]


@pytest.mark.asyncio
async def test_cross_encoder_orders_by_model_scores():
    overview = _hit(1, "年假制度见人力资源部通知。", dense_score=0.95)
    detail = _hit(2, "年假多少天：15 天。年假需提前申请。", dense_score=0.35)

    async def score_fn(query: str, documents: list[str]) -> list[float]:
        assert query == "年假多少天"
        assert len(documents) == 2
        return [0.1, 0.9]

    reranked = await CrossEncoderReranker(
        api_key="k",
        model="bge-reranker",
        base_url="http://example.test/v1",
        score_fn=score_fn,
    ).rerank("年假多少天", [overview, detail])
    assert [hit.document_id for hit in reranked] == [2, 1]
    assert reranked[0].score == 0.9


@pytest.mark.asyncio
async def test_cross_encoder_falls_back_to_features_on_error():
    overview = _hit(1, "年假制度见人力资源部通知。", dense_score=0.95)
    detail = _hit(2, "年假多少天：15 天。年假需提前申请。", dense_score=0.35)

    async def boom(query: str, documents: list[str]) -> list[float]:
        raise RuntimeError("rerank down")

    reranked = await CrossEncoderReranker(
        api_key="k",
        model="bge-reranker",
        base_url="http://example.test/v1",
        score_fn=boom,
    ).rerank("年假多少天", [overview, detail])
    assert [hit.document_id for hit in reranked] == [2, 1]


def test_factory_uses_features_without_keys(monkeypatch):
    reranker_mod._cached_reranker = None
    monkeypatch.setattr(reranker_mod.settings, "RERANK_API_KEY", None)
    monkeypatch.setattr(reranker_mod.settings, "RERANK_BASE_URL", "http://example.test/v1")
    monkeypatch.setattr(reranker_mod.settings, "RERANK_MODEL", "bge-reranker")
    assert isinstance(build_reranker(), FeatureReranker)


def test_factory_uses_cross_encoder_when_configured(monkeypatch):
    reranker_mod._cached_reranker = None
    monkeypatch.setattr(reranker_mod.settings, "RERANK_API_KEY", "k")
    monkeypatch.setattr(reranker_mod.settings, "RERANK_BASE_URL", "http://example.test/v1")
    monkeypatch.setattr(reranker_mod.settings, "RERANK_MODEL", "bge-reranker")
    reranker = build_reranker()
    assert isinstance(reranker, CrossEncoderReranker)
    assert reranker.model == "bge-reranker"


def test_rerank_url_and_payload_shapes():
    assert _rerank_url("http://example.test/v1") == "http://example.test/v1/rerank"
    assert _rerank_url("http://example.test/v1/rerank") == "http://example.test/v1/rerank"
    cohere = _rerank_payload("m", "q", ["a"], "http://example.test/v1")
    assert cohere["query"] == "q"
    assert cohere["documents"] == ["a"]
    dash = _rerank_payload(
        "gte-rerank",
        "q",
        ["a"],
        "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank",
    )
    assert dash["input"]["query"] == "q"
    assert dash["input"]["documents"] == ["a"]


def test_parse_cohere_and_dashscope_scores():
    assert _parse_rerank_scores(
        {"results": [{"index": 1, "relevance_score": 0.9}, {"index": 0, "relevance_score": 0.2}]},
        2,
    ) == [0.2, 0.9]
    assert _parse_rerank_scores(
        {"output": {"results": [{"index": 0, "relevance_score": 0.7}]}},
        1,
    ) == [0.7]
