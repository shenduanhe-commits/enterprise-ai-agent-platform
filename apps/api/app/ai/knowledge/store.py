import logging
from dataclasses import dataclass, field, replace
from typing import Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from app.ai.knowledge.embedding import HASH_VECTOR_SIZE
from app.ai.knowledge.sparse import SparseVectorData, encode_sparse, rrf_scores, sparse_dot
from app.core.config import settings

logger = logging.getLogger(__name__)

COLLECTION = "eaap_chunks"
DENSE_VECTOR = "dense"
SPARSE_VECTOR = "sparse"


def chunk_point_id(document_id: int, ordinal: int) -> UUID:
    return uuid5(NAMESPACE_URL, f"{document_id}:{ordinal}")


@dataclass
class ChunkRecord:
    document_id: int
    user_id: int
    agent_id: int
    ordinal: int
    text: str
    source: str
    vector: list[float]
    sparse_indices: list[int] = field(default_factory=list)
    sparse_values: list[float] = field(default_factory=list)


@dataclass
class SearchHit:
    document_id: int
    user_id: int
    agent_id: int
    ordinal: int
    text: str
    source: str
    score: float
    chunk_id: str
    dense_score: float = 0.0


class ChunkStore(Protocol):
    async def upsert(self, records: list[ChunkRecord]) -> None: ...

    async def search(
        self,
        vector: list[float],
        *,
        user_id: int,
        agent_id: int,
        limit: int = 8,
        sparse: SparseVectorData | None = None,
    ) -> list[SearchHit]: ...

    async def delete_by_document(self, document_id: int, *, user_id: int) -> None: ...


class InMemoryChunkStore:
    def __init__(self):
        self.records: list[ChunkRecord] = []

    async def upsert(self, records: list[ChunkRecord]) -> None:
        incoming = {(record.document_id, record.ordinal) for record in records}
        self.records = [
            record
            for record in self.records
            if (record.document_id, record.ordinal) not in incoming
        ]
        self.records.extend(_with_sparse(record) for record in records)

    async def search(
        self,
        vector: list[float],
        *,
        user_id: int,
        agent_id: int,
        limit: int = 8,
        sparse: SparseVectorData | None = None,
    ) -> list[SearchHit]:
        scoped = [
            record
            for record in self.records
            if record.user_id == user_id and record.agent_id == agent_id
        ]
        dense_hits = [
            _hit_from_record(
                record,
                score=_cosine(vector, record.vector),
                dense_score=_cosine(vector, record.vector),
            )
            for record in scoped
        ]
        dense_hits.sort(key=lambda hit: hit.score, reverse=True)
        if sparse is None or sparse.is_empty():
            return dense_hits[:limit]
        sparse_hits: list[SearchHit] = []
        for record in scoped:
            score = sparse_dot(sparse, _sparse_of(record))
            if score <= 0:
                continue
            sparse_hits.append(_hit_from_record(record, score=score, dense_score=0.0))
        sparse_hits.sort(key=lambda hit: hit.score, reverse=True)
        return _fuse_hits(dense_hits, sparse_hits, limit=limit)

    async def delete_by_document(self, document_id: int, *, user_id: int) -> None:
        self.records = [
            record
            for record in self.records
            if not (record.document_id == document_id and record.user_id == user_id)
        ]


class QdrantChunkStore:
    def __init__(self, url: str | None = None, vector_size: int | None = None):
        self._url = url or settings.QDRANT_URL
        self._vector_size = vector_size or HASH_VECTOR_SIZE
        self._client = None

    def _get_client(self):
        if self._client is None:
            from qdrant_client import AsyncQdrantClient

            self._client = AsyncQdrantClient(url=self._url)
        return self._client

    async def ensure_collection(self) -> bool:
        client = self._get_client()
        existing = await client.get_collections()
        names = {item.name for item in existing.collections}
        if COLLECTION in names:
            info = await client.get_collection(COLLECTION)
            if _hybrid_schema_ok(info, self._vector_size):
                return False
            logger.warning(
                "recreating %s for hybrid schema (dense size %s); will reindex from disk",
                COLLECTION,
                self._vector_size,
            )
            await client.delete_collection(COLLECTION)
        await self._create_collection(client)
        return True

    async def _create_collection(self, client) -> None:
        from qdrant_client.models import Distance, Modifier, SparseVectorParams, VectorParams

        await client.create_collection(
            collection_name=COLLECTION,
            vectors_config={
                DENSE_VECTOR: VectorParams(
                    size=self._vector_size, distance=Distance.COSINE
                )
            },
            sparse_vectors_config={
                SPARSE_VECTOR: SparseVectorParams(modifier=Modifier.IDF)
            },
        )

    async def upsert(self, records: list[ChunkRecord]) -> None:
        from qdrant_client.models import PointStruct, SparseVector

        await self.ensure_collection()
        points = []
        for record in records:
            prepared = _with_sparse(record)
            points.append(
                PointStruct(
                    id=chunk_point_id(prepared.document_id, prepared.ordinal),
                    vector={
                        DENSE_VECTOR: prepared.vector,
                        SPARSE_VECTOR: SparseVector(
                            indices=prepared.sparse_indices,
                            values=prepared.sparse_values,
                        ),
                    },
                    payload={
                        "document_id": prepared.document_id,
                        "user_id": prepared.user_id,
                        "agent_id": prepared.agent_id,
                        "ordinal": prepared.ordinal,
                        "text": prepared.text,
                        "source": prepared.source,
                    },
                )
            )
        await self._get_client().upsert(collection_name=COLLECTION, points=points)

    async def search(
        self,
        vector: list[float],
        *,
        user_id: int,
        agent_id: int,
        limit: int = 8,
        sparse: SparseVectorData | None = None,
    ) -> list[SearchHit]:
        await self.ensure_collection()
        dense_hits = await self._query_dense(vector, user_id=user_id, agent_id=agent_id, limit=limit)
        if sparse is None or sparse.is_empty():
            return dense_hits
        sparse_hits = await self._query_sparse(
            sparse, user_id=user_id, agent_id=agent_id, limit=limit
        )
        return _fuse_hits(dense_hits, sparse_hits, limit=limit)

    async def _query_dense(
        self, vector: list[float], *, user_id: int, agent_id: int, limit: int
    ) -> list[SearchHit]:
        response = await self._get_client().query_points(
            collection_name=COLLECTION,
            query=vector,
            using=DENSE_VECTOR,
            limit=limit,
            query_filter=_owner_filter(user_id, agent_id),
            with_payload=True,
        )
        return [_hit_from_point(point) for point in response.points]

    async def _query_sparse(
        self,
        sparse: SparseVectorData,
        *,
        user_id: int,
        agent_id: int,
        limit: int,
    ) -> list[SearchHit]:
        from qdrant_client.models import SparseVector

        response = await self._get_client().query_points(
            collection_name=COLLECTION,
            query=SparseVector(indices=sparse.indices, values=sparse.values),
            using=SPARSE_VECTOR,
            limit=limit,
            query_filter=_owner_filter(user_id, agent_id),
            with_payload=True,
        )
        return [_hit_from_point(point) for point in response.points]

    async def delete_by_document(self, document_id: int, *, user_id: int) -> None:
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        await self.ensure_collection()
        await self._get_client().delete(
            collection_name=COLLECTION,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id", match=MatchValue(value=document_id)
                    ),
                    FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                ]
            ),
        )


def _owner_filter(user_id: int, agent_id: int):
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    return Filter(
        must=[
            FieldCondition(key="user_id", match=MatchValue(value=user_id)),
            FieldCondition(key="agent_id", match=MatchValue(value=agent_id)),
        ]
    )


def _with_sparse(record: ChunkRecord) -> ChunkRecord:
    if record.sparse_indices:
        return record
    encoded = encode_sparse(record.text)
    return replace(
        record,
        sparse_indices=encoded.indices,
        sparse_values=encoded.values,
    )


def _sparse_of(record: ChunkRecord) -> SparseVectorData:
    return SparseVectorData(indices=record.sparse_indices, values=record.sparse_values)


def _hit_from_record(
    record: ChunkRecord, *, score: float, dense_score: float
) -> SearchHit:
    return SearchHit(
        document_id=record.document_id,
        user_id=record.user_id,
        agent_id=record.agent_id,
        ordinal=record.ordinal,
        text=record.text,
        source=record.source,
        score=score,
        chunk_id=str(chunk_point_id(record.document_id, record.ordinal)),
        dense_score=dense_score,
    )


def _hit_from_point(point) -> SearchHit:
    payload = point.payload or {}
    score = float(point.score or 0.0)
    return SearchHit(
        document_id=int(payload["document_id"]),
        user_id=int(payload["user_id"]),
        agent_id=int(payload["agent_id"]),
        ordinal=int(payload["ordinal"]),
        text=str(payload.get("text") or ""),
        source=str(payload.get("source") or ""),
        score=score,
        chunk_id=str(point.id),
        dense_score=score,
    )


def _fuse_hits(
    dense_hits: list[SearchHit],
    sparse_hits: list[SearchHit],
    *,
    limit: int,
) -> list[SearchHit]:
    scores = rrf_scores(
        [hit.chunk_id for hit in dense_hits],
        [hit.chunk_id for hit in sparse_hits],
    )
    payloads = {hit.chunk_id: hit for hit in sparse_hits}
    payloads.update({hit.chunk_id: hit for hit in dense_hits})
    dense_scores = {hit.chunk_id: hit.dense_score for hit in dense_hits}
    fused = [
        replace(
            payloads[chunk_id],
            score=score,
            dense_score=dense_scores.get(chunk_id, 0.0),
        )
        for chunk_id, score in scores.items()
    ]
    fused.sort(key=lambda hit: hit.score, reverse=True)
    return fused[:limit]


def _hybrid_schema_ok(info, vector_size: int) -> bool:
    params = info.config.params
    vectors = params.vectors
    if getattr(vectors, "size", None) is not None:
        return False
    dense = _mapping_get(vectors, DENSE_VECTOR)
    size = int(getattr(dense, "size", 0) or 0)
    if size != vector_size:
        return False
    sparse = params.sparse_vectors
    return _mapping_get(sparse, SPARSE_VECTOR) is not None


def _mapping_get(container, key):
    if container is None:
        return None
    if isinstance(container, dict):
        return container.get(key)
    getter = getattr(container, "get", None)
    if callable(getter):
        return getter(key)
    try:
        return container[key]
    except (KeyError, TypeError, IndexError):
        return None


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True))


_cached_store: QdrantChunkStore | None = None


def get_chunk_store() -> QdrantChunkStore:
    global _cached_store
    if _cached_store is None:
        from app.ai.knowledge.embedding import get_embedding_client

        _cached_store = QdrantChunkStore(vector_size=get_embedding_client().size)
    return _cached_store
