import os
import uuid
import json
import base64

from flask import Flask, request, render_template, redirect, url_for, jsonify
import google.oauth2.id_token
from google.auth.transport import requests
from datetime import datetime, timedelta
from google.oauth2 import service_account

from google.cloud import firestore, storage
from google.auth.exceptions import DefaultCredentialsError
from google.cloud.firestore_v1.base_query import FieldFilter


app = Flask(__name__, static_folder="static", template_folder="templets")

gcpKey="ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsCiAgInByb2plY3RfaWQiOiAiYm9vbWluZy1vcmRlci00OTc2MTEtZjgiLAogICJwcml2YXRlX2tleV9pZCI6ICI1ZWY5YTA4OWI3YjhjYTUwNzIyMmQ5MmE1ZGNjN2QyYjYzYWRjN2ExIiwKICAicHJpdmF0ZV9rZXkiOiAiLS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tXG5NSUlFdlFJQkFEQU5CZ2txaGtpRzl3MEJBUUVGQUFTQ0JLY3dnZ1NqQWdFQUFvSUJBUUMyTkdiVG1mT0RtQTlnXG42aFphQ2ZNdlRZeWt6UHh1OTFzd2dTaEQ2SWhKZ3oxNXFkQXk5dG13QWdRZTRFM3g1N1B3RmIxRXdEd2pGeG92XG5YYmxrMDhycDBxZThHS1Nhck5MWmlpck9BQVhSR0tGd0U5WC9BbmNwUnVMNVM5UWd2ZVIyeGpIMVhlckF2a1ZpXG5sN2pyZCtDRVVYRWQyRnVkYk5jMGwzUVQvTTZpVmpmZDZrajM0elNHSGsyTTlHR1d6d0xKT1RTZVFheFJIYWVlXG40ZjB2QS84WFlicXNUWEZiY041dVR4d3FvUS9TVVZ6c2dDRWtYenBJeWFadFYxMDNYK2JuWGtabHcvUnZHbjJIXG40LzBPaVRwMnhITmFFbXJJYU5XY25OakdUZWdDb09MT1RrNUhYdFlGblZaZUVaZXZDMXZ2dGpxQUxnL1B3MW5TXG5Rb1VDOEJ0ZkFnTUJBQUVDZ2dFQUM0OWJqc1ZQdStPajVpUXo4dFo2eFYrSU10U0dsNHUrRDEvQ2JEeU9tUXRvXG5sUlYvRGh5M1J3RjV2WFBCdmoxVEgwSmgxY0RVaisxaFRld0dYUzFLekhiL0NXSU8zM2xqajBYQzNYc0c0M05LXG5tcy9IWGZ5TUR1UmVkaTZuY01SYmdHV211Y2lSb2xUd0ZnZEdSam8rMW1aTVpQWmJLYXZFSTZRUVMweFkxOWZCXG5BYlMwVExwcXRjV3p5TjQwTFlWUUlZSmdhY01Vc1hyRjJPZ0ZaZUc4bmJzcmNEa2hCYnY5dWw0dEVmWkU4VG1QXG5JcnlCVFh5NVJNbXU2NnhlVndxKzBvV1d0YysydDBjTFpkL2VCOVJUOTAwOTJxTm9ZMVJadUtITThuUXYyRjRLXG5GbDJBOGtGTk5CcWNya2RMNXFpcmlZdTRkU1ZvOFdsY0Z3VlBqbkFBb1FLQmdRRHM5WUd4TEU1Vi9zcWZSdUFNXG53R0xhaFFsRitEU0R0akdMOWNxWm1xMFRaTkJQeHF4bHh2eVZ2Rk9hcVpTVzRNc01GUElmN2djTCtnbDFGenhKXG5HRUYxb1c0SCtuVG1DYTJ4Njd5SzVYa2RxUEgzYmJJQ3pMNHRzVXZVMjBHSHY2dnFzdWFWRmVrZXc4ajN2eGp4XG44Z0ZIQ3FXUlhiUXNadkRhdTgvMkIrMWw1d0tCZ1FERTJJcXppU3JDc0M3RVp6UW94WldOYndIaVU1VFRtMU1YXG5YdGt2dnNCcTdnNVVKM2pUZi9PRVJXSGQyUUl5UzJJWGNVQXVLRTRwQ3ZlZk5xQnZKOHQxQXl4aHJFeHdHdkUvXG5qREVPY0ZZd2gxQmhsR0UwZDM4QVJUdzdNTXYxR1ZnUTFSNmZlUHlWVHVTeXlwQVlBdklPMlFzZWpaemFmanF6XG5SaU5Zc1diL3lRS0JnREdtYjNwVU1rWEtrV0kyVTVQWWE5NGxxZi9ETmgyeSswYThSYXRSd1pvaXNaTkZxYkhaXG5zK3NiL3RpVlY5RVZZUFl6SFZpYlkxYWJHWWd6U2lwMnJxQ2JKcGI5WDZranRnVmx3NmZHMVUzbHJHMlB5cERUXG5uYld0UkpwaEpxWHUvM0s1OFo2amJLbEpsTDUwaUNHSjk4S085SW8wL0IraG9pM3kxR3hVMU9WWkFvR0FXMC9iXG4zM2EwcUVWVUhIV0hZNVpzVG9SOUNrRWRXNS9FeHFXUCtDN3pVV2NHckpEMjRwMkxHQU9iWjI3Z0x2WjdGVWJLXG5yOTZ3aXlkMFFKMzFoRHFnamJJZ0oxcm14bVlwSFFKcVN6bGZNZm5ERnREZTJwaklDQmNWM3BzL01YNUZOT0czXG41K0FXd3lncXZLbHNlRWI5aEZlNGFiN2xVUkdYSjB4VTN6TEVCY2tDZ1lFQXYrUmVXTjJEUHVFTDZVeWhLbkh3XG56MXFRTjdkK0o3NHRrRlh2YTl6WnY0bnZaeksvdHdOdm14bVhUVWNMTUMzTzFWNkQ1VzFWT3dxbUFRcU5LYXZwXG5mRGZhL2IwZE5QKzZGaGkxdTVMaHU2TTJ2UlhwbDYzRkdLdFdqbHpWSWIvZUZnL2lXQXp1b3FNVGw5S1dSb2Z1XG41VStTQ0pZaEFMcjZvTzNBbjhLT2Rhbz1cbi0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS1cbiIsCiAgImNsaWVudF9lbWFpbCI6ICJib29taW5nLW9yZGVyLTQ5NzYxMS1mOEBhcHBzcG90LmdzZXJ2aWNlYWNjb3VudC5jb20iLAogICJjbGllbnRfaWQiOiAiMTA5OTM1Mzc4MTg5OTE5MTIzMDM2IiwKICAiYXV0aF91cmkiOiAiaHR0cHM6Ly9hY2NvdW50cy5nb29nbGUuY29tL28vb2F1dGgyL2F1dGgiLAogICJ0b2tlbl91cmkiOiAiaHR0cHM6Ly9vYXV0aDIuZ29vZ2xlYXBpcy5jb20vdG9rZW4iLAogICJhdXRoX3Byb3ZpZGVyX3g1MDlfY2VydF91cmwiOiAiaHR0cHM6Ly93d3cuZ29vZ2xlYXBpcy5jb20vb2F1dGgyL3YxL2NlcnRzIiwKICAiY2xpZW50X3g1MDlfY2VydF91cmwiOiAiaHR0cHM6Ly93d3cuZ29vZ2xlYXBpcy5jb20vcm9ib3QvdjEvbWV0YWRhdGEveDUwOS9ib29taW5nLW9yZGVyLTQ5NzYxMS1mOCU0MGFwcHNwb3QuZ3NlcnZpY2VhY2NvdW50LmNvbSIsCiAgInVuaXZlcnNlX2RvbWFpbiI6ICJnb29nbGVhcGlzLmNvbSIKfQo="


service_account_info = json.loads(
    base64.b64decode(gcpKey).decode("utf-8")
)


credentials = service_account.Credentials.from_service_account_info(
    service_account_info
)

STORAGE_BUCKET = "booming-order-497611-f8.appspot.com"


WORK_START = "00:00"
WORK_END = "23:59"
DAY_TOTAL_MINUTES = 24 * 60

def get_firestore():
    try:
        return firestore.Client(
            project=service_account_info["project_id"],
            credentials=credentials,

        )
    except DefaultCredentialsError:
        print("Firestore credentials are missing! Please set up your credentials.")
        return None
    except AttributeError as e:
        print(f"Firestore encountered an AttributeError: {e}")
        return None


def get_storage_client():
    try:
        return storage.Client(
            project=service_account_info["project_id"],
            credentials=credentials
        )
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




# ==================== SHARED ACTION SERVICES ====================
# Core service functions for room and booking operations (CRUD).
# Used by HTTP route handlers to perform business logic.

def _find_room_by_name_or_id(value: str):
    """Resolve a room by its document id first, then by (case-insensitive) name."""
    if not value:
        return None
    doc = rooms_collection.document(value).get()
    if doc.exists:
        return doc_to_dict(doc)
    for r in rooms_collection.stream():
        data = doc_to_dict(r)
        if data.get("name", "").strip().lower() == value.strip().lower():
            return data
    return None


def _valid_time(t: str) -> bool:
    try:
        datetime.strptime(t, "%H:%M")
        return True
    except (ValueError, TypeError):
        return False


def _valid_date(d: str) -> bool:
    try:
        datetime.strptime(d, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def create_room_svc(user: dict, room_name: str):
    room_name = (room_name or "").strip()
    if not room_name:
        return {"error": "Please provide a room name."}
    existing = list(rooms_collection.where(filter=FieldFilter("name", "==", room_name)).limit(1).stream())
    if existing:
        return {"error": f"A room named '{room_name}' already exists."}
    _, ref = rooms_collection.add({
        "name": room_name,
        "created_by": user["user_id"],
        "created_by_email": user["email"],
        "created_at": datetime.now().isoformat(),
    })
    bump_stat(user["user_id"], "rooms_created")
    return {"success": True, "room_id": ref.id, "room_name": room_name}


def book_room_svc(user: dict, room_ref: str, date: str, start_time: str, end_time: str, meeting_name: str):
    room = _find_room_by_name_or_id(room_ref)
    if not room:
        return {"error": f"I couldn't find a room called '{room_ref}'."}
    meeting_name = (meeting_name or "").strip()
    if not meeting_name:
        return {"error": "Please give the meeting a name."}
    if not _valid_date(date):
        return {"error": "That date isn't valid. Use YYYY-MM-DD."}
    if not (_valid_time(start_time) and _valid_time(end_time)):
        return {"error": "Those times aren't valid. Use HH:MM (24h)."}
    if start_time >= end_time:
        return {"error": "End time must be after start time."}
    if check_booking_clash(room["_id"], date, start_time, end_time):
        return {"error": f"{room['name']} is already booked during that window on {date}."}

    day_id = get_or_create_day(room["_id"], date)
    _, ref = bookings_collection.add({
        "day_id": day_id,
        "room_id": room["_id"],
        "room_name": room["name"],
        "meeting_name": meeting_name,
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "user_id": user["user_id"],
        "user_email": user["email"],
        "created_at": datetime.now().isoformat(),
    })
    bump_stat(user["user_id"], "bookings_created")
    return {
        "success": True,
        "booking_id": ref.id,
        "room_name": room["name"],
        "meeting_name": meeting_name,
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
    }


def _find_user_booking(user: dict, meeting_name: str = "", date: str = "", room_ref: str = ""):
    """Best-effort match of one of the current user's bookings from loose criteria."""
    mine = [doc_to_dict(d) for d in bookings_collection.where(filter=FieldFilter("user_id", "==", user["user_id"])).stream()]
    room = _find_room_by_name_or_id(room_ref) if room_ref else None
    matches = []
    for b in mine:
        if meeting_name and meeting_name.strip().lower() not in b.get("meeting_name", "").lower():
            continue
        if date and b.get("date") != date:
            continue
        if room and b.get("room_id") != room["_id"]:
            continue
        matches.append(b)
    return matches


def cancel_booking_svc(user: dict, meeting_name: str = "", date: str = "", room_ref: str = ""):
    matches = _find_user_booking(user, meeting_name, date, room_ref)
    if not matches:
        return {"error": "I couldn't find a matching booking of yours to cancel."}
    if len(matches) > 1:
        summary = "; ".join(f"{m.get('meeting_name')} in {m.get('room_name')} on {m.get('date')} {m.get('start_time')}-{m.get('end_time')}" for m in matches[:5])
        return {"error": f"I found multiple matching bookings: {summary}. Please be more specific (name + date)."}
    b = matches[0]
    bookings_collection.document(b["_id"]).delete()
    bump_stat(user["user_id"], "bookings_deleted")
    return {"success": True, "cancelled": b.get("meeting_name"), "room_name": b.get("room_name"), "date": b.get("date"), "start_time": b.get("start_time"), "end_time": b.get("end_time")}


def reschedule_booking_svc(user: dict, meeting_name: str = "", date: str = "", room_ref: str = "",
                           new_date: str = "", new_start: str = "", new_end: str = ""):
    matches = _find_user_booking(user, meeting_name, date, room_ref)
    if not matches:
        return {"error": "I couldn't find a matching booking of yours to reschedule."}
    if len(matches) > 1:
        return {"error": "I found multiple matching bookings. Please specify the meeting name and current date."}
    b = matches[0]
    target_date = new_date or b.get("date")
    target_start = new_start or b.get("start_time")
    target_end = new_end or b.get("end_time")
    if not _valid_date(target_date) or not (_valid_time(target_start) and _valid_time(target_end)):
        return {"error": "The new date/time isn't valid."}
    if target_start >= target_end:
        return {"error": "End time must be after start time."}
    if check_booking_clash(b["room_id"], target_date, target_start, target_end, b["_id"]):
        return {"error": f"{b.get('room_name')} is already booked during that new window."}
    day_id = get_or_create_day(b["room_id"], target_date)
    bookings_collection.document(b["_id"]).update({
        "day_id": day_id,
        "date": target_date,
        "start_time": target_start,
        "end_time": target_end,
        "updated_at": datetime.now().isoformat(),
    })
    bump_stat(user["user_id"], "bookings_edited")
    return {"success": True, "meeting_name": b.get("meeting_name"), "room_name": b.get("room_name"), "date": target_date, "start_time": target_start, "end_time": target_end}
    
    
# ==================== ROUTES ====================

@app.route("/", methods=["GET"])
def home():
    user = get_user_data()
    rooms = [doc_to_dict(doc) for doc in rooms_collection.stream()]
    return render_template("index.html", user=user, rooms=rooms)


@app.route("/add-room", methods=["POST"])
def add_room():
    user = get_user_data()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    room_name = (request.form.get("room_name", "") or "").strip()
    if not room_name:
        return jsonify({"error": "Please enter a room name"}), 400

    existing = list(rooms_collection.where(filter=FieldFilter("name", "==", room_name)).limit(1).stream())
    if existing:
        return jsonify({"error": "A room with this name already exists!"}), 400

    _, ref = rooms_collection.add({
        "name": room_name,
        "created_by": user["user_id"],
        "created_by_email": user["email"],
        "created_at": datetime.now().isoformat(),
    })
    bump_stat(user["user_id"], "rooms_created")
    return jsonify({
        "success": True,
        "room": {
            "_id": ref.id,
            "name": room_name,
            "created_by": user["user_id"],
            "created_by_email": user["email"],
        },
    })


@app.route("/delete-room/<room_id>", methods=["POST"])
def delete_room(room_id):
    user = get_user_data()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    room_doc = rooms_collection.document(room_id).get()
    if not room_doc.exists:
        return jsonify({"error": "Room not found"}), 404

    room = room_doc.to_dict()
    if room.get("created_by") != user["user_id"]:
        return jsonify({"error": "Only the room creator can delete this room"}), 403

    days = list(days_collection.where(filter=FieldFilter("room_id", "==", room_id)).stream())
    for day in days:
        booking = list(bookings_collection.where(filter=FieldFilter("day_id", "==", day.id)).limit(1).stream())
        if booking:
            return jsonify({"error": "Cannot delete room with existing bookings"}), 400

    for day in days:
        days_collection.document(day.id).delete()
    rooms_collection.document(room_id).delete()
    bump_stat(user["user_id"], "rooms_deleted")
    return jsonify({"success": True})

@app.route("/book-room", methods=["POST"])
def book_room():
    user = get_user_data()
    if not user:
        return redirect(url_for("home"), code=303)

    room_id = request.form["room_id"]
    date = request.form["date"]
    start_time = request.form["start_time"]
    end_time = request.form["end_time"]
    meeting_name = (request.form.get("meeting_name", "") or "").strip()

    if not meeting_name:
        return jsonify({"error": "Please enter a meeting name"}), 400
    if start_time >= end_time:
        return jsonify({"error": "End time must be after start time"}), 400
    if check_booking_clash(room_id, date, start_time, end_time):
        return jsonify({"error": "This time slot clashes with an existing booking"}), 400

    day_id = get_or_create_day(room_id, date)
    room_doc = rooms_collection.document(room_id).get()
    if not room_doc.exists:
        return jsonify({"error": "Room not found"}), 404
    room = room_doc.to_dict()

    bookings_collection.add({
        "day_id": day_id,
        "room_id": room_id,
        "room_name": room["name"],
        "meeting_name": meeting_name,
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "user_id": user["user_id"],
        "user_email": user["email"],
        "created_at": datetime.now().isoformat(),
    })
    bump_stat(user["user_id"], "bookings_created")
    return jsonify({"success": True})



@app.route("/my-bookings", methods=["GET"])
def get_my_bookings():
    user = get_user_data()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    room_id = request.args.get("room_id")
    query = bookings_collection.where(filter=FieldFilter("user_id", "==", user["user_id"]))
    if room_id:
        query = query.where(filter=FieldFilter("room_id", "==", room_id))

    bookings = [doc_to_dict(doc) for doc in query.stream()]
    bookings.sort(key=lambda b: (b.get("date", ""), b.get("start_time", "")))
    return jsonify({"bookings": bookings})


@app.route("/delete-booking/<booking_id>", methods=["POST"])
def delete_booking(booking_id):
    user = get_user_data()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    booking_doc = bookings_collection.document(booking_id).get()
    if not booking_doc.exists:
        return jsonify({"error": "Booking not found"}), 404

    booking = booking_doc.to_dict()
    if booking.get("user_id") != user["user_id"]:
        return jsonify({"error": "You can only delete your own bookings"}), 403

    bookings_collection.document(booking_id).delete()
    bump_stat(user["user_id"], "bookings_deleted")
    return jsonify({"success": True})


@app.route("/edit-booking/<booking_id>", methods=["GET"])
def edit_booking_page(booking_id):
    user = get_user_data()
    if not user:
        return redirect(url_for("home"), code=303)

    booking_doc = bookings_collection.document(booking_id).get()
    if not booking_doc.exists:
        return redirect(url_for("home"), code=303)

    booking = doc_to_dict(booking_doc)
    if booking.get("user_id") != user["user_id"]:
        return redirect(url_for("home"), code=303)

    rooms = [doc_to_dict(doc) for doc in rooms_collection.stream()]
    return render_template("edit_booking.html", user=user, booking=booking, rooms=rooms)


@app.route("/update-booking/<booking_id>", methods=["POST"])
def update_booking(booking_id):
    user = get_user_data()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    booking_doc = bookings_collection.document(booking_id).get()
    if not booking_doc.exists:
        return jsonify({"error": "Booking not found"}), 404

    booking = booking_doc.to_dict()
    if booking.get("user_id") != user["user_id"]:
        return jsonify({"error": "You can only edit your own bookings"}), 403

    room_id = request.form["room_id"]
    date = request.form["date"]
    start_time = request.form["start_time"]
    end_time = request.form["end_time"]
    meeting_name = (request.form.get("meeting_name", "") or "").strip() or booking.get("meeting_name", "")

    if not meeting_name:
        return jsonify({"error": "Please enter a meeting name"}), 400
    if start_time >= end_time:
        return jsonify({"error": "End time must be after start time"}), 400
    if check_booking_clash(room_id, date, start_time, end_time, booking_id):
        return jsonify({"error": "This time slot clashes with an existing booking"}), 400

    day_id = get_or_create_day(room_id, date)
    room_doc = rooms_collection.document(room_id).get()
    if not room_doc.exists:
        return jsonify({"error": "Room not found"}), 404
    room = room_doc.to_dict()

    bookings_collection.document(booking_id).update({
        "day_id": day_id,
        "room_id": room_id,
        "room_name": room["name"],
        "meeting_name": meeting_name,
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "updated_at": datetime.now().isoformat(),
    })
    bump_stat(user["user_id"], "bookings_edited")
    return jsonify({"success": True})


@app.route("/room/<room_id>", methods=["GET"])
def view_room(room_id):
    user = get_user_data()
    room_doc = rooms_collection.document(room_id).get()
    if not room_doc.exists:
        return redirect(url_for("home"), code=303)

    room = doc_to_dict(room_doc)
    bookings = [doc_to_dict(doc) for doc in bookings_collection.where(filter=FieldFilter("room_id", "==", room_id)).stream()]
    bookings.sort(key=lambda b: (b.get("date", ""), b.get("start_time", "")))

    today = datetime.now().date()
    occupancy_data = []
    calendar_data = []
    for i in range(5):
        check_date = today + timedelta(days=i)
        date_str = check_date.strftime("%Y-%m-%d")
        occupancy = calculate_occupancy(room_id, date_str)
        occupancy_data.append({
            "date": date_str,
            "day_name": check_date.strftime("%A"),
            "occupancy": occupancy,
        })
        day_bookings = [b for b in bookings if b["date"] == date_str]
        calendar_data.append({
            "date": date_str,
            "day_name": check_date.strftime("%A"),
            "bookings": day_bookings,
        })

    earliest_free = find_earliest_free_slot(room_id)

    return render_template(
        "room.html",
        user=user,
        room=room,
        bookings=bookings,
        occupancy_data=occupancy_data,
        calendar_data=calendar_data,
        earliest_free=earliest_free,
    )


@app.route("/filter-by-day", methods=["GET"])
def filter_by_day():
    get_user_data()
    date = request.args.get("date")
    bookings = [doc_to_dict(doc) for doc in bookings_collection.where(filter=FieldFilter("date", "==", date)).stream()]
    bookings.sort(key=lambda b: (b.get("room_name", ""), b.get("start_time", "")))
    return jsonify({"bookings": bookings})


@app.route("/room-bookings/<room_id>", methods=["GET"])
def get_room_bookings(room_id):
    get_user_data()
    date = request.args.get("date")
    query = bookings_collection.where(filter=FieldFilter("room_id", "==", room_id))
    if date:
        query = query.where(filter=FieldFilter("date", "==", date))
    bookings = [doc_to_dict(doc) for doc in query.stream()]
    bookings.sort(key=lambda b: (b.get("date", ""), b.get("start_time", "")))
    return jsonify({"bookings": bookings})


# ==================== PROFILE ====================

@app.route("/profile", methods=["GET"])
def profile_page():
    user = get_user_data()
    if not user:
        return redirect(url_for("home"), code=303)

    profile = get_user_profile(user["user_id"], user["email"], user["name"])

    my_rooms = [doc_to_dict(d) for d in rooms_collection.where(filter=FieldFilter("created_by", "==", user["user_id"])).stream()]
    my_bookings = [doc_to_dict(d) for d in bookings_collection.where(filter=FieldFilter("user_id", "==", user["user_id"])).stream()]
    my_bookings.sort(key=lambda b: (b.get("date", ""), b.get("start_time", "")), reverse=True)

    today_str = datetime.now().strftime("%Y-%m-%d")
    upcoming = [b for b in my_bookings if b.get("date", "") >= today_str]

    stats = {
        "rooms_created": profile.get("rooms_created", 0),
        "rooms_deleted": profile.get("rooms_deleted", 0),
        "bookings_created": profile.get("bookings_created", 0),
        "bookings_deleted": profile.get("bookings_deleted", 0),
        "bookings_edited": profile.get("bookings_edited", 0),
        "active_rooms": len(my_rooms),
        "active_bookings": len(my_bookings),
        "upcoming_bookings": len(upcoming),
    }

    return render_template(
        "profile.html",
        user=user,
        profile=profile,
        stats=stats,
        my_rooms=my_rooms,
        recent_bookings=my_bookings[:8],
    )


# ==================== ABOUT ====================

@app.route("/about", methods=["GET"])
def about_page():
    user = get_user_data()
    if not user:
        return redirect(url_for("home"), code=303)

    # Live totals so the About page reflects real usage.
    total_rooms = len(list(rooms_collection.stream()))
    total_bookings = len(list(bookings_collection.stream()))
    total_users = len(list(users_collection.stream()))

    return render_template(
        "about.html",
        user=user,
        totals={
            "rooms": total_rooms,
            "bookings": total_bookings,
            "users": total_users,
        },
    )


@app.route("/upload-photo", methods=["POST"])
def upload_photo():
    user = get_user_data()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    photo = request.files.get("photo")
    if photo is None:
        return jsonify({"error": "No file uploaded"}), 400

    if photo.content_type not in ("image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"):
        return jsonify({"error": "Please upload a PNG, JPG, WEBP or GIF image"}), 400

    client = get_storage_client()
    if client is None:
        return jsonify({"error": "Storage is not configured"}), 500

    try:
        bucket = client.bucket(STORAGE_BUCKET)
        ext = (photo.filename or "img").split(".")[-1].lower()
        blob_name = f"profile_pics/{user['user_id']}/{uuid.uuid4().hex}.{ext}"
        blob = bucket.blob(blob_name)
        contents = photo.read()
        blob.upload_from_string(contents, content_type=photo.content_type)
        try:
            blob.make_public()
            photo_url = blob.public_url
        except Exception:
            photo_url = f"https://storage.googleapis.com/{STORAGE_BUCKET}/{blob_name}"

        users_collection.document(user["user_id"]).set({"photo_url": photo_url}, merge=True)
        return jsonify({"success": True, "photo_url": photo_url})
    except Exception as e:
        print(f"Photo upload error: {e}")
        return jsonify({"error": f"Upload failed: {e}"}), 500


@app.route("/update-profile", methods=["POST"])
def update_profile():
    user = get_user_data()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    display_name = request.form["display_name"]
    users_collection.document(user["user_id"]).set(
        {"display_name": display_name.strip() or user["email"]}, merge=True
    )
    return jsonify({"success": True})


# ==================== BOOKINGS GRAPH DATA ====================

def _to_minutes(t):
    h, m = t.split(":")
    return int(h) * 60 + int(m)


@app.route("/room-graph/<room_id>", methods=["GET"])
def room_graph(room_id):
    """Return bookings for a room on a date shaped for a timeline graph."""
    user = get_user_data()
    date = request.args.get("date")
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    day_doc = find_day_doc(room_id, date)
    bookings = []
    if day_doc:
        bookings = [doc_to_dict(b) for b in bookings_collection.where(filter=FieldFilter("day_id", "==", day_doc.id)).stream()]
    bookings.sort(key=lambda b: b.get("start_time", ""))

    items = []
    for b in bookings:
        items.append({
            "id": b["_id"],
            "start": b["start_time"],
            "end": b["end_time"],
            "start_min": _to_minutes(b["start_time"]),
            "end_min": _to_minutes(b["end_time"]),
            "user_email": b.get("user_email", ""),
            "is_mine": bool(user and b.get("user_id") == user["user_id"]),
        })

    free = compute_free_slots(room_id, date)
    return jsonify({
        "date": date,
        "work_start": WORK_START,
        "work_end": WORK_END,
        "work_start_min": _to_minutes(WORK_START),
        "work_end_min": _to_minutes(WORK_END),
        "bookings": items,
        "free_slots": free,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)