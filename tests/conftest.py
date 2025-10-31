"""Pytest configuration and fixtures for tests."""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

# Set test environment variables before importing app modules
os.environ["POSTGRES_USER"] = "postgres_test"
os.environ["POSTGRES_PASSWORD"] = "postgres_test"
os.environ["POSTGRES_DB"] = "gemini_cache_test"
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5433"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6380"
os.environ["REDIS_DB"] = "0"
os.environ["GEMINI_API_KEY"] = "test_key"
os.environ["DB_POOL_SIZE"] = "2"
os.environ["DB_MAX_OVERFLOW"] = "3"

from app.database import Base, get_db
from app.main import app


@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine."""
    database_url = "postgresql://postgres_test:postgres_test@localhost:5433/gemini_cache_test"
    engine = create_engine(database_url, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a test database session for each test."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def client(test_db_session):
    """Create a test client with database session override."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_gemini_service():
    """Mock the Gemini service to avoid API calls."""
    from unittest.mock import AsyncMock
    with patch("app.controllers.gemini_service") as mock_service:
        # Default mock response (must be AsyncMock for async methods)
        mock_service.generate_response = AsyncMock(return_value=("TRUSTED", "This is a test response from mocked Gemini API"))
        yield mock_service


@pytest.fixture(scope="function")
async def clean_redis():
    """Clean Redis test database before each test."""
    from app.redis_client import redis_client
    # Clear all keys in the test Redis database
    client = redis_client._get_client()
    await client.flushdb()
    yield
    # Clean up after test
    await client.flushdb()
