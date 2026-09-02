from fastapi import APIRouter, File, Form, Response, UploadFile

from app.ai.knowledge.store import get_chunk_store
from app.core.dependencies import CurrentUser, DbSession
from app.repositories.agent_repository import AgentRepository
from app.repositories.knowledge_document_repository import KnowledgeDocumentRepository
from app.schemas.knowledge import KnowledgeDocumentResponse
from app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])

service = KnowledgeService(
    KnowledgeDocumentRepository(),
    AgentRepository(),
    chunk_store=get_chunk_store(),
)


@router.post("/documents", response_model=KnowledgeDocumentResponse)
async def upload_document(
    current_user: CurrentUser,
    db: DbSession,
    agent_id: int = Form(),
    file: UploadFile = File(),
    title: str | None = Form(None),
):
    content = await file.read()
    return await service.upload(
        db,
        owner_user_id=current_user.id,
        agent_id=agent_id,
        filename=file.filename,
        content=content,
        title=title,
    )


@router.get("/documents", response_model=list[KnowledgeDocumentResponse])
async def list_documents(
    current_user: CurrentUser,
    db: DbSession,
    agent_id: int | None = None,
):
    return await service.list_documents(
        db, current_user.id, agent_id=agent_id
    )


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: int,
    current_user: CurrentUser,
    db: DbSession,
):
    await service.delete_document(
        db,
        owner_user_id=current_user.id,
        document_id=document_id,
    )
    return Response(status_code=204)
