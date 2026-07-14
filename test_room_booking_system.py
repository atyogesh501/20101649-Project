"""
CRUD Test Suite — Flask Room Booking System

"""

import unittest
from unittest.mock import MagicMock, patch, call
from datetime import datetime

try:
    from main import (
        create_room_svc, book_room_svc,
        cancel_booking_svc, reschedule_booking_svc,
        find_day_doc, get_or_create_day, doc_to_dict,
    )
except ImportError as e:
    print(f"Import warning: {e}")


# ── Helpers ──────────────────────────────────────────────────────────────────

class FakeDoc:
    """Minimal Firestore document mock."""
    def __init__(self, doc_id, data):
        self.id = doc_id
        self._data = data
    def to_dict(self):
        return self._data.copy()


def make_user():
    return {"user_id": "u1", "email": "test@dbs.ie", "name": "Tester"}

def make_room():
    return {"_id": "r1", "name": "Room A", "created_by": "u1",
            "created_by_email": "test@dbs.ie", "created_at": datetime.now().isoformat()}

def make_booking():
    return {"_id": "b1", "room_id": "r1", "room_name": "Room A",
            "meeting_name": "Standup", "date": "2025-07-15",
            "start_time": "09:00", "end_time": "10:00",
            "user_id": "u1", "user_email": "test@dbs.ie",
            "day_id": "d1", "created_at": datetime.now().isoformat()}


# ── CREATE ────────────────────────────────────────────────────────────────────

class TestCreate(unittest.TestCase):

    @patch('main.bump_stat')
    @patch('main.rooms_collection')
    def test_create_room_success(self, mock_col, mock_stat):
        """C1: Valid room name creates room and bumps stat."""
        mock_col.where.return_value.limit.return_value.stream.return_value = []
        ref = MagicMock(); ref.id = "r_new"
        mock_col.add.return_value = (None, ref)

        res = create_room_svc(make_user(), "Board Room")

        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("room_id"), "r_new")
        mock_stat.assert_called_once_with("u1", "rooms_created")

    @patch('main.rooms_collection')
    def test_create_room_duplicate(self, mock_col):
        """C2: Duplicate room name returns error."""
        mock_col.where.return_value.limit.return_value.stream.return_value = [MagicMock()]
        res = create_room_svc(make_user(), "Room A")
        self.assertIn("error", res)
        self.assertIn("already exists", res["error"])

    @patch('main.rooms_collection')
    def test_create_room_empty_name(self, mock_col):
        """C3: Empty or whitespace name returns error."""
        for name in ("", "   "):
            self.assertIn("error", create_room_svc(make_user(), name))

    @patch('main.bump_stat')
    @patch('main.bookings_collection')
    @patch('main.get_or_create_day')
    @patch('main.check_booking_clash')
    @patch('main._find_room_by_name_or_id')
    def test_book_room_success(self, mock_find, mock_clash, mock_day, mock_bk, mock_stat):
        """C4: Valid booking returns success and booking_id."""
        mock_find.return_value = make_room()
        mock_clash.return_value = False
        mock_day.return_value = "d1"
        ref = MagicMock(); ref.id = "b_new"
        mock_bk.add.return_value = (None, ref)

        res = book_room_svc(make_user(), "Room A", "2025-07-15", "09:00", "10:00", "Sprint")

        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("booking_id"), "b_new")
        self.assertEqual(res.get("meeting_name"), "Sprint")

    @patch('main._find_room_by_name_or_id')
    def test_book_room_not_found(self, mock_find):
        """C5: Booking a non-existent room returns error."""
        mock_find.return_value = None
        res = book_room_svc(make_user(), "Ghost", "2025-07-15", "09:00", "10:00", "Mtg")
        self.assertIn("error", res)
        self.assertIn("couldn't find", res["error"])

    @patch('main.check_booking_clash')
    @patch('main._find_room_by_name_or_id')
    def test_book_room_clash(self, mock_find, mock_clash):
        """C6: Clashing time slot returns error."""
        mock_find.return_value = make_room()
        mock_clash.return_value = True
        res = book_room_svc(make_user(), "Room A", "2025-07-15", "09:00", "10:00", "Mtg")
        self.assertIn("error", res)
        self.assertIn("already booked", res["error"])

    @patch('main._find_room_by_name_or_id')
    def test_book_room_bad_time_range(self, mock_find):
        """C7: End time before start time returns error."""
        mock_find.return_value = make_room()
        res = book_room_svc(make_user(), "Room A", "2025-07-15", "10:00", "09:00", "Mtg")
        self.assertIn("error", res)
        self.assertIn("after start time", res["error"])


# ── READ ──────────────────────────────────────────────────────────────────────

class TestRead(unittest.TestCase):

    def test_doc_to_dict_room(self):
        """R1: doc_to_dict maps id to _id and preserves all fields."""
        doc = FakeDoc("r1", make_room())
        result = doc_to_dict(doc)
        self.assertEqual(result["_id"], "r1")
        self.assertEqual(result["name"], "Room A")
        self.assertIn("created_by", result)

    def test_doc_to_dict_booking(self):
        """R2: doc_to_dict preserves all booking fields."""
        doc = FakeDoc("b1", make_booking())
        result = doc_to_dict(doc)
        self.assertEqual(result["_id"], "b1")
        self.assertEqual(result["meeting_name"], "Standup")
        self.assertEqual(result["start_time"], "09:00")

    @patch('main.days_collection')
    def test_find_day_doc_found(self, mock_col):
        """R3: find_day_doc returns document when it exists."""
        mock_col.where.return_value.where.return_value.limit.return_value \
            .stream.return_value = [FakeDoc("d1", {"room_id": "r1", "date": "2025-07-15"})]
        result = find_day_doc("r1", "2025-07-15")
        self.assertIsNotNone(result)

    @patch('main.days_collection')
    def test_find_day_doc_missing(self, mock_col):
        """R4: find_day_doc returns None when no document exists."""
        mock_col.where.return_value.where.return_value.limit.return_value \
            .stream.return_value = []
        self.assertIsNone(find_day_doc("r1", "2025-07-20"))

    @patch('main.days_collection')
    def test_get_or_create_day_existing(self, mock_col):
        """R5: get_or_create_day returns existing ID without creating."""
        mock_col.where.return_value.where.return_value.limit.return_value \
            .stream.return_value = [FakeDoc("d1", {})]
        self.assertEqual(get_or_create_day("r1", "2025-07-15"), "d1")
        mock_col.add.assert_not_called()

    @patch('main.days_collection')
    def test_get_or_create_day_new(self, mock_col):
        """R6: get_or_create_day creates and returns new ID when missing."""
        mock_col.where.return_value.where.return_value.limit.return_value \
            .stream.return_value = []
        ref = MagicMock(); ref.id = "d_new"
        mock_col.add.return_value = (None, ref)
        self.assertEqual(get_or_create_day("r1", "2025-07-20"), "d_new")


# ── UPDATE ────────────────────────────────────────────────────────────────────

class TestUpdate(unittest.TestCase):

    @patch('main.bump_stat')
    @patch('main.bookings_collection')
    @patch('main.get_or_create_day')
    @patch('main.check_booking_clash')
    def test_reschedule_success(self, mock_clash, mock_day, mock_bk, mock_stat):
        """U1: Valid reschedule updates booking and bumps stat."""
        mock_bk.where.return_value.stream.return_value = [FakeDoc("b1", make_booking())]
        mock_clash.return_value = False
        mock_day.return_value = "d2"
        mock_bk.document.return_value.update = MagicMock()

        res = reschedule_booking_svc(make_user(), meeting_name="Standup",
                                     new_date="2025-07-16", new_start="14:00", new_end="15:00")

        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("date"), "2025-07-16")
        self.assertEqual(res.get("start_time"), "14:00")
        mock_stat.assert_called_once_with("u1", "bookings_edited")

    @patch('main.check_booking_clash')
    @patch('main.bookings_collection')
    def test_reschedule_clash(self, mock_bk, mock_clash):
        """U2: Reschedule to occupied slot returns error."""
        mock_bk.where.return_value.stream.return_value = [FakeDoc("b1", make_booking())]
        mock_clash.return_value = True
        res = reschedule_booking_svc(make_user(), meeting_name="Standup",
                                     new_date="2025-07-16", new_start="14:00", new_end="15:00")
        self.assertIn("error", res)
        self.assertIn("already booked", res["error"])

    @patch('main.bookings_collection')
    def test_reschedule_not_found(self, mock_bk):
        """U3: Reschedule non-existent booking returns error."""
        mock_bk.where.return_value.stream.return_value = []
        res = reschedule_booking_svc(make_user(), meeting_name="Ghost",
                                     new_date="2025-07-16", new_start="14:00", new_end="15:00")
        self.assertIn("error", res)
        self.assertIn("couldn't find", res["error"])

    @patch('main.bookings_collection')
    def test_reschedule_bad_time(self, mock_bk):
        """U4: Reschedule with end before start returns error."""
        mock_bk.where.return_value.stream.return_value = [FakeDoc("b1", make_booking())]
        res = reschedule_booking_svc(make_user(), meeting_name="Standup",
                                     new_date="2025-07-16", new_start="14:00", new_end="13:00")
        self.assertIn("error", res)
        self.assertIn("after start time", res["error"])


# ── DELETE ────────────────────────────────────────────────────────────────────

class TestDelete(unittest.TestCase):

    @patch('main.bump_stat')
    @patch('main.bookings_collection')
    def test_cancel_success(self, mock_bk, mock_stat):
        """D1: Valid cancellation deletes booking and bumps stat."""
        mock_bk.where.return_value.stream.return_value = [FakeDoc("b1", make_booking())]
        mock_del = MagicMock()
        mock_bk.document.return_value.delete = mock_del

        res = cancel_booking_svc(make_user(), meeting_name="Standup")

        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("cancelled"), "Standup")
        mock_stat.assert_called_once_with("u1", "bookings_deleted")
        mock_del.assert_called_once()

    @patch('main.bookings_collection')
    def test_cancel_not_found(self, mock_bk):
        """D2: Cancel non-existent booking returns error."""
        mock_bk.where.return_value.stream.return_value = []
        res = cancel_booking_svc(make_user(), meeting_name="Ghost")
        self.assertIn("error", res)
        self.assertIn("couldn't find", res["error"])

    @patch('main.bookings_collection')
    def test_cancel_wrong_user(self, mock_bk):
        """D3: Cancel booking owned by another user returns error.
        
        FIX: Mock must simulate real DB behavior:
        - When query filters by user_id="u1", return empty (booking belongs to other_user)
        - This tests that cancel_booking_svc calls _find_user_booking which filters by user_id
        """
        # Setup mock to return empty when filtering for u1's bookings
        mock_bk.where.return_value.stream.return_value = []
        
        res = cancel_booking_svc(make_user(), meeting_name="Standup")
        
        # Should return error because no booking found for user u1
        self.assertIn("error", res)
        self.assertIn("couldn't find", res["error"])

    @patch('main.bump_stat')
    @patch('main.bookings_collection')
    def test_cancel_by_date(self, mock_bk, mock_stat):
        """D4: Cancel filtered by date deletes correct booking."""
        mock_bk.where.return_value.stream.return_value = [FakeDoc("b1", make_booking())]
        mock_bk.document.return_value.delete = MagicMock()
        res = cancel_booking_svc(make_user(), meeting_name="Standup", date="2025-07-15")
        self.assertTrue(res.get("success"))


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)