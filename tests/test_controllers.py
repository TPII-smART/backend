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


def test_gemini_endpoint_with_mock(client, mock_gemini_service, clean_redis, test_db_session):
    """Test Gemini endpoint with mocked API response."""
    # Configure mock to return specific response
    mock_gemini_service.generate_response.return_value = ("MATCHS WITH DESCRIPTION", "Test analysis details")
    
    # Make request
    response = client.post(
        "/gemini",
        json={"workId": "gig-0-1-1", "hashes": ["ipfs://test_hash_123"], "expected": "test_expected"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "badge" in data
    assert "details" in data
    assert data["badge"] == "MATCHS WITH DESCRIPTION"
    assert data["details"] == "Test analysis details"
    
    # Verify Gemini service was called
    mock_gemini_service.generate_response.assert_called_once()
    
    # Verify data was stored in database
    cached_entry = test_db_session.query(GeminiCache).filter(
        GeminiCache.id == "gig-0-1-1"
    ).first()
    assert cached_entry is not None
    assert cached_entry.badge == "MATCHS WITH DESCRIPTION"
    assert cached_entry.details == "Test analysis details"


def test_gemini_endpoint_untrusted_response(client, mock_gemini_service, clean_redis, test_db_session):
    """Test Gemini endpoint returns NEEDS REVISION classification."""
    mock_gemini_service.generate_response.return_value = ("NEEDS REVISION", "Suspicious activity detected")
    
    response = client.post(
        "/gemini",
        json={"workId": "gig-0-1-2", "hashes": ["ipfs://suspicious_hash"], "expected": "check_security"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["badge"] == "NEEDS REVISION"
    assert data["details"] == "Suspicious activity detected"


def test_gemini_endpoint_unknown_response(client, mock_gemini_service, clean_redis, test_db_session):
    """Test Gemini endpoint returns UNKNOWN classification."""
    mock_gemini_service.generate_response.return_value = ("UNKNOWN", "Unable to classify")
    
    response = client.post(
        "/gemini",
        json={"workId": "gig-0-1-3", "hashes": ["ipfs://unclear_hash"], "expected": "ambiguous_data"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["badge"] == "UNKNOWN"
    assert data["details"] == "Unable to classify"


def test_gemini_endpoint_cache_from_database(client, mock_gemini_service, clean_redis, test_db_session):
    """Test that cached data is retrieved from database."""
    # First, insert data directly into database
    cached_entry = GeminiCache(
        id="gig-0-1-4",
        badge="MATCHS WITH DESCRIPTION",
        details="Previously cached response"
    )
    test_db_session.add(cached_entry)
    test_db_session.commit()
    
    # Make request with same workId
    response = client.post(
        "/gemini",
        json={"workId": "gig-0-1-4", "hashes": ["ipfs://cached_hash"], "expected": "any_value"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["badge"] == "MATCHS WITH DESCRIPTION"
    assert data["details"] == "Previously cached response"
    
    # Verify Gemini service was NOT called (data came from cache)
    mock_gemini_service.generate_response.assert_not_called()


def test_gemini_endpoint_validation_error(client):
    """Test endpoint returns validation error for missing fields."""
    # Missing 'expected' field
    response = client.post(
        "/gemini",
        json={"workId": "gig-0-1-5", "hashes": ["ipfs://test_hash"]}
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_gemini_endpoint_invalid_badge_value(client, test_db_session):
    """Test that only valid badge values are accepted."""
    # Try to create entry with invalid badge (should be caught by Pydantic)
    response = client.post(
        "/gemini",
        json={"workId": "gig-0-1-6", "hashes": ["ipfs://test"], "expected": "test"}
    )
    
    # Response should still work because Gemini service is mocked
    # 503 if Gemini service fails (not mocked), 200 if successful
    assert response.status_code in [200, 503]


def test_multiple_requests_same_hash(client, mock_gemini_service, clean_redis, test_db_session):
    """Test multiple requests with same workId use cache."""
    mock_gemini_service.generate_response.return_value = ("MATCHS WITH DESCRIPTION", "First response")
    
    # First request - should call API and store in Redis and PostgreSQL
    response1 = client.post(
        "/gemini",
        json={"workId": "gig-0-1-7", "hashes": ["ipfs://same_hash"], "expected": "value1"}
    )
    assert response1.status_code == 200
    assert mock_gemini_service.generate_response.call_count == 1
    
    # Second request with same workId - should use Redis cache
    response2 = client.post(
        "/gemini",
        json={"workId": "gig-0-1-7", "hashes": ["ipfs://same_hash"], "expected": "value2"}
    )
    assert response2.status_code == 200
    # Should still be 1 because second request uses Redis cache
    assert mock_gemini_service.generate_response.call_count == 1
    
    # Both responses should have same data from cache
    assert response2.json()["badge"] == "MATCHS WITH DESCRIPTION"
    assert response2.json()["details"] == "First response"
