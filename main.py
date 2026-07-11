import os
import uuid

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
