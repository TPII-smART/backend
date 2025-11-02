"""Tests for error handling middleware and RFC 9457 compliance."""
import pytest
from fastapi.testclient import TestClient


def test_validation_error_rfc9457(client):
    """Test that validation errors return RFC 9457 compliant response."""
    # Send invalid request (missing required fields)
    response = client.post("/gemini", json={})
    
    assert response.status_code == 422
    assert response.headers.get("content-type") == "application/problem+json"
    
    data = response.json()
    
    # Verify RFC 9457 fields are present
    assert "type" in data
    assert "title" in data
    assert "status" in data
    assert "detail" in data
    assert "instance" in data
    
    # Verify specific values
    assert data["status"] == 422
    assert data["title"] == "Validation Error"
    assert data["instance"] == "/gemini"
    assert "workId" in data["detail"] or "hashes" in data["detail"] or "expected" in data["detail"]


def test_validation_error_missing_hash(client):
    """Test validation error when hashes is missing."""
    response = client.post("/gemini", json={"workId": "gig-0-1-1", "expected": "test"})
    
    assert response.status_code == 422
    data = response.json()
    
    assert data["status"] == 422
    assert data["title"] == "Validation Error"
    assert "hashes" in data["detail"]


def test_validation_error_missing_expected(client):
    """Test validation error when expected is missing."""
    response = client.post("/gemini", json={"workId": "gig-0-1-1", "hashes": ["ipfs://test123"]})
    
    assert response.status_code == 422
    data = response.json()
    
    assert data["status"] == 422
    assert data["title"] == "Validation Error"
    assert "expected" in data["detail"]


def test_not_found_error_rfc9457(client):
    """Test that 404 errors return RFC 9457 compliant response."""
    response = client.get("/nonexistent")
    
    assert response.status_code == 404
    assert response.headers.get("content-type") == "application/problem+json"
    
    data = response.json()
    
    # Verify RFC 9457 fields
    assert data["type"] == "https://datatracker.ietf.org/doc/html/rfc9110#section-15.5.5"
    assert data["title"] == "Not Found"
    assert data["status"] == 404
    assert data["instance"] == "/nonexistent"


def test_gemini_api_error_returns_503(client, mock_gemini_service, clean_redis, test_db_session):
    """Test that Gemini API errors return 503 Service Unavailable."""
    # Configure mock to raise an exception
    mock_gemini_service.generate_response.side_effect = Exception("Gemini API connection failed")
    
    response = client.post(
        "/gemini",
        json={"workId": "gig-0-1-8", "hashes": ["ipfs://error_hash"], "expected": "test_value"}
    )
    
    assert response.status_code == 503
    assert response.headers.get("content-type") == "application/problem+json"
    
    data = response.json()
    
    # Verify RFC 9457 fields
    assert data["type"] == "https://datatracker.ietf.org/doc/html/rfc9110#section-15.6.4"
    assert data["title"] == "Service Unavailable"
    assert data["status"] == 503
    assert "Gemini API" in data["detail"] or "unavailable" in data["detail"].lower()
    assert data["instance"] == "/gemini"


def test_successful_request_no_error_response(client, mock_gemini_service, clean_redis, test_db_session):
    """Test that successful requests don't have error format."""
    mock_gemini_service.generate_response.return_value = ("MATCHS WITH DESCRIPTION", "Test response")
    
    response = client.post(
        "/gemini",
        json={"workId": "gig-0-1-9", "hashes": ["ipfs://success_hash"], "expected": "test_value"}
    )
    
    assert response.status_code == 200
    # Successful responses should NOT be in problem+json format
    assert response.headers.get("content-type") != "application/problem+json"
    
    data = response.json()
    
    # Should have normal response structure, not RFC 9457 error structure
    assert "badge" in data
    assert "details" in data
    assert "type" not in data  # RFC 9457 field should not be present
    assert "title" not in data  # RFC 9457 field should not be present


def test_rfc9457_structure_validation(client):
    """Test that error responses follow exact RFC 9457 structure."""
    response = client.post("/gemini", json={"invalid": "data"})
    
    assert response.status_code == 422
    data = response.json()
    
    # RFC 9457 requires these specific fields
    required_fields = ["type", "title", "status", "detail", "instance"]
    for field in required_fields:
        assert field in data, f"RFC 9457 requires '{field}' field"
    
    # Verify types
    assert isinstance(data["type"], str)
    assert isinstance(data["title"], str)
    assert isinstance(data["status"], int)
    assert isinstance(data["detail"], str)
    assert isinstance(data["instance"], str)
    
    # Verify type is a URI
    assert data["type"].startswith("http") or data["type"] == "about:blank"
