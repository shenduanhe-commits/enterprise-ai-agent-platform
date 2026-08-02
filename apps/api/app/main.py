from fastapi import FastAPI

from app.api import api_router
from app.core.config import settings
from app.core.lifespan import lifespan

print(settings.DATABASE_URL)
print(settings.REDIS_URL)

app = FastAPI(
    title="Enterprise AI Agent Platform API", version="1.0.0", lifespan=lifespan
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"name": "EAAP API", "version": "1.0.0", "status": "running"}
