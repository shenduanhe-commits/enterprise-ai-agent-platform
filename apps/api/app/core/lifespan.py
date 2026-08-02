from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    生命周期管理
    """
    setup_logging()

    print("EAAP API starting...")

    yield

    print("EAAP API shutting down...")
