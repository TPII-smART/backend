"""Pydantic models for API request/response."""
from pydantic import BaseModel, Field
from typing import Literal


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
    
    badge: Literal['TRUSTED', 'UNTRUSTED', 'UNKNOWN'] = Field(
        ..., 
        description="Trust badge classification"
    )
    details: str = Field(..., description="Details from Gemini API analysis")
    
    class Config:
        json_schema_extra = {
            "example": {
                "badge": "TRUSTED",
                "details": "Analysis details from Gemini API"
            }
        }
