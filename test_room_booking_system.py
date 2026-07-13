import unittest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from datetime import datetime, timedelta
import sys
import json


try:
    from main import (
        create_room_svc,
        book_room_svc,
        cancel_booking_svc,
        reschedule_booking_svc,
        check_booking_clash,
        calculate_occupancy,
        compute_free_slots,
        find_day_doc,
        _valid_time,
        _valid_date,
        _find_room_by_name_or_id,
        doc_to_dict,
        get_or_create_day,
        bump_stat,
        WORK_START,
        WORK_END,
        DAY_TOTAL_MINUTES,
    )
except ImportError as e:
    print(f"Warning: Could not import main module: {e}")
    print("Make sure main.py is in the same directory or adjust sys.path")


# ================================================================================
# TEST FIXTURES AND MOCK DATA
# ================================================================================

class MockFirestoreDoc:
    """Mock Firestore Document for testing."""
    
    def __init__(self, doc_id, data):
        self.id = doc_id
        self._data = data
    
    def to_dict(self):
        return self._data.copy()
    
    def get(self):
        return self


class TestRoomBookingSystem(unittest.TestCase):
    """
    Main test class for Room Booking System.
    
    Contains unit tests and integration tests for all major operations.
    Uses mocking to isolate database calls.
    """
    
    # ========================================================================
    # SETUP AND TEARDOWN
    # ========================================================================
    
    def setUp(self):
        """
        Set up test fixtures before each test.
        
        Creates mock user, room, and booking data for consistent testing.
        """
        self.mock_user = {
            "user_id": "test_user_123",
            "email": "testuser@example.com",
            "name": "Test User"
        }
        
        self.mock_room = {
            "_id": "room_001",
            "name": "Conference Room A",
            "created_by": "test_user_123",
            "created_by_email": "testuser@example.com",
            "created_at": datetime.now().isoformat()
        }
        
        self.mock_booking = {
            "_id": "booking_001",
            "day_id": "day_001",
            "room_id": "room_001",
            "room_name": "Conference Room A",
            "meeting_name": "Team Standup",
            "date": "2025-07-15",
            "start_time": "09:00",
            "end_time": "10:00",
            "user_id": "test_user_123",
            "user_email": "testuser@example.com",
            "created_at": datetime.now().isoformat()
        }
        
        # Test dates
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
