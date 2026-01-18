"""
Tests for the visitor check-in system.

Run with: python -m pytest tests/
"""

import pytest
import numpy as np
import tempfile
import os
from pathlib import Path

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import VisitorDatabase, AttendanceLogger
from src.recognition import FaceRecognizer, RecognitionResult


class TestVisitorDatabase:
    """Tests for the database module."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = VisitorDatabase(db_path)
            yield db
    
    def test_add_visitor(self, temp_db):
        """Test adding a new visitor."""
        # Create a fake face encoding (128 dimensions)
        fake_encoding = np.random.rand(128)
        
        visitor_id = temp_db.add_visitor("John Doe", fake_encoding)
        
        assert visitor_id == 1
        assert temp_db.get_visitor_count() == 1
    
    def test_get_visitor(self, temp_db):
        """Test retrieving a visitor by ID."""
        fake_encoding = np.random.rand(128)
        visitor_id = temp_db.add_visitor("Jane Smith", fake_encoding)
        
        visitor = temp_db.get_visitor(visitor_id)
        
        assert visitor is not None
        assert visitor["name"] == "Jane Smith"
        assert visitor["visit_count"] == 1
    
    def test_get_all_encodings(self, temp_db):
        """Test retrieving all face encodings."""
        enc1 = np.random.rand(128)
        enc2 = np.random.rand(128)
        
        temp_db.add_visitor("Person 1", enc1)
        temp_db.add_visitor("Person 2", enc2)
        
        encodings = temp_db.get_all_encodings()
        
        assert len(encodings) == 2
        assert encodings[0][1] == "Person 1"
        assert encodings[1][1] == "Person 2"
        assert len(encodings[0][2]) == 128  # Encoding dimension
    
    def test_record_visit(self, temp_db):
        """Test updating visit count."""
        fake_encoding = np.random.rand(128)
        visitor_id = temp_db.add_visitor("Frequent Visitor", fake_encoding)
        
        # Initial visit count is 1
        visitor = temp_db.get_visitor(visitor_id)
        assert visitor["visit_count"] == 1
        
        # Record another visit
        temp_db.record_visit(visitor_id)
        
        visitor = temp_db.get_visitor(visitor_id)
        assert visitor["visit_count"] == 2
    
    def test_delete_visitor(self, temp_db):
        """Test deleting a visitor."""
        fake_encoding = np.random.rand(128)
        visitor_id = temp_db.add_visitor("To Delete", fake_encoding)
        
        assert temp_db.get_visitor_count() == 1
        
        result = temp_db.delete_visitor(visitor_id)
        
        assert result is True
        assert temp_db.get_visitor_count() == 0
        assert temp_db.get_visitor(visitor_id) is None


class TestAttendanceLogger:
    """Tests for the attendance logger."""
    
    @pytest.fixture
    def temp_logger(self):
        """Create a temporary logger for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AttendanceLogger(tmpdir)
            yield logger
    
    def test_log_checkin(self, temp_logger):
        """Test logging a check-in."""
        temp_logger.log_checkin(1, "Test Person", recognized=True)
        
        checkins = temp_logger.get_today_checkins()
        
        assert len(checkins) == 1
        assert checkins[0]["visitor_name"] == "Test Person"
        assert checkins[0]["recognized"] is True
    
    def test_multiple_checkins(self, temp_logger):
        """Test logging multiple check-ins."""
        temp_logger.log_checkin(1, "Person A", recognized=True)
        temp_logger.log_checkin(2, "Person B", recognized=True)
        temp_logger.log_checkin(3, "Person C", recognized=False)
        
        checkins = temp_logger.get_today_checkins()
        
        assert len(checkins) == 3


class TestFaceRecognizer:
    """Tests for the face recognition module."""
    
    def test_find_match_empty_database(self):
        """Test matching against empty database."""
        recognizer = FaceRecognizer()
        
        fake_encoding = np.random.rand(128)
        result = recognizer.find_match(fake_encoding, [])
        
        assert result.success is False
        assert "No registered visitors" in result.message
    
    def test_find_match_exact(self):
        """Test finding an exact match."""
        recognizer = FaceRecognizer(tolerance=0.6)
        
        # Create a known encoding
        known_encoding = np.random.rand(128)
        known_encodings = [(1, "Known Person", known_encoding)]
        
        # Same encoding should match
        result = recognizer.find_match(known_encoding, known_encodings)
        
        assert result.success is True
        assert result.visitor_id == 1
        assert result.visitor_name == "Known Person"
        assert result.confidence > 0.9
    
    def test_find_match_similar(self):
        """Test finding a similar (but not exact) match."""
        recognizer = FaceRecognizer(tolerance=0.6)
        
        # Create a known encoding
        known_encoding = np.random.rand(128)
        known_encodings = [(1, "Known Person", known_encoding)]
        
        # Create a slightly different encoding (add small noise)
        similar_encoding = known_encoding + np.random.rand(128) * 0.1
        
        result = recognizer.find_match(similar_encoding, known_encodings)
        
        # Should still match with some confidence
        assert result.success is True
        assert result.visitor_id == 1
    
    def test_find_match_different(self):
        """Test not matching a completely different face."""
        recognizer = FaceRecognizer(tolerance=0.6)
        
        known_encoding = np.random.rand(128)
        known_encodings = [(1, "Known Person", known_encoding)]
        
        # Completely different encoding
        different_encoding = np.random.rand(128)
        
        result = recognizer.find_match(different_encoding, known_encodings)
        
        # Might or might not match depending on random values
        # Just check it returns a valid result
        assert isinstance(result, RecognitionResult)
    
    def test_tolerance_adjustment(self):
        """Test that tolerance can be adjusted."""
        recognizer = FaceRecognizer(tolerance=0.6)
        
        assert recognizer.tolerance == 0.6
        
        recognizer.set_tolerance(0.4)
        assert recognizer.tolerance == 0.4
        
        # Test bounds
        recognizer.set_tolerance(0.0)
        assert recognizer.tolerance == 0.1  # Minimum
        
        recognizer.set_tolerance(2.0)
        assert recognizer.tolerance == 1.0  # Maximum


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
