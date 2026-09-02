import pytest

from app.ai.knowledge.eval import (
    GOLD_PATH,
    citation_precision,
    load_gold,
    recall_at_k,
    run_retrieval_eval,
)


def test_gold_set_has_at_least_20_cases():
    gold = load_gold()
    assert GOLD_PATH.is_file()
    assert len(gold["cases"]) >= 20
    assert len(gold["documents"]) >= 20


def test_recall_and_precision_math():
    assert recall_at_k([1], [1, 2]) == 1.0
    assert recall_at_k([1, 2], [1]) == 0.5
    assert recall_at_k([], []) == 1.0
    assert recall_at_k([], [1]) == 0.0
    assert citation_precision([1], [1, 2]) == 0.5
    assert citation_precision([], []) == 1.0
    assert citation_precision([1], []) == 0.0


@pytest.mark.asyncio
async def test_must_hit_gold_cases():
    summary = await run_retrieval_eval()
    failed = [
        item.case_id
        for item in summary.results
        if item.must_hit and (item.recall < 1.0 or item.precision < 1.0)
    ]
    assert failed == []
    assert summary.empty_query_hallucination == 0.0
    assert summary.recall_at_k == 1.0
    assert summary.citation_precision == 1.0
    assert summary.embedder_label == "HashEmbeddingClient"
    assert summary.reranker_label == "FeatureReranker"
