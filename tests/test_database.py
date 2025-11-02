"""Tests for database models and operations."""
import pytest
from datetime import datetime
from app.database import GeminiCache


def test_create_cache_entry(test_db_session):
    """Test creating a cache entry in the database."""
    entry = GeminiCache(
        id="db-test-1",
        badge="MATCHS WITH DESCRIPTION",
        details="Test details for database entry"
    )
    test_db_session.add(entry)
    test_db_session.commit()
    
    # Query back the entry
    retrieved = test_db_session.query(GeminiCache).filter(
        GeminiCache.id == "db-test-1"
    ).first()
    
    assert retrieved is not None
    assert retrieved.id == "db-test-1"
    assert retrieved.badge == "MATCHS WITH DESCRIPTION"
    assert retrieved.details == "Test details for database entry"
    assert isinstance(retrieved.created_at, datetime)
    assert isinstance(retrieved.updated_at, datetime)


def test_update_cache_entry(test_db_session):
    """Test updating an existing cache entry."""
    # Create entry
    entry = GeminiCache(
        id="update_test",
        badge="UNKNOWN",
        details="Initial details"
    )
    test_db_session.add(entry)
    test_db_session.commit()
    
    # Update entry
    entry.badge = "MATCHS WITH DESCRIPTION"
    entry.details = "Updated details"
    test_db_session.commit()
    
    # Verify update
    retrieved = test_db_session.query(GeminiCache).filter(
        GeminiCache.id == "update_test"
    ).first()
    
    assert retrieved.badge == "MATCHS WITH DESCRIPTION"
    assert retrieved.details == "Updated details"


def test_query_by_hash(test_db_session):
    """Test querying cache entries by id."""
    # Create multiple entries
    entries = [
        GeminiCache(id="db-test-query-1", badge="MATCHS WITH DESCRIPTION", details="Details 1"),
        GeminiCache(id="db-test-query-2", badge="NEEDS REVISION", details="Details 2"),
        GeminiCache(id="db-test-query-3", badge="UNKNOWN", details="Details 3"),
    ]
    for entry in entries:
        test_db_session.add(entry)
    test_db_session.commit()
    
    # Query specific id
    result = test_db_session.query(GeminiCache).filter(
        GeminiCache.id == "db-test-query-2"
    ).first()
    
    assert result is not None
    assert result.badge == "NEEDS REVISION"
    assert result.details == "Details 2"


def test_hash_primary_key_constraint(test_db_session):
    """Test that id is unique (primary key constraint)."""
    entry1 = GeminiCache(
        id="duplicate_id",
        badge="MATCHS WITH DESCRIPTION",
        details="First entry"
    )
    test_db_session.add(entry1)
    test_db_session.commit()
    
    # Expunge to avoid identity conflict
    test_db_session.expunge(entry1)
    
    # Try to insert another entry with same id
    entry2 = GeminiCache(
        id="duplicate_id",
        badge="NEEDS REVISION",
        details="Second entry"
    )
    test_db_session.add(entry2)
    
    with pytest.raises(Exception):  # Will raise IntegrityError
        test_db_session.commit()


def test_delete_cache_entry(test_db_session):
    """Test deleting a cache entry."""
    entry = GeminiCache(
        id="delete_test",
        badge="MATCHS WITH DESCRIPTION",
        details="To be deleted"
    )
    test_db_session.add(entry)
    test_db_session.commit()
    
    # Delete entry
    test_db_session.delete(entry)
    test_db_session.commit()
    
    # Verify deletion
    result = test_db_session.query(GeminiCache).filter(
        GeminiCache.id == "delete_test"
    ).first()
    
    assert result is None


def test_all_badge_types(test_db_session):
    """Test storing all three badge types."""
    badges = ["MATCHS WITH DESCRIPTION", "NEEDS REVISION", "UNKNOWN"]
    
    for i, badge in enumerate(badges):
        entry = GeminiCache(
            id=f"badge_test_{i}",
            badge=badge,
            details=f"Details for {badge}"
        )
        test_db_session.add(entry)
    
    test_db_session.commit()
    
    # Verify all were stored
    for i, badge in enumerate(badges):
        result = test_db_session.query(GeminiCache).filter(
            GeminiCache.id == f"badge_test_{i}"
        ).first()
        assert result.badge == badge
