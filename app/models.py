"""Pydantic models for API request/response."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal


class GeminiRequest(BaseModel):
    """Request model for Gemini API endpoint."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "workId": "gig-0-1-1",
                "hashes": [
                    "ipfs://bafybeihdwdcefgh4dqkjv67uzcmwiyje6z4g3d5y5r3g4a3g5j6e6q7e",
                    "ipfs://bafybeibwzif3c4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s"
                ],
                "expected": "some expected value"
            }
        }
    )

    workId: str = Field(..., description="Work ID for the request")
    hashes: list[str] = Field(..., description="List of ipfs hash identifiers")
    expected: str = Field(..., description="Expected value or context")


class GeminiResponse(BaseModel):
    """Response model for Gemini API endpoint."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "badge": "MATCHS WITH DESCRIPTION",
                "details": "Analysis details from Gemini API"
            }
        }
    )

    badge: Literal['MATCHS WITH DESCRIPTION', 'NEEDS REVISION', 'UNKNOWN'] = Field(
        ...,
        description="Trust badge classification"
    )
    details: str = Field(..., description="Details from Gemini API analysis")
