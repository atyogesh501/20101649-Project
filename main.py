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