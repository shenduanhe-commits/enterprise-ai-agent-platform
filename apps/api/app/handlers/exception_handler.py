from app.core.exceptions import EAAPException
from fastapi import Request
from fastapi.responses import JSONResponse


async def eaap_exception_handler(request: Request, exc: EAAPException):

    return JSONResponse(
        status_code=exc.status_code, content={"code": exc.code, "message": exc.message}
    )
