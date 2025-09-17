# app/core/errors.py
from typing import Any, Optional, Dict
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR
from fastapi.exceptions import RequestValidationError

from app.core.logger import get_logger
log = get_logger(__name__)

class ApiError(BaseModel):
    error: str
    message: str
    details: Optional[Any] = None

def error_response(status_code: int, error: str, message: str, details: Any = None) -> JSONResponse:
    payload = ApiError(error=error, message=message, details=details).model_dump()
    return JSONResponse(status_code=status_code, content=payload)

async def http_exception_handler(request: Request, exc: HTTPException):
    # Normalize all HTTPExceptions into {error, message, details}
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail and "message" in detail:
        payload = detail
    else:
        payload = {
            "error": getattr(exc, "name", "HTTPError"),
            "message": str(detail),
            "details": None,
        }
    log.warning("HTTPException", extra={"path": request.url.path, "status": exc.status_code, "payload": payload})
    return JSONResponse(status_code=exc.status_code, content=payload)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    payload = {
        "error": "ValidationError",
        "message": "Request validation failed",
        "details": exc.errors(),
    }
    log.warning("ValidationError", extra={"path": request.url.path, "details": exc.errors()})
    return JSONResponse(status_code=HTTP_422_UNPROCESSABLE_ENTITY, content=payload)

async def generic_exception_handler(request: Request, exc: Exception):
    payload = {
        "error": "InternalServerError",
        "message": "An unexpected error occurred",
        "details": None,
    }
    log.error("Unhandled exception", extra={"path": request.url.path}, exc_info=exc)
    return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content=payload)

