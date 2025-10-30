"""FastAPI application main module."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager

from app.database import init_db
from app.config import settings
from app.controllers import router
from app.middleware import (
    error_handler_middleware,
    validation_exception_handler,
    http_exception_handler
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup: Initialize database
    init_db()
    yield
    # Shutdown: cleanup if needed


# Create FastAPI application
app = FastAPI(
    title="Gemini API with Caching",
    description="FastAPI service that calls Gemini API with Redis and PostgreSQL caching",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
if settings.CORS_ENABLED:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=settings.CORS_CREDENTIALS,
        allow_methods=settings.cors_methods_list,
        allow_headers=settings.cors_headers_list,
    )

# Add error handling middleware
app.middleware("http")(error_handler_middleware)

# Add exception handlers for RFC 9457 compliant error responses
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)

# Include API router
app.include_router(router)
