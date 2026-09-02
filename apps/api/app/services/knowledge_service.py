import asyncio
import logging
from pathlib import Path
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.knowledge.chunker import chunk_markdown
from app.ai.knowledge.embedding import EmbeddingClient, get_embedding_client
from app.ai.knowledge.parser import extract_text, supported_suffix
from app.ai.knowledge.store import ChunkRecord, ChunkStore, QdrantChunkStore
from app.core.config import settings
from app.core.exceptions import BusinessException, NotFoundException
from app.models.knowledge_document import KnowledgeDocumentStatus
from app.repositories.agent_repository import AgentRepository
from app.repositories.knowledge_document_repository import KnowledgeDocumentRepository
from app.schemas.knowledge import KnowledgeDocumentCreate, KnowledgeDocumentResponse

_MAX_UPLOAD_BYTES = 2 * 1024 * 1024
_MAX_ERROR_CHARS = 2000

logger = logging.getLogger(__name__)


class KnowledgeService:
    def __init__(
        self,
        repository: KnowledgeDocumentRepository,
        agent_repository: AgentRepository,
        upload_dir: Path | None = None,
        embedder: EmbeddingClient | None = None,
        chunk_store: ChunkStore | None = None,
    ):
        self.repository = repository
        self.agent_repository = agent_repository
        self.upload_dir = upload_dir or Path(settings.KNOWLEDGE_UPLOAD_DIR)
        self.embedder = embedder or get_embedding_client()
        self.chunk_store = chunk_store or QdrantChunkStore(
            vector_size=self.embedder.size
        )

    async def upload(
        self,
        db: AsyncSession,
        *,
        owner_user_id: int,
        agent_id: int,
        filename: str | None,
        content: bytes,
        title: str | None = None,
    ) -> KnowledgeDocumentResponse:
        agent = await self.agent_repository.get_by_id(db, agent_id, owner_user_id)
        if agent is None:
            raise NotFoundException("智能体不存在")

        suffix = supported_suffix(filename)
        if suffix is None:
            raise BusinessException("只支持 Markdown（.md）、PDF（.pdf）、Word（.docx）")
        if not content:
            raise BusinessException("文件不能为空")
        if len(content) > _MAX_UPLOAD_BYTES:
            raise BusinessException("文件过大")

        relative = f"{owner_user_id}/{uuid4().hex}{suffix}"
        destination = self.upload_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(destination.write_bytes, content)

        display_title = (title or Path(filename or "").stem).strip() or "untitled"
        row = await self.repository.create(
            db,
            KnowledgeDocumentCreate(
                owner_user_id=owner_user_id,
                agent_id=agent_id,
                title=display_title,
                source_uri=relative.replace("\\", "/"),
                status=KnowledgeDocumentStatus.PENDING.value,
            ),
        )
        return await self._ingest(db, row, filename=filename or relative, content=content)

    async def list_documents(
        self,
        db: AsyncSession,
        owner_user_id: int,
        agent_id: int | None = None,
    ) -> list[KnowledgeDocumentResponse]:
        rows = await self.repository.list_by_owner(db, owner_user_id, agent_id=agent_id)
        return [KnowledgeDocumentResponse.model_validate(row) for row in rows]

    async def delete_document(
        self,
        db: AsyncSession,
        *,
        owner_user_id: int,
        document_id: int,
    ) -> None:
        row = await self.repository.get_by_id_for_owner(
            db, document_id, owner_user_id
        )
        if row is None:
            raise NotFoundException("文档不存在")

        await self.chunk_store.delete_by_document(row.id, user_id=owner_user_id)
        await self._delete_file(row.source_uri)
        deleted = await self.repository.delete(db, document_id, owner_user_id)
        if not deleted:
            raise NotFoundException("文档不存在")

    async def _delete_file(self, source_uri: str) -> None:
        relative = Path(source_uri)
        if relative.is_absolute() or ".." in relative.parts:
            logger.warning("skip deleting unsafe source_uri=%s", source_uri)
            return
        destination = self.upload_dir / relative
        await asyncio.to_thread(_unlink_if_exists, destination)

    async def reindex_all(self, db: AsyncSession) -> int:
        rows = await self.repository.list_all(db)
        rebuilt = 0
        for row in rows:
            result = await self.reindex_from_disk(db, row)
            if result.status == KnowledgeDocumentStatus.READY.value:
                rebuilt += 1
        logger.info("knowledge reindex finished: %s/%s ready", rebuilt, len(rows))
        return rebuilt

    async def reindex_from_disk(self, db: AsyncSession, row) -> KnowledgeDocumentResponse:
        content = await asyncio.to_thread(self._read_source_bytes, row.source_uri)
        if content is None:
            updated = await self.repository.update_status(
                db,
                row.id,
                KnowledgeDocumentStatus.FAILED.value,
                "磁盘上找不到原文件，无法重建向量",
            )
            return KnowledgeDocumentResponse.model_validate(updated)
        filename = Path(row.source_uri).name
        return await self._ingest(db, row, filename=filename, content=content)

    def _read_source_bytes(self, source_uri: str) -> bytes | None:
        relative = Path(source_uri)
        if relative.is_absolute() or ".." in relative.parts:
            logger.warning("skip reading unsafe source_uri=%s", source_uri)
            return None
        destination = self.upload_dir / relative
        if not destination.is_file():
            return None
        return destination.read_bytes()

    async def _ingest(
        self,
        db: AsyncSession,
        row,
        *,
        filename: str,
        content: bytes,
    ) -> KnowledgeDocumentResponse:
        try:
            text = extract_text(filename, content)
            chunks = chunk_markdown(text)
            if not chunks:
                updated = await self.repository.update_status(
                    db,
                    row.id,
                    KnowledgeDocumentStatus.FAILED.value,
                    "文档没有可索引的文本",
                )
                return KnowledgeDocumentResponse.model_validate(updated)

            vectors = await self.embedder.embed(chunks)
            records = [
                ChunkRecord(
                    document_id=row.id,
                    user_id=row.owner_user_id,
                    agent_id=row.agent_id,
                    ordinal=index,
                    text=chunk,
                    source=row.title,
                    vector=vector,
                )
                for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True))
            ]
            await self.chunk_store.upsert(records)
            updated = await self.repository.update_status(
                db,
                row.id,
                KnowledgeDocumentStatus.READY.value,
                None,
            )
            return KnowledgeDocumentResponse.model_validate(updated)
        except UnicodeDecodeError:
            logger.exception("knowledge ingest failed for document %s", row.id)
            updated = await self.repository.update_status(
                db,
                row.id,
                KnowledgeDocumentStatus.FAILED.value,
                "文件不是 UTF-8 文本",
            )
            return KnowledgeDocumentResponse.model_validate(updated)
        except Exception as exc:
            logger.exception("knowledge ingest failed for document %s", row.id)
            updated = await self.repository.update_status(
                db,
                row.id,
                KnowledgeDocumentStatus.FAILED.value,
                str(exc)[:_MAX_ERROR_CHARS],
            )
            return KnowledgeDocumentResponse.model_validate(updated)


def _unlink_if_exists(path: Path) -> None:
    if path.is_file():
        path.unlink()
