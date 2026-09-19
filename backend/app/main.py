import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import artifacts, chat, health, sessions
from app.config import get_settings
from app.database import close_database, create_database_schema
from app.logging_config import configure_logging
from app.providers import (
    ProviderConfigurationError,
    ProviderError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)


settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await create_database_schema()
    logger.info("application_started")
    try:
        yield
    finally:
        await close_database()
        logger.info("application_stopped")


app = FastAPI(
    title="The Lenny Growth Assistant API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin] if hasattr(settings, "frontend_origin") else ["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):  # type: ignore[no-untyped-def]
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    started_at = time.monotonic()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "api_request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round((time.monotonic() - started_at) * 1000, 2),
        },
    )
    return response


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: object | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": getattr(request.state, "request_id", None),
                "details": details or {},
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return error_response(
        request,
        422,
        "VALIDATION_ERROR",
        "The request contains invalid or missing fields.",
        exc.errors(),
    )


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
    return error_response(request, exc.status_code, code, str(exc.detail))


@app.exception_handler(ProviderError)
async def provider_error_handler(request: Request, exc: ProviderError) -> JSONResponse:
    if isinstance(exc, ProviderConfigurationError):
        status_code = 400
    elif isinstance(exc, ProviderTimeoutError):
        status_code = 504
    elif isinstance(exc, ProviderUnavailableError):
        status_code = 503
    else:
        status_code = 502
    logger.error(
        "provider_error",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "error_code": exc.code,
        },
    )
    return error_response(request, status_code, exc.code, str(exc))


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.exception(
        "unhandled_error",
        extra={"request_id": request_id, "error_code": "INTERNAL_ERROR"},
    )
    return error_response(
        request,
        500,
        "INTERNAL_ERROR",
        "An unexpected server error occurred.",
    )


app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(artifacts.router)

