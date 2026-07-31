from fastapi import FastAPI
from app.core.config import settings

print(settings.DATABASE_URL)
print(settings.REDIS_URL)

app = FastAPI(
    title="Enterprise AI Agent Platform API",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "name": "EAAP API",
        "version": "1.0.0",
        "status": "running"
    }