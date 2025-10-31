"""Pydantic models for API request/response."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal


class GeminiRequest(BaseModel):
    """Request model for Gemini API endpoint."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "hash": "abc123def456",
                "expected": "some expected value"
            }
        }
    )
    
    hash: str = Field(..., description="Hash identifier for the request")
    expected: str = Field(..., description="Expected value or context")


class GeminiResponse(BaseModel):
    """Response model for Gemini API endpoint."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "badge": "TRUSTED",
                "details": "Analysis details from Gemini API"
            }
        }
    )
    
    badge: Literal['TRUSTED', 'UNTRUSTED', 'UNKNOWN'] = Field(
        ..., 
        description="Trust badge classification"
    )
    details: str = Field(..., description="Details from Gemini API analysis")
