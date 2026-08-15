from fastapi import APIRouter

from app.api.v1 import router as v1_router

router = APIRouter()
router.include_router(v1_router, prefix="/v1")  # 将 v1 路由包含在 api 路由中

__all__ = ["router"]
