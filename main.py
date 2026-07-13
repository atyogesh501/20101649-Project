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