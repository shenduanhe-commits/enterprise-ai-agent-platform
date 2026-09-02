from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.ai.knowledge.embedding import HashEmbeddingClient
from app.ai.knowledge.store import ChunkRecord, InMemoryChunkStore
from app.core.exceptions import BusinessException, NotFoundException
from app.schemas.knowledge import KnowledgeDocumentCreate, KnowledgeDocumentResponse
from app.services.knowledge_service import KnowledgeService


def _document(**overrides):
    data = {
        "id": 1,
        "owner_user_id": 7,
        "agent_id": 3,
        "title": "handbook",
        "source_uri": "7/abc.md",
        "status": "pending",
        "error": None,
        "created_at": datetime.now(timezone.utc),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


class FakeAgentRepository:
    def __init__(self, agent=None):
        self.agent = agent
        self.calls = []

    async def get_by_id(self, db, agent_id, user_id):
        self.calls.append((agent_id, user_id))
        return self.agent


class FakeKnowledgeRepository:
    def __init__(self, document=None, documents=None):
        self.document = document
        self.documents = documents or []
        self.create_calls = []
        self.update_calls = []
        self.list_calls = []
        self.get_calls = []
        self.delete_calls = []

    async def create(self, db, document: KnowledgeDocumentCreate):
        self.create_calls.append(document)
        return self.document

    async def update_status(self, db, document_id, status, error=None):
        self.update_calls.append((document_id, status, error))
        self.document.status = status
        self.document.error = error
        return self.document

    async def list_by_owner(self, db, owner_user_id, agent_id=None):
        self.list_calls.append((owner_user_id, agent_id))
        return self.documents

    async def list_all(self, db):
        if self.documents:
            return self.documents
        if self.document:
            return [self.document]
        return []

    async def get_by_id_for_owner(self, db, document_id, owner_user_id):
        self.get_calls.append((document_id, owner_user_id))
        if (
            self.document
            and self.document.id == document_id
            and self.document.owner_user_id == owner_user_id
        ):
            return self.document
        return None

    async def delete(self, db, document_id, owner_user_id):
        self.delete_calls.append((document_id, owner_user_id))
        return True


class BoomStore:
    async def upsert(self, records):
        raise RuntimeError("qdrant down")


def _service(repository, agent_repository, upload_dir=None, chunk_store=None):
    return KnowledgeService(
        repository,
        agent_repository,
        upload_dir=upload_dir,
        embedder=HashEmbeddingClient(),
        chunk_store=chunk_store or InMemoryChunkStore(),
    )


@pytest.mark.asyncio
async def test_upload_chunks_and_marks_ready(tmp_path: Path):
    agent = SimpleNamespace(id=3, created_by=7)
    saved = _document()
    store = InMemoryChunkStore()
    service = _service(
        FakeKnowledgeRepository(document=saved),
        FakeAgentRepository(agent=agent),
        upload_dir=tmp_path,
        chunk_store=store,
    )

    result = await service.upload(
        None,
        owner_user_id=7,
        agent_id=3,
        filename="handbook.md",
        content=b"# leave policy\nAnnual leave is 15 days.\n",
        title=None,
    )

    assert isinstance(result, KnowledgeDocumentResponse)
    assert result.status == "ready"
    created = service.repository.create_calls[0]
    assert created.owner_user_id == 7
    assert created.agent_id == 3
    assert created.title == "handbook"
    assert created.status == "pending"
    assert service.repository.update_calls == [(1, "ready", None)]
    written = list(tmp_path.glob("7/*.md"))
    assert len(written) == 1
    assert len(store.records) == 1
    chunk = store.records[0]
    assert chunk.document_id == 1
    assert chunk.user_id == 7
    assert chunk.agent_id == 3
    assert "leave policy" in chunk.text
    assert len(chunk.vector) == 64


@pytest.mark.asyncio
async def test_upload_pdf_is_indexed(tmp_path: Path):
    from tests.test_parser import _pdf_bytes

    store = InMemoryChunkStore()
    service = _service(
        FakeKnowledgeRepository(document=_document(source_uri="7/abc.pdf")),
        FakeAgentRepository(agent=SimpleNamespace(id=3, created_by=7)),
        upload_dir=tmp_path,
        chunk_store=store,
    )

    result = await service.upload(
        None,
        owner_user_id=7,
        agent_id=3,
        filename="handbook.pdf",
        content=_pdf_bytes("Annual leave is 15 days."),
    )

    assert result.status == "ready"
    assert list(tmp_path.glob("7/*.pdf"))
    assert "15 days" in store.records[0].text


@pytest.mark.asyncio
async def test_upload_docx_is_indexed(tmp_path: Path):
    from tests.test_parser import _docx_bytes

    store = InMemoryChunkStore()
    service = _service(
        FakeKnowledgeRepository(document=_document(source_uri="7/abc.docx")),
        FakeAgentRepository(agent=SimpleNamespace(id=3, created_by=7)),
        upload_dir=tmp_path,
        chunk_store=store,
    )

    result = await service.upload(
        None,
        owner_user_id=7,
        agent_id=3,
        filename="handbook.docx",
        content=_docx_bytes("年假为 15 天。"),
    )

    assert result.status == "ready"
    assert list(tmp_path.glob("7/*.docx"))
    assert "年假为 15 天" in store.records[0].text


@pytest.mark.asyncio
async def test_upload_marks_failed_when_text_empty(tmp_path: Path):
    store = InMemoryChunkStore()
    service = _service(
        FakeKnowledgeRepository(document=_document()),
        FakeAgentRepository(agent=SimpleNamespace(id=3, created_by=7)),
        upload_dir=tmp_path,
        chunk_store=store,
    )

    result = await service.upload(
        None,
        owner_user_id=7,
        agent_id=3,
        filename="empty.md",
        content=b"\n\n  \n",
    )

    assert result.status == "failed"
    assert result.error == "文档没有可索引的文本"
    assert store.records == []


@pytest.mark.asyncio
async def test_upload_marks_failed_when_store_raises(tmp_path: Path):
    service = _service(
        FakeKnowledgeRepository(document=_document()),
        FakeAgentRepository(agent=SimpleNamespace(id=3, created_by=7)),
        upload_dir=tmp_path,
        chunk_store=BoomStore(),
    )

    result = await service.upload(
        None,
        owner_user_id=7,
        agent_id=3,
        filename="handbook.md",
        content=b"# leave\n",
    )

    assert result.status == "failed"
    assert "qdrant down" in result.error
    assert result.status != "pending"


@pytest.mark.asyncio
async def test_upload_rejects_non_markdown(tmp_path: Path):
    service = _service(
        FakeKnowledgeRepository(),
        FakeAgentRepository(agent=SimpleNamespace(id=1)),
        upload_dir=tmp_path,
    )

    with pytest.raises(BusinessException, match="只支持"):
        await service.upload(
            None,
            owner_user_id=1,
            agent_id=1,
            filename="notes.txt",
            content=b"hello",
        )
    assert service.repository.create_calls == []


@pytest.mark.asyncio
async def test_upload_rejects_unowned_agent(tmp_path: Path):
    service = _service(
        FakeKnowledgeRepository(),
        FakeAgentRepository(agent=None),
        upload_dir=tmp_path,
    )

    with pytest.raises(NotFoundException, match="智能体不存在"):
        await service.upload(
            None,
            owner_user_id=2,
            agent_id=9,
            filename="handbook.md",
            content=b"# hi\n",
        )


@pytest.mark.asyncio
async def test_list_documents_uses_current_user_id():
    owned = _document(owner_user_id=4)
    repo = FakeKnowledgeRepository(documents=[owned])
    service = _service(repo, FakeAgentRepository())

    result = await service.list_documents(None, owner_user_id=4, agent_id=3)

    assert repo.list_calls == [(4, 3)]
    assert result[0].owner_user_id == 4


@pytest.mark.asyncio
async def test_delete_document_removes_file_and_chunks(tmp_path: Path):
    store = InMemoryChunkStore()
    saved = _document(status="ready", source_uri="7/abc.md")
    file_path = tmp_path / "7" / "abc.md"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("# leave\n", encoding="utf-8")
    await store.upsert(
        [
            ChunkRecord(
                document_id=1,
                user_id=7,
                agent_id=3,
                ordinal=0,
                text="年假为 15 天。",
                source="handbook",
                vector=[0.1] * 64,
            ),
            ChunkRecord(
                document_id=2,
                user_id=7,
                agent_id=3,
                ordinal=0,
                text="病假 5 天。",
                source="other",
                vector=[0.2] * 64,
            ),
        ]
    )
    service = _service(
        FakeKnowledgeRepository(document=saved),
        FakeAgentRepository(),
        upload_dir=tmp_path,
        chunk_store=store,
    )

    await service.delete_document(None, owner_user_id=7, document_id=1)

    assert service.repository.delete_calls == [(1, 7)]
    assert not file_path.exists()
    assert [record.document_id for record in store.records] == [2]


@pytest.mark.asyncio
async def test_delete_rejects_unowned_document(tmp_path: Path):
    store = InMemoryChunkStore()
    owned_by_other = _document(owner_user_id=9)
    service = _service(
        FakeKnowledgeRepository(document=owned_by_other),
        FakeAgentRepository(),
        upload_dir=tmp_path,
        chunk_store=store,
    )

    with pytest.raises(NotFoundException, match="文档不存在"):
        await service.delete_document(None, owner_user_id=7, document_id=1)

    assert service.repository.delete_calls == []
    assert store.records == []


@pytest.mark.asyncio
async def test_delete_does_not_remove_row_when_store_fails(tmp_path: Path):
    class BoomDeleteStore(InMemoryChunkStore):
        async def delete_by_document(self, document_id, *, user_id):
            raise RuntimeError("qdrant down")

    service = _service(
        FakeKnowledgeRepository(document=_document()),
        FakeAgentRepository(),
        upload_dir=tmp_path,
        chunk_store=BoomDeleteStore(),
    )

    with pytest.raises(RuntimeError, match="qdrant down"):
        await service.delete_document(None, owner_user_id=7, document_id=1)

    assert service.repository.delete_calls == []


@pytest.mark.asyncio
async def test_reindex_from_disk_rebuilds_vectors(tmp_path: Path):
    store = InMemoryChunkStore()
    saved = _document(status="ready", source_uri="7/abc.md")
    file_path = tmp_path / "7" / "abc.md"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("# 年假\n年假为 15 天。\n", encoding="utf-8")
    service = _service(
        FakeKnowledgeRepository(document=saved),
        FakeAgentRepository(),
        upload_dir=tmp_path,
        chunk_store=store,
    )

    result = await service.reindex_from_disk(None, saved)

    assert result.status == "ready"
    assert store.records
    assert "15" in store.records[0].text


@pytest.mark.asyncio
async def test_reindex_marks_failed_when_file_missing(tmp_path: Path):
    store = InMemoryChunkStore()
    saved = _document(source_uri="7/missing.md")
    service = _service(
        FakeKnowledgeRepository(document=saved),
        FakeAgentRepository(),
        upload_dir=tmp_path,
        chunk_store=store,
    )

    result = await service.reindex_from_disk(None, saved)

    assert result.status == "failed"
    assert "找不到原文件" in result.error
    assert store.records == []
