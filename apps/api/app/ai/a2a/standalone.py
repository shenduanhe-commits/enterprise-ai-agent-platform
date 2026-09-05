"""Writer 对端进程：只挂 health + A2A 信箱，不跑 Chat / MCP。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.event_loop import use_selector_event_loop_on_windows

use_selector_event_loop_on_windows()

from app.api.v1.a2a import router as a2a_router
from app.api.v1.health import router as health_router
from app.core.exceptions import EAAPException
from app.core.logging import setup_logging
from app.handlers.exception_handler import eaap_exception_handler


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging()
    print("EAAP Writer (A2A) starting — POST /api/v1/a2a/message")
    yield
    print("EAAP Writer (A2A) shutting down...")


app = FastAPI(title="EAAP Writer (A2A)", version="1.0.0", lifespan=lifespan)
app.include_router(health_router, prefix="/api/v1")
app.include_router(a2a_router, prefix="/api/v1")
app.add_exception_handler(EAAPException, eaap_exception_handler)
