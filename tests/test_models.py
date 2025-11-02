"""Tests for Pydantic models."""
import pytest
from pydantic import ValidationError
from app.models import GeminiRequest, GeminiResponse


def test_gemini_request_valid():
    """Test creating a valid GeminiRequest."""
    request = GeminiRequest(
        workId="gig-0-1-1",
        hashes=["ipfs://test_hash_123"],
        expected="test_expected_value"
    )
    assert request.workId == "gig-0-1-1"
    assert request.hashes == ["ipfs://test_hash_123"]
    assert request.expected == "test_expected_value"


def test_gemini_request_missing_hash():
    """Test GeminiRequest validation fails without hashes."""
    with pytest.raises(ValidationError) as exc_info:
        GeminiRequest(workId="gig-0-1-1", expected="test_value")
    
    errors = exc_info.value.errors()
    assert any(error["loc"] == ("hashes",) for error in errors)


def test_gemini_request_missing_expected():
    """Test GeminiRequest validation fails without expected."""
    with pytest.raises(ValidationError) as exc_info:
        GeminiRequest(workId="gig-0-1-1", hashes=["ipfs://test_hash"])
    
    errors = exc_info.value.errors()
    assert any(error["loc"] == ("expected",) for error in errors)


def test_gemini_response_trusted():
    """Test creating a GeminiResponse with MATCHS WITH DESCRIPTION badge."""
    response = GeminiResponse(
        badge="MATCHS WITH DESCRIPTION",
        details="This is trusted data"
    )
    assert response.badge == "MATCHS WITH DESCRIPTION"
    assert response.details == "This is trusted data"


def test_gemini_response_untrusted():
    """Test creating a GeminiResponse with NEEDS REVISION badge."""
    response = GeminiResponse(
        badge="NEEDS REVISION",
        details="This is untrusted data"
    )
    assert response.badge == "NEEDS REVISION"
    assert response.details == "This is untrusted data"


def test_gemini_response_unknown():
    """Test creating a GeminiResponse with UNKNOWN badge."""
    response = GeminiResponse(
        badge="UNKNOWN",
        details="Cannot determine trust level"
    )
    assert response.badge == "UNKNOWN"
    assert response.details == "Cannot determine trust level"


def test_gemini_response_invalid_badge():
    """Test GeminiResponse validation fails with invalid badge."""
    with pytest.raises(ValidationError) as exc_info:
        GeminiResponse(
            badge="INVALID_BADGE",
            details="Some details"
        )
    
    errors = exc_info.value.errors()
    assert any(error["loc"] == ("badge",) for error in errors)


def test_gemini_response_missing_details():
    """Test GeminiResponse validation fails without details."""
    with pytest.raises(ValidationError) as exc_info:
        GeminiResponse(badge="TRUSTED")
    
    errors = exc_info.value.errors()
    assert any(error["loc"] == ("details",) for error in errors)


def test_gemini_models_json_serialization():
    """Test that models can be serialized to JSON."""
    request = GeminiRequest(workId="gig-0-1-1", hashes=["ipfs://test"], expected="value")
    response = GeminiResponse(badge="MATCHS WITH DESCRIPTION", details="Test details")
    
    # Test serialization
    request_json = request.model_dump()
    response_json = response.model_dump()
    
    assert isinstance(request_json, dict)
    assert isinstance(response_json, dict)
    assert request_json["workId"] == "gig-0-1-1"
    assert request_json["hashes"] == ["ipfs://test"]
    assert response_json["badge"] == "MATCHS WITH DESCRIPTION"
