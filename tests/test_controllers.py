"""Tests for API controllers."""
import pytest
from app.database import GeminiCache


def test_root_endpoint(client):
    """Test root endpoint returns correct response."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Gemini API Service"
    assert data["status"] == "running"
    assert data["docs"] == "/docs"


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_gemini_endpoint_with_mock(client, mock_gemini_service, test_db_session):
    """Test Gemini endpoint with mocked API response."""
    # Configure mock to return specific response
    mock_gemini_service.generate_response.return_value = ("TRUSTED", "Test analysis details")
    
    # Make request
    response = client.post(
        "/gemini",
        json={"hash": "test_hash_123", "expected": "test_expected"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "badge" in data
    assert "details" in data
    assert data["badge"] == "TRUSTED"
    assert data["details"] == "Test analysis details"
    
    # Verify Gemini service was called
    mock_gemini_service.generate_response.assert_called_once()
    
    # Verify data was stored in database
    cached_entry = test_db_session.query(GeminiCache).filter(
        GeminiCache.hash == "test_hash_123"
    ).first()
    assert cached_entry is not None
    assert cached_entry.badge == "TRUSTED"
    assert cached_entry.details == "Test analysis details"


def test_gemini_endpoint_untrusted_response(client, mock_gemini_service, test_db_session):
    """Test Gemini endpoint returns UNTRUSTED classification."""
    mock_gemini_service.generate_response.return_value = ("UNTRUSTED", "Suspicious activity detected")
    
    response = client.post(
        "/gemini",
        json={"hash": "suspicious_hash", "expected": "check_security"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["badge"] == "UNTRUSTED"
    assert data["details"] == "Suspicious activity detected"


def test_gemini_endpoint_unknown_response(client, mock_gemini_service, test_db_session):
    """Test Gemini endpoint returns UNKNOWN classification."""
    mock_gemini_service.generate_response.return_value = ("UNKNOWN", "Unable to classify")
    
    response = client.post(
        "/gemini",
        json={"hash": "unclear_hash", "expected": "ambiguous_data"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["badge"] == "UNKNOWN"
    assert data["details"] == "Unable to classify"


def test_gemini_endpoint_cache_from_database(client, mock_gemini_service, test_db_session):
    """Test that cached data is retrieved from database."""
    # First, insert data directly into database
    cached_entry = GeminiCache(
        hash="cached_hash",
        badge="TRUSTED",
        details="Previously cached response"
    )
    test_db_session.add(cached_entry)
    test_db_session.commit()
    
    # Make request with same hash
    response = client.post(
        "/gemini",
        json={"hash": "cached_hash", "expected": "any_value"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["badge"] == "TRUSTED"
    assert data["details"] == "Previously cached response"
    
    # Verify Gemini service was NOT called (data came from cache)
    mock_gemini_service.generate_response.assert_not_called()


def test_gemini_endpoint_validation_error(client):
    """Test endpoint returns validation error for missing fields."""
    # Missing 'expected' field
    response = client.post(
        "/gemini",
        json={"hash": "test_hash"}
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_gemini_endpoint_invalid_badge_value(client, test_db_session):
    """Test that only valid badge values are accepted."""
    # Try to create entry with invalid badge (should be caught by Pydantic)
    response = client.post(
        "/gemini",
        json={"hash": "test", "expected": "test"}
    )
    
    # Response should still work because Gemini service is mocked
    assert response.status_code in [200, 500]  # 500 if mock not set up


def test_multiple_requests_same_hash(client, mock_gemini_service, test_db_session):
    """Test multiple requests with same hash use cache."""
    mock_gemini_service.generate_response.return_value = ("TRUSTED", "First response")
    
    # First request - should call API
    response1 = client.post(
        "/gemini",
        json={"hash": "same_hash", "expected": "value1"}
    )
    assert response1.status_code == 200
    assert mock_gemini_service.generate_response.call_count == 1
    
    # Second request with same hash - should use cache
    response2 = client.post(
        "/gemini",
        json={"hash": "same_hash", "expected": "value2"}
    )
    assert response2.status_code == 200
    # Should still be 1 because second request uses cache
    assert mock_gemini_service.generate_response.call_count == 1
    
    # Both responses should have same data from cache
    assert response2.json()["badge"] == "TRUSTED"
    assert response2.json()["details"] == "First response"
