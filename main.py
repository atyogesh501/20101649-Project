import os
import uuid

from flask import Flask, request
import google.oauth2.id_token
from google.auth.transport import requests


app = Flask(__name__, static_folder="static", template_folder="templates")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "firestoreDetails.json"

STORAGE_BUCKET = "booming-order-497611-f8.appspot.com"


WORK_START = "00:00"
WORK_END = "23:59"
DAY_TOTAL_MINUTES = 24 * 60

def get_user_token():
    id_token = request.cookies.get("token")
    if id_token:
        try:
            firebase_request_adapter = requests.Request()
            return google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        except ValueError as e:
            print("Error verifying Firebase token:", e)
    return None
