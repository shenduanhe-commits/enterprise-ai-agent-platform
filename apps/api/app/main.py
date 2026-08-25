from fastapi import FastAPI

from app.core.event_loop import use_selector_event_loop_on_windows

use_selector_event_loop_on_windows()

from app.api import router
from app.core.exceptions import EAAPException
from app.core.lifespan import lifespan
from app.handlers.exception_handler import eaap_exception_handler

app = FastAPI(
    title="Enterprise AI Agent Platform API", version="1.0.0", lifespan=lifespan
)

app.include_router(router, prefix="/api")
app.add_exception_handler(EAAPException, eaap_exception_handler)


@app.get("/")
def root():
    return {"name": "EAAP API", "version": "1.0.0", "status": "running"}
