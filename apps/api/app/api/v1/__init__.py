from fastapi import APIRouter

from app.api.v1.agents import router as agents_router
from app.api.v1.auth import router as auth_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.health import router as health_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.runs import router as runs_router
from app.api.v1.users import router as users_router

router = APIRouter()


router.include_router(health_router)
router.include_router(users_router)
router.include_router(auth_router)
router.include_router(agents_router)
router.include_router(conversations_router)
router.include_router(runs_router)
router.include_router(knowledge_router)
