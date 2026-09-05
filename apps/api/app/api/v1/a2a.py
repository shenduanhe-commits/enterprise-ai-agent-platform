import logging

from fastapi import APIRouter, Request

from app.ai.a2a.client import A2A_KEY_HEADER
from app.ai.a2a.protocol import A2AMessage, A2AReply
from app.ai.a2a.writer import write_brief
from app.ai.dependencies import get_llm_gateway
from app.core.config import settings
from app.core.exceptions import UnauthorizedException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/a2a", tags=["A2A"])


@router.post("/message", response_model=A2AReply)
async def a2a_message(body: A2AMessage, request: Request):
    expected = settings.A2A_INTERNAL_KEY or ""
    if not expected or request.headers.get(A2A_KEY_HEADER) != expected:
        raise UnauthorizedException("A2A 未授权")
    logger.info(
        "A2A inbox from=%s to=%s task_id=%s",
        body.from_agent,
        body.to_agent,
        body.task_id,
    )
    if body.to_agent != "writer":
        return A2AReply(
            from_agent="writer",
            task_id=body.task_id,
            content=f"unknown agent {body.to_agent}",
            status="failed",
        )
    meta = body.metadata or {}
    try:
        text = await write_brief(
            get_llm_gateway(),
            provider=str(meta.get("provider") or "mock"),
            model=str(meta.get("model") or "mock-model"),
            user_message=str(meta.get("user_message") or ""),
            notes=body.content,
        )
    except Exception as exc:  # noqa: BLE001 — 对端失败要回 envelope，不能 500 冒充协议成功
        return A2AReply(
            from_agent="writer",
            task_id=body.task_id,
            content=str(exc),
            status="failed",
        )
    return A2AReply(
        from_agent="writer",
        task_id=body.task_id,
        content=text,
        status="completed",
    )
