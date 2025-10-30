"""Pydantic models for API request/response."""
from pydantic import BaseModel, Field


class GeminiRequest(BaseModel):
    """Request model for Gemini API endpoint."""
    
    hash: str = Field(..., description="Hash identifier for the request")
    expected: str = Field(..., description="Expected value or context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "hash": "abc123def456",
                "expected": "some expected value"
            }
        }


class GeminiResponse(BaseModel):
    """Response model for Gemini API endpoint."""
    
    hash: str = Field(..., description="Hash identifier from the request")
    expected: str = Field(..., description="Expected value from the request")
    response: str = Field(..., description="Response from Gemini API")
    cached: bool = Field(..., description="Whether the response was served from cache")
    
    class Config:
        json_schema_extra = {
            "example": {
                "hash": "abc123def456",
                "expected": "some expected value",
                "response": "Gemini API response text",
                "cached": False
            }
        }
