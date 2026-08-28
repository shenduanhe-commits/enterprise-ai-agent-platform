from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run_span import RunSpan
from app.schemas.run import RunSpanCreate


class RunSpanRepository:
    async def create(self, db: AsyncSession, span: RunSpanCreate) -> RunSpan:
        db_span = RunSpan(**span.model_dump())
        db.add(db_span)
        await db.commit()
        await db.refresh(db_span)
        return db_span

    async def list_by_conversation_id(
        self,
        db: AsyncSession,
        conversation_id: int,
    ) -> list[RunSpan]:
        stmt = (
            select(RunSpan)
            .where(RunSpan.conversation_id == conversation_id)
            .order_by(RunSpan.started_at.asc(), RunSpan.id.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
