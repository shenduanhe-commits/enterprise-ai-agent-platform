import hashlib
import logging
from typing import Protocol

from app.core.config import settings

logger = logging.getLogger(__name__)

HASH_VECTOR_SIZE = 64
VECTOR_SIZE = HASH_VECTOR_SIZE


class EmbeddingClient(Protocol):
    size: int
    use_lexical_gate: bool

    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashEmbeddingClient:
    """本地可复现的假向量。没配 embedding Key/模型时用；维数固定 64。"""

    size = HASH_VECTOR_SIZE
    use_lexical_gate = True

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [_hash_vector(text) for text in texts]


class OpenAICompatEmbeddingClient:
    """OpenAI 兼容 embeddings 接口。上传和检索必须共用同一个实例配置。"""

    use_lexical_gate = False

    def __init__(
        self,
        api_key: str,
        model: str,
        size: int,
        base_url: str | None = None,
    ):
        self.size = size
        self.model = model
        self._api_key = api_key
        self._base_url = base_url
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI

            kwargs: dict = {"api_key": self._api_key}
            if self._base_url:
                kwargs["base_url"] = self._base_url
            self._client = AsyncOpenAI(**kwargs)
        return self._client

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors: list[list[float]] = []
        client = self._get_client()
        batch_size = max(1, settings.EMBEDDING_BATCH)
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            response = await client.embeddings.create(
                model=self.model,
                input=batch,
                dimensions=self.size,
            )
            vectors.extend(item.embedding for item in response.data)
        return vectors


_cached_client: EmbeddingClient | None = None


def get_embedding_client() -> EmbeddingClient:
    global _cached_client
    if _cached_client is None:
        _cached_client = build_embedding_client()
    return _cached_client


def build_embedding_client() -> EmbeddingClient:
    model = (settings.EMBEDDING_MODEL or "").strip()
    api_key = (settings.EMBEDDING_API_KEY or "").strip()
    base_url = (settings.EMBEDDING_BASE_URL or "").strip() or None
    if model and api_key:
        client = OpenAICompatEmbeddingClient(
            api_key=api_key,
            base_url=base_url,
            model=model,
            size=settings.EMBEDDING_DIM,
        )
        logger.info(
            "knowledge embedding: model=%s dim=%s base_url=%s",
            client.model,
            client.size,
            base_url or "default",
        )
        return client

    logger.info("knowledge embedding: hash dim=%s", HASH_VECTOR_SIZE)
    return HashEmbeddingClient()


def _hash_vector(text: str) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    raw = (digest * ((HASH_VECTOR_SIZE // len(digest)) + 1))[:HASH_VECTOR_SIZE]
    values = [byte / 255.0 for byte in raw]
    norm = sum(value * value for value in values) ** 0.5
    if norm == 0:
        return values
    return [value / norm for value in values]
