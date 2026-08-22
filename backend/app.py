from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from models.schemas import ErrorResponse, HealthResponse
from routes import rag, voice, analytics
from services.config import get_settings
from services.exceptions import AppError
from services.limiter import limiter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="HH Goa 2026 — Voice-Enabled RAG API",
    description="Voice-Enabled Retrieval-Augmented Generation pipeline with Sarvam STT, MSMARCO-XI hybrid search, and latency analytics.",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    logger.warning("%s: %s", exc.error_type, exc.message)
    payload = ErrorResponse(detail=exc.message, error_type=exc.error_type)
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    first_error = exc.errors()[0] if exc.errors() else {}
    location = ".".join(str(part) for part in first_error.get("loc", []) if part != "body")
    message = first_error.get("msg", "Invalid request.")
    detail = f"{location}: {message}" if location else message
    payload = ErrorResponse(detail=detail, error_type="validation_error")
    return JSONResponse(status_code=422, content=payload.model_dump())


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    payload = ErrorResponse(detail=str(exc.detail), error_type="http_error")
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled API error: %s", exc)
    payload = ErrorResponse(detail="Internal server error.", error_type="internal_server_error")
    return JSONResponse(status_code=500, content=payload.model_dump())


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    settings = get_settings()
    groq_configured = bool(settings.groq_api_key)
    sarvam_configured = bool(settings.sarvam_api_key)
    return HealthResponse(
        status="ok" if (groq_configured or sarvam_configured) else "degraded",
        checks={
            "api": "ok",
            "groq_configured": groq_configured,
            "sarvam_configured": sarvam_configured,
            "target_latency_ms": settings.target_latency_ms,
        },
    )


@app.on_event("startup")
async def startup_event() -> None:
    from rag.orchestrator import orchestrator
    logger.info("Running system warmup...")
    await orchestrator.generator.llm_service.warmup()
    await orchestrator.stt_service.warmup()

# Mount routers
app.include_router(rag.router)
app.include_router(voice.router)
app.include_router(analytics.router)
