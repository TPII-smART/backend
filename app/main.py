"""FastAPI application main module."""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from app.models import GeminiRequest, GeminiResponse
from app.database import get_db, init_db, GeminiCache
from app.redis_client import redis_client
from app.gemini_service import gemini_service
from app.config import settings


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


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "message": "Gemini API Service",
        "status": "running",
        "docs": "/docs"
    }


@app.post(
    "/gemini",
    response_model=GeminiResponse,
    summary="Call Gemini API with caching",
    description="Sends a request to Gemini API. Responses are cached in Redis and PostgreSQL to avoid overcalling the API."
)
async def call_gemini(
    request: GeminiRequest,
    db: Session = Depends(get_db)
) -> GeminiResponse:
    """
    Call Gemini API with caching mechanism.
    
    First checks Redis cache, then PostgreSQL, and finally calls the API if not cached.
    
    Args:
        request: Request body with hash and expected fields
        db: Database session dependency
        
    Returns:
        GeminiResponse with the API response and cache status
    """
    hash_key = request.hash
    
    # Check Redis cache first (fastest)
    cached_data = redis_client.get_cache(hash_key)
    if cached_data:
        return GeminiResponse(
            hash=request.hash,
            expected=request.expected,
            response=cached_data["response"],
            cached=True
        )
    
    # Check PostgreSQL cache (persistent storage)
    db_cache = db.query(GeminiCache).filter(
        GeminiCache.hash == hash_key,
        GeminiCache.expected == request.expected
    ).first()
    
    if db_cache:
        # Store in Redis for faster subsequent access
        cache_data = {"response": db_cache.response}
        redis_client.set_cache(hash_key, cache_data)
        
        return GeminiResponse(
            hash=request.hash,
            expected=request.expected,
            response=db_cache.response,
            cached=True
        )
    
    # Not in cache, call Gemini API
    try:
        gemini_response = gemini_service.generate_response(
            hash_value=request.hash,
            expected_value=request.expected
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to call Gemini API: {str(e)}"
        )
    
    # Cache the response in both Redis and PostgreSQL
    cache_data = {"response": gemini_response}
    redis_client.set_cache(hash_key, cache_data)
    
    # Store in PostgreSQL
    new_cache = GeminiCache(
        hash=hash_key,
        expected=request.expected,
        response=gemini_response
    )
    db.add(new_cache)
    db.commit()
    
    return GeminiResponse(
        hash=request.hash,
        expected=request.expected,
        response=gemini_response,
        cached=False
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
