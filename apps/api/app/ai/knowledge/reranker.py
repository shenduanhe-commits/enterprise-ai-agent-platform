import logging
from collections.abc import Awaitable, Callable
from dataclasses import replace
from typing import Protocol

import httpx

from app.ai.knowledge.sparse import lexical_terms
from app.ai.knowledge.store import SearchHit
from app.core.config import settings

logger = logging.getLogger(__name__)

ScoreFn = Callable[[str, list[str]], Awaitable[list[float]]]


class Reranker(Protocol):
    async def rerank(self, query: str, hits: list[SearchHit]) -> list[SearchHit]: ...


class FeatureReranker:
    """用 query-document 对重排：dense 分 + 问句词覆盖率。不调厂商接口。"""

    async def rerank(self, query: str, hits: list[SearchHit]) -> list[SearchHit]:
        if len(hits) <= 1:
            return list(hits)
        terms = lexical_terms(query)
        term_count = max(len(terms), 1)
        scored: list[tuple[float, SearchHit]] = []
        for hit in hits:
            haystack = hit.text.lower()
            matched = sum(1 for term in terms if term in haystack)
            score = hit.dense_score + 2.0 * (matched / term_count)
            scored.append((score, replace(hit, score=score)))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [hit for _, hit in scored]


class CrossEncoderReranker:
    """把 (query, chunk) 成对送给 rerank 模型打分。失败则回退 FeatureReranker。"""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        *,
        score_fn: ScoreFn | None = None,
        fallback: Reranker | None = None,
    ):
        self.model = model
        self._api_key = api_key
        self._base_url = base_url
        self._score_fn = score_fn
        self._fallback = fallback or FeatureReranker()

    async def rerank(self, query: str, hits: list[SearchHit]) -> list[SearchHit]:
        if len(hits) <= 1:
            return list(hits)
        try:
            scores = await self._score(query, [hit.text for hit in hits])
            if len(scores) != len(hits):
                raise ValueError(
                    f"rerank score count {len(scores)} != hits {len(hits)}"
                )
        except Exception:
            logger.exception("cross-encoder rerank failed; falling back to features")
            return await self._fallback.rerank(query, hits)
        scored = [
            (score, replace(hit, score=score)) for hit, score in zip(hits, scores)
        ]
        scored.sort(key=lambda item: item[0], reverse=True)
        return [hit for _, hit in scored]

    async def _score(self, query: str, documents: list[str]) -> list[float]:
        if self._score_fn is not None:
            return await self._score_fn(query, documents)
        url = _rerank_url(self._base_url)
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = _rerank_payload(self.model, query, documents, self._base_url)
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return _parse_rerank_scores(response.json(), len(documents))


_cached_reranker: Reranker | None = None


# 获取重排器
def get_reranker() -> Reranker:
    global _cached_reranker
    if _cached_reranker is None:
        _cached_reranker = build_reranker()
    return _cached_reranker


# 构建重排器
def build_reranker() -> Reranker:
    model = (settings.RERANK_MODEL or "").strip()
    api_key = (settings.RERANK_API_KEY or "").strip()
    base_url = (settings.RERANK_BASE_URL or "").strip()
    if model and api_key and base_url:
        logger.info("knowledge rerank: cross-encoder model=%s", model)
        return CrossEncoderReranker(api_key=api_key, model=model, base_url=base_url)
    logger.info("knowledge rerank: feature (no RERANK_MODEL/KEY/URL)")
    return FeatureReranker()


# 构建重排URL
def _rerank_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/rerank") or "text-rerank" in base:
        return base
    return f"{base}/rerank"


# 构建重排负载
def _rerank_payload(
    model: str, query: str, documents: list[str], base_url: str
) -> dict:
    if "dashscope" in base_url.lower() or "text-rerank" in base_url.lower():
        return {
            "model": model,
            "input": {"query": query, "documents": documents},
            "parameters": {
                "return_documents": False,
                "top_n": len(documents),
            },
        }
    return {
        "model": model,
        "query": query,
        "documents": documents,
        "top_n": len(documents),
    }


# 解析重排得分
def _parse_rerank_scores(payload: object, count: int) -> list[float]:
    if not isinstance(payload, dict):
        raise TypeError("rerank response is not an object")
    results = payload.get("results")
    output = payload.get("output")
    if results is None and isinstance(output, dict):
        results = output.get("results")
    if not isinstance(results, list) or not results:
        raise ValueError("rerank response missing results")
    scores = [float("-inf")] * count
    for item in results:
        if not isinstance(item, dict):
            continue
        index = int(item["index"])
        raw = item.get("relevance_score", item.get("score"))
        if raw is None or not (0 <= index < count):
            continue
        scores[index] = float(raw)
    if all(score == float("-inf") for score in scores):
        raise ValueError("rerank response had no usable scores")
    return scores
