from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_document import KnowledgeDocument
from app.schemas.knowledge import KnowledgeDocumentCreate


class KnowledgeDocumentRepository:
    async def create(
        self, db: AsyncSession, document: KnowledgeDocumentCreate
    ) -> KnowledgeDocument:
        row = KnowledgeDocument(**document.model_dump())
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return row

    async def update_status(
        self,
        db: AsyncSession,
        document_id: int,
        status: str,
        error: str | None = None,
    ) -> KnowledgeDocument:
        row = await db.get(KnowledgeDocument, document_id)
        if row is None:
            raise LookupError(f"knowledge_document {document_id} not found")
        row.status = status
        row.error = error
        await db.commit()
        await db.refresh(row)
        return row

    async def list_by_owner(
        self,
        db: AsyncSession,
        owner_user_id: int,
        agent_id: int | None = None,
    ) -> list[KnowledgeDocument]:
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.owner_user_id == owner_user_id
        )
        if agent_id is not None:
            stmt = stmt.where(KnowledgeDocument.agent_id == agent_id)
        stmt = stmt.order_by(KnowledgeDocument.id.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self, db: AsyncSession) -> list[KnowledgeDocument]:
        stmt = select(KnowledgeDocument).order_by(KnowledgeDocument.id.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id_for_owner(
        self,
        db: AsyncSession,
        document_id: int,
        owner_user_id: int,
    ) -> KnowledgeDocument | None:
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.owner_user_id == owner_user_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(
        self,
        db: AsyncSession,
        document_id: int,
        owner_user_id: int,
    ) -> bool:
        row = await self.get_by_id_for_owner(db, document_id, owner_user_id)
        if row is None:
            return False
        await db.delete(row)
        await db.commit()
        return True
