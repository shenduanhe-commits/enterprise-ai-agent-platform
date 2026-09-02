import logging

from app.ai.knowledge.budget import fit_context_budget
from app.ai.knowledge.embedding import EmbeddingClient, get_embedding_client
from app.ai.knowledge.reranker import FeatureReranker, Reranker
from app.ai.knowledge.sparse import encode_sparse, lexical_terms
from app.ai.knowledge.store import ChunkStore, QdrantChunkStore, SearchHit
from app.core.config import settings

logger = logging.getLogger(__name__)

KNOWLEDGE_PREFIX = "【知识库】"
_CANDIDATE_LIMIT = 32
_RETURN_LIMIT = 4
_SCORE_THRESHOLD = 0.3


class KnowledgeRetriever:
    def __init__(
        self,
        embedder: EmbeddingClient | None = None,
        store: ChunkStore | None = None,
        reranker: Reranker | None = None,
    ):
        self.embedder = embedder or get_embedding_client()
        self.store = store or QdrantChunkStore(vector_size=self.embedder.size)
        self.reranker = reranker or FeatureReranker()

    async def retrieve(
        self,
        query: str,
        *,
        user_id: int,
        agent_id: int,
    ) -> list[SearchHit]:
        if not query.strip():
            return []
        try:
            vectors = await self.embedder.embed([query])
            hits = await self.store.search(
                vectors[0],
                user_id=user_id,
                agent_id=agent_id,
                limit=_CANDIDATE_LIMIT,
                sparse=encode_sparse(query),
            )
        except Exception:
            logger.exception("knowledge retrieve failed")
            return []
        if getattr(self.embedder, "use_lexical_gate", True):
            matched = [hit for hit in hits if _has_term_overlap(query, hit.text)]
        else:
            matched = [
                hit
                for hit in hits
                if hit.dense_score >= _SCORE_THRESHOLD
                or _has_term_overlap(query, hit.text)
            ]
        ranked = await self.reranker.rerank(query, matched)
        return fit_context_budget(
            ranked[:_RETURN_LIMIT],
            settings.KNOWLEDGE_CONTEXT_TOKENS,
        )


def format_knowledge_message(hits: list[SearchHit]) -> str:
    lines = [
        KNOWLEDGE_PREFIX,
        "以下摘录来自当前用户在该 Agent 下的文档。与问题无关则不要使用，不要编造未出现的制度。",
        "",
    ]
    for index, hit in enumerate(hits, start=1):
        lines.append(f"[{index}] {hit.source} (document_id={hit.document_id})")
        lines.append(hit.text)
        lines.append("")
    return "\n".join(lines).strip()


def _has_term_overlap(query: str, text: str) -> bool:
    haystack = text.lower()
    return any(term in haystack for term in lexical_terms(query))
