from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.run_span_repository import RunSpanRepository
from app.schemas.run import RunSpanCreate, RunSpanResponse


class RunSpanService:
    def __init__(self, repository: RunSpanRepository):
        self.repository = repository

    async def create_span(
        self, db: AsyncSession, span_data: RunSpanCreate
    ) -> RunSpanResponse:
        span = await self.repository.create(db, span_data)
        return RunSpanResponse.model_validate(span)

    async def list_spans(
        self, db: AsyncSession, conversation_id: int
    ) -> list[RunSpanResponse]:
        spans = await self.repository.list_by_conversation_id(db, conversation_id)
        return [RunSpanResponse.model_validate(span) for span in spans]
