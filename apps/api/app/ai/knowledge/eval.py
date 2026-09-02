from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

from app.ai.knowledge.embedding import HashEmbeddingClient, get_embedding_client
from app.ai.knowledge.reranker import FeatureReranker, get_reranker
from app.ai.knowledge.retriever import KnowledgeRetriever
from app.ai.knowledge.store import ChunkRecord, InMemoryChunkStore, SearchHit

GOLD_PATH = Path(__file__).resolve().parents[3] / "evals" / "gold" / "retrieval.json"
REPORT_PATH = Path(__file__).resolve().parents[3] / "evals" / "reports" / "retrieval.md"


@dataclass
class CaseResult:
    case_id: str
    question: str
    expected: list[int]
    retrieved: list[int]
    recall: float
    precision: float
    must_hit: bool
    notes: str


@dataclass
class EvalSummary:
    k: int
    case_count: int
    recall_at_k: float
    citation_precision: float
    empty_query_hallucination: float
    results: list[CaseResult]
    embedder_label: str = "HashEmbeddingClient"
    reranker_label: str = "FeatureReranker"


def recall_at_k(expected: list[int], retrieved: list[int]) -> float:
    if not expected:
        return 1.0 if not retrieved else 0.0
    relevant = set(expected)
    return len(relevant & set(retrieved)) / len(relevant)


def citation_precision(expected: list[int], retrieved: list[int]) -> float:
    if not retrieved:
        return 1.0 if not expected else 0.0
    return len(set(expected) & set(retrieved)) / len(retrieved)


def load_gold(path: Path | None = None) -> dict:
    target = path or GOLD_PATH
    return json.loads(target.read_text(encoding="utf-8"))


async def index_documents(
    documents: list[dict],
    *,
    live: bool = False,
) -> KnowledgeRetriever:
    store = InMemoryChunkStore()
    embedder = get_embedding_client() if live else HashEmbeddingClient()
    reranker = get_reranker() if live else FeatureReranker()
    texts = [document["text"] for document in documents]
    vectors = await embedder.embed(texts)
    records = [
        ChunkRecord(
            document_id=document["id"],
            user_id=document["user_id"],
            agent_id=document["agent_id"],
            ordinal=0,
            text=document["text"],
            source=document["title"],
            vector=vector,
        )
        for document, vector in zip(documents, vectors)
    ]
    await store.upsert(records)
    return KnowledgeRetriever(embedder, store, reranker)


def _component_label(component: object) -> str:
    model = getattr(component, "model", None)
    if isinstance(model, str) and model.strip():
        return model.strip()
    return type(component).__name__


async def run_retrieval_eval(
    gold: dict | None = None, *, live: bool = False
) -> EvalSummary:
    payload = gold or load_gold()
    k = int(payload.get("k") or 4)
    retriever = await index_documents(payload["documents"], live=live)
    results: list[CaseResult] = []
    for case in payload["cases"]:
        hits: list[SearchHit] = await retriever.retrieve(
            case["question"],
            user_id=case["user_id"],
            agent_id=case["agent_id"],
        )
        retrieved = [hit.document_id for hit in hits[:k]]
        expected = list(case["expected_doc_ids"])
        results.append(
            CaseResult(
                case_id=case["id"],
                question=case["question"],
                expected=expected,
                retrieved=retrieved,
                recall=recall_at_k(expected, retrieved),
                precision=citation_precision(expected, retrieved),
                must_hit=bool(case.get("must_hit")),
                notes=str(case.get("notes") or ""),
            )
        )
    empty_cases = [item for item in results if not item.expected]
    hallucinated = [item for item in empty_cases if item.retrieved]
    return EvalSummary(
        k=k,
        case_count=len(results),
        recall_at_k=sum(item.recall for item in results) / len(results),
        citation_precision=sum(item.precision for item in results) / len(results),
        empty_query_hallucination=(
            len(hallucinated) / len(empty_cases) if empty_cases else 0.0
        ),
        results=results,
        embedder_label=_component_label(retriever.embedder),
        reranker_label=_component_label(retriever.reranker),
    )


def render_report(summary: EvalSummary) -> str:
    lines = [
        "# 知识库检索黄金集",
        "",
        f"- 条数：{summary.case_count}",
        f"- 向量：{summary.embedder_label}",
        f"- 重排：{summary.reranker_label}",
        f"- recall@{summary.k}：{summary.recall_at_k:.3f}",
        f"- citation precision：{summary.citation_precision:.3f}",
        f"- 空期望却检出（检索幻觉）：{summary.empty_query_hallucination:.3f}",
        "",
        "答案级幻觉（模型说了引用里没有的事实）需要 LLM-as-judge，不在本报告。",
        "",
        "| id | recall | precision | expected | retrieved | notes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in summary.results:
        lines.append(
            f"| {item.case_id} | {item.recall:.2f} | {item.precision:.2f} | "
            f"{item.expected} | {item.retrieved} | {item.notes} |"
        )
    return "\n".join(lines) + "\n"


async def _main(write_report: bool, live: bool) -> None:
    summary = await run_retrieval_eval(live=live)
    report = render_report(summary)
    print(report)
    if write_report:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(report, encoding="utf-8")
        print(f"wrote {REPORT_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument(
        "--live",
        action="store_true",
        help="use EMBEDDING_* / RERANK_* from .env instead of hash + features",
    )
    args = parser.parse_args()
    asyncio.run(_main(args.write_report, args.live))
