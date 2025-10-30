"""Middleware for error handling and RFC 9457 problem details."""
import logging
from typing import Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, ConfigDict


logger = logging.getLogger(__name__)


class ProblemDetail(BaseModel):
    """RFC 9457 Problem Details for HTTP APIs.
    
    See: https://www.rfc-editor.org/rfc/rfc9457.html
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "https://example.com/probs/validation-error",
                "title": "Validation Error",
                "status": 422,
                "detail": "Request validation failed",
                "instance": "/api/endpoint"
            }
        }
    )
    
    type: str
    title: str
    status: int
    detail: str
    instance: str


async def error_handler_middleware(request: Request, call_next):
    """
    Middleware to handle all errors and format them according to RFC 9457.
    
    This middleware catches all exceptions and formats them into RFC 9457
    Problem Details JSON structure for consistent error responses.
    """
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        return await handle_exception(request, exc)


async def handle_exception(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle exceptions and return RFC 9457 compliant error response.
    
    Args:
        request: The incoming request
        exc: The exception that was raised
        
    Returns:
        JSONResponse with RFC 9457 problem details
    """
    # Default values
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_type = "about:blank"
    title = "Internal Server Error"
    detail = str(exc)
    
    # Handle specific exception types
    if isinstance(exc, StarletteHTTPException):
        status_code = exc.status_code
        detail = exc.detail
        
        # Map status codes to appropriate types and titles
        if status_code == status.HTTP_400_BAD_REQUEST:
            error_type = "https://datatracker.ietf.org/doc/html/rfc9110#section-15.5.1"
            title = "Bad Request"
        elif status_code == status.HTTP_401_UNAUTHORIZED:
            error_type = "https://datatracker.ietf.org/doc/html/rfc9110#section-15.5.2"
            title = "Unauthorized"
        elif status_code == status.HTTP_403_FORBIDDEN:
            error_type = "https://datatracker.ietf.org/doc/html/rfc9110#section-15.5.4"
            title = "Forbidden"
        elif status_code == status.HTTP_404_NOT_FOUND:
            error_type = "https://datatracker.ietf.org/doc/html/rfc9110#section-15.5.5"
            title = "Not Found"
        elif status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
            error_type = "https://datatracker.ietf.org/doc/html/rfc4918#section-11.2"
            title = "Unprocessable Entity"
        elif status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            error_type = "https://datatracker.ietf.org/doc/html/rfc9110#section-15.6.4"
            title = "Service Unavailable"
        elif status_code >= 500:
            error_type = "https://datatracker.ietf.org/doc/html/rfc9110#section-15.6.1"
            title = "Internal Server Error"
            
    elif isinstance(exc, RequestValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        error_type = "https://datatracker.ietf.org/doc/html/rfc4918#section-11.2"
        title = "Validation Error"
        detail = f"Request validation failed: {str(exc)}"
    
    # Check if it's a Gemini API error (return 503)
    elif "Gemini API error" in str(exc) or "Failed to call Gemini API" in str(exc):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        error_type = "https://datatracker.ietf.org/doc/html/rfc9110#section-15.6.4"
        title = "Service Unavailable"
        detail = "Gemini API is currently unavailable"
        logger.error(f"Gemini API error: {str(exc)}")
    
    # Log the error
    logger.error(
        f"Error handling request {request.method} {request.url.path}: "
        f"{exc.__class__.__name__}: {str(exc)}"
    )
    
    # Create RFC 9457 problem details
    problem = ProblemDetail(
        type=error_type,
        title=title,
        status=status_code,
        detail=detail,
        instance=str(request.url.path)
    )
    
    # Return JSON response with problem details
    return JSONResponse(
        status_code=status_code,
        content=problem.model_dump(),
        headers={"Content-Type": "application/problem+json"}
    )


def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle validation errors and return RFC 9457 compliant response.
    
    Args:
        request: The incoming request
        exc: The validation error
        
    Returns:
        JSONResponse with RFC 9457 problem details
    """
    # Format validation errors
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append(f"{field}: {error['msg']}")
    
    detail = "; ".join(errors)
    
    problem = ProblemDetail(
        type="https://datatracker.ietf.org/doc/html/rfc4918#section-11.2",
        title="Validation Error",
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=detail,
        instance=str(request.url.path)
    )
    
    logger.warning(f"Validation error on {request.url.path}: {detail}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=problem.model_dump(),
        headers={"Content-Type": "application/problem+json"}
    )


def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions and return RFC 9457 compliant response.
    
    Args:
        request: The incoming request
        exc: The HTTP exception
        
    Returns:
        JSONResponse with RFC 9457 problem details
    """
    # Map status codes to RFC 9110 references
    status_code = exc.status_code
    error_type = "about:blank"
    title = "HTTP Error"
    
    if status_code == status.HTTP_400_BAD_REQUEST:
        error_type = "https://datatracker.ietf.org/doc/html/rfc9110#section-15.5.1"
        title = "Bad Request"
    elif status_code == status.HTTP_401_UNAUTHORIZED:
        error_type = "https://datatracker.ietf.org/doc/html/rfc9110#section-15.5.2"
        title = "Unauthorized"
    elif status_code == status.HTTP_403_FORBIDDEN:
        error_type = "https://datatracker.ietf.org/doc/html/rfc9110#section-15.5.4"
        title = "Forbidden"
    elif status_code == status.HTTP_404_NOT_FOUND:
        error_type = "https://datatracker.ietf.org/doc/html/rfc9110#section-15.5.5"
        title = "Not Found"
    elif status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        error_type = "https://datatracker.ietf.org/doc/html/rfc4918#section-11.2"
        title = "Unprocessable Entity"
    elif status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
        error_type = "https://datatracker.ietf.org/doc/html/rfc9110#section-15.6.4"
        title = "Service Unavailable"
    elif status_code >= 500:
        error_type = "https://datatracker.ietf.org/doc/html/rfc9110#section-15.6.1"
        title = "Internal Server Error"
    
    problem = ProblemDetail(
        type=error_type,
        title=title,
        status=status_code,
        detail=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
        instance=str(request.url.path)
    )
    
    logger.info(f"HTTP {status_code} on {request.url.path}: {exc.detail}")
    
    return JSONResponse(
        status_code=status_code,
        content=problem.model_dump(),
        headers={"Content-Type": "application/problem+json"}
    )
