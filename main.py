import os
import uuid
from datetime import datetime

from flask import Flask, request
import google.oauth2.id_token
from google.auth.transport import requests

from google.cloud import firestore, storage
from google.auth.exceptions import DefaultCredentialsError
from google.cloud.firestore_v1.base_query import FieldFilter


app = Flask(__name__, static_folder="static", template_folder="templates")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "firestoreDetails.json"

STORAGE_BUCKET = "booming-order-497611-f8.appspot.com"


WORK_START = "00:00"
WORK_END = "23:59"
DAY_TOTAL_MINUTES = 24 * 60

def get_firestore():
    try:
        return firestore.Client()
    except DefaultCredentialsError:
        print("Firestore credentials are missing! Please set up your credentials.")
        return None
    except AttributeError as e:
        print(f"Firestore encountered an AttributeError: {e}")
        return None


def get_storage_client():
    try:
        return storage.Client()
    except Exception as e:
        print(f"Storage client error: {e}")
        return None

db = get_firestore()
if db is not None:
    print("Successfully connected to Firestore!")

rooms_collection = db.collection("rooms")
days_collection = db.collection("days")
bookings_collection = db.collection("bookings")
users_collection = db.collection("users")



def doc_to_dict(doc):
    data = doc.to_dict() or {}
    data["_id"] = doc.id
    return data

def get_user_token():
    id_token = request.cookies.get("token")
    if id_token:
        try:
            firebase_request_adapter = requests.Request()
            return google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        except ValueError as e:
            print("Error verifying Firebase token:", e)
    return None

def get_user_data():
    user_token = get_user_token()
    if not user_token:
        return None
    user = {
        "user_id": user_token.get("user_id"),
        "email": user_token.get("email"),
        "name": user_token.get("name", user_token.get("email", "User")),
    }
    # Merge in stored profile (photo + display name)
    profile = get_user_profile(user["user_id"], user["email"], user["name"])
    user["photo_url"] = profile.get("photo_url")
    user["display_name"] = profile.get("display_name", user["name"])
    return user


# ==================== USER PROFILE / STATS ====================

def get_user_profile(user_id: str, email: str = "", name: str = ""):
    """Fetch or lazily create a user profile document holding stats + photo."""
    ref = users_collection.document(user_id)
    snap = ref.get()
    if snap.exists:
        return snap.to_dict()
    profile = {
        "user_id": user_id,
        "email": email,
        "display_name": name or email or "User",
        "photo_url": None,
        "rooms_created": 0,
        "rooms_deleted": 0,
        "bookings_created": 0,
        "bookings_deleted": 0,
        "bookings_edited": 0,
        "created_at": datetime.now().isoformat(),
    }
    ref.set(profile)
    return profile


def bump_stat(user_id: str, field: str, amount: int = 1):
    try:
        users_collection.document(user_id).set(
            {field: firestore.Increment(amount)}, merge=True
        )
    except Exception as e:
        print(f"Failed to bump stat {field}: {e}")


# ==================== BOOKING HELPERS ====================

def find_day_doc(room_id: str, date: str):
    day_docs = list(
        days_collection
        .where(filter=FieldFilter("room_id", "==", room_id))
        .where(filter=FieldFilter("date", "==", date))
        .limit(1)
        .stream()
    )
    return day_docs[0] if day_docs else None


def check_booking_clash(room_id: str, date: str, start_time: str, end_time: str, exclude_booking_id: str = None):
    day_doc = find_day_doc(room_id, date)
    if not day_doc:
        return False

    bookings = bookings_collection.where(filter=FieldFilter("day_id", "==", day_doc.id)).stream()
    new_start = datetime.strptime(start_time, "%H:%M")
    new_end = datetime.strptime(end_time, "%H:%M")

    for booking in bookings:
        if exclude_booking_id and booking.id == exclude_booking_id:
            continue
        data = booking.to_dict()
        existing_start = datetime.strptime(data["start_time"], "%H:%M")
        existing_end = datetime.strptime(data["end_time"], "%H:%M")
        if not (new_end <= existing_start or new_start >= existing_end):
            return True
    return False


def get_or_create_day(room_id: str, date: str):
    day_doc = find_day_doc(room_id, date)
    if day_doc:
        return day_doc.id
    _, day_ref = days_collection.add({"room_id": room_id, "date": date})
    return day_ref.id


def calculate_occupancy(room_id: str, date: str):
    day_doc = find_day_doc(room_id, date)
    if not day_doc:
        return 0.0
    bookings = list(bookings_collection.where(filter=FieldFilter("day_id", "==", day_doc.id)).stream())
    total_minutes = DAY_TOTAL_MINUTES
    booked_minutes = 0
    work_start = datetime.strptime(WORK_START, "%H:%M")
    work_end = datetime.strptime(WORK_END, "%H:%M")
    for booking in bookings:
        data = booking.to_dict()
        start = datetime.strptime(data["start_time"], "%H:%M")
        end = datetime.strptime(data["end_time"], "%H:%M")
        effective_start = max(start, work_start)
        effective_end = min(end, work_end)
        if effective_start < effective_end:
            booked_minutes += (effective_end - effective_start).seconds // 60
    return round((booked_minutes / total_minutes) * 100, 1)


def compute_free_slots(room_id: str, date: str):
    """Return list of free (start,end) windows within working hours for a room/day."""
    day_doc = find_day_doc(room_id, date)
    bookings = []
    if day_doc:
        bookings = [b.to_dict() for b in bookings_collection.where(filter=FieldFilter("day_id", "==", day_doc.id)).stream()]
    bookings.sort(key=lambda x: x["start_time"])
    free = []
    cursor = WORK_START
    for b in bookings:
        if b["start_time"] > cursor:
            free.append({"start": cursor, "end": b["start_time"]})
        if b["end_time"] > cursor:
            cursor = b["end_time"]
    if cursor < WORK_END:
        free.append({"start": cursor, "end": WORK_END})
    return free


def find_earliest_free_slot(room_id: str):
    today = datetime.now().date()
    for i in range(5):
        check_date = today + timedelta(days=i)
        date_str = check_date.strftime("%Y-%m-%d")
        free = compute_free_slots(room_id, date_str)
        if free:
            return {"date": date_str, "time": free[0]["start"]}
    return None
