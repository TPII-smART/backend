"""Tests for database models and operations."""
import pytest
from datetime import datetime
from app.database import GeminiCache


def test_create_cache_entry(test_db_session):
    """Test creating a cache entry in the database."""
    entry = GeminiCache(
        hash="test_hash_1",
        badge="TRUSTED",
        details="Test details for database entry"
    )
    test_db_session.add(entry)
    test_db_session.commit()
    
    # Query back the entry
    retrieved = test_db_session.query(GeminiCache).filter(
        GeminiCache.hash == "test_hash_1"
    ).first()
    
    assert retrieved is not None
    assert retrieved.hash == "test_hash_1"
    assert retrieved.badge == "TRUSTED"
    assert retrieved.details == "Test details for database entry"
    assert isinstance(retrieved.created_at, datetime)
    assert isinstance(retrieved.updated_at, datetime)


def test_update_cache_entry(test_db_session):
    """Test updating an existing cache entry."""
    # Create entry
    entry = GeminiCache(
        hash="update_test",
        badge="UNKNOWN",
        details="Initial details"
    )
    test_db_session.add(entry)
    test_db_session.commit()
    
    # Update entry
    entry.badge = "TRUSTED"
    entry.details = "Updated details"
    test_db_session.commit()
    
    # Verify update
    retrieved = test_db_session.query(GeminiCache).filter(
        GeminiCache.hash == "update_test"
    ).first()
    
    assert retrieved.badge == "TRUSTED"
    assert retrieved.details == "Updated details"


def test_query_by_hash(test_db_session):
    """Test querying cache entries by hash."""
    # Create multiple entries
    entries = [
        GeminiCache(hash="hash1", badge="TRUSTED", details="Details 1"),
        GeminiCache(hash="hash2", badge="UNTRUSTED", details="Details 2"),
        GeminiCache(hash="hash3", badge="UNKNOWN", details="Details 3"),
    ]
    for entry in entries:
        test_db_session.add(entry)
    test_db_session.commit()
    
    # Query specific hash
    result = test_db_session.query(GeminiCache).filter(
        GeminiCache.hash == "hash2"
    ).first()
    
    assert result is not None
    assert result.badge == "UNTRUSTED"
    assert result.details == "Details 2"


def test_hash_primary_key_constraint(test_db_session):
    """Test that hash is unique (primary key constraint)."""
    entry1 = GeminiCache(
        hash="duplicate_hash",
        badge="TRUSTED",
        details="First entry"
    )
    test_db_session.add(entry1)
    test_db_session.commit()
    
    # Try to insert another entry with same hash
    entry2 = GeminiCache(
        hash="duplicate_hash",
        badge="UNTRUSTED",
        details="Second entry"
    )
    test_db_session.add(entry2)
    
    with pytest.raises(Exception):  # Will raise IntegrityError
        test_db_session.commit()


def test_delete_cache_entry(test_db_session):
    """Test deleting a cache entry."""
    entry = GeminiCache(
        hash="delete_test",
        badge="TRUSTED",
        details="To be deleted"
    )
    test_db_session.add(entry)
    test_db_session.commit()
    
    # Delete entry
    test_db_session.delete(entry)
    test_db_session.commit()
    
    # Verify deletion
    result = test_db_session.query(GeminiCache).filter(
        GeminiCache.hash == "delete_test"
    ).first()
    
    assert result is None


def test_all_badge_types(test_db_session):
    """Test storing all three badge types."""
    badges = ["TRUSTED", "UNTRUSTED", "UNKNOWN"]
    
    for i, badge in enumerate(badges):
        entry = GeminiCache(
            hash=f"badge_test_{i}",
            badge=badge,
            details=f"Details for {badge}"
        )
        test_db_session.add(entry)
    
    test_db_session.commit()
    
    # Verify all were stored
    for i, badge in enumerate(badges):
        result = test_db_session.query(GeminiCache).filter(
            GeminiCache.hash == f"badge_test_{i}"
        ).first()
        assert result.badge == badge
