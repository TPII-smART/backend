"""API endpoint controllers."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models import GeminiRequest, GeminiResponse
from app.database import get_db, GeminiCache
from app.redis_client import redis_client
from app.gemini_service import gemini_service
from sqlalchemy import select

# Create API router
router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "message": "Gemini API Service",
        "status": "running",
        "docs": "/docs"
    }


@router.post(
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
        GeminiResponse with badge classification and details
    """
    hash_keys = [h.replace("ipfs://", "") for h in request.hashes]
    work_id = request.workId

    # Check Redis cache first (fastest)
    cached_data = await redis_client.get_cache(work_id)
    if cached_data:
        return GeminiResponse(
            badge=cached_data["badge"],
            details=cached_data["details"]
        )

    # Check PostgreSQL cache (persistent storage)
    stmt = select(GeminiCache).where(GeminiCache.id == work_id)
    db_cache = db.execute(stmt).first()

    if db_cache:
        db_cache = db_cache[0]  # Unwrap from SQLAlchemy Row
        # Store in Redis for faster subsequent access
        cache_data = {
            "badge": db_cache.badge,
            "details": db_cache.details
        }
        await redis_client.set_cache(work_id, cache_data)

        return GeminiResponse(
            badge=db_cache.badge,  # type: ignore
            details=db_cache.details  # type: ignore
        )

    # Not in cache, call Gemini API
    try:
        badge, details = await gemini_service.generate_response(
            hashes=hash_keys,
            expected_value=request.expected
        )
    except Exception as e:
        # Raise 503 for Gemini API errors (will be caught by middleware)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to call Gemini API: {str(e)}"
        )

    # Cache the response in both Redis and PostgreSQL
    cache_data = {
        "badge": badge,
        "details": details
    }
    await redis_client.set_cache(work_id, cache_data)

    # Store in PostgreSQL
    new_cache = GeminiCache(
        id=work_id,
        badge=badge,
        details=details
    )
    db.add(new_cache)
    db.commit()

    return GeminiResponse(
        badge=badge,
        details=details
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
