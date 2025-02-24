from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from os import environ
import os


app = Flask(__name__)

CORS(app)

# Load the key from an environment variable
key_path = os.getenv("DONOR_DB_KEY")

# Initialize Firestore
cred = credentials.Certificate(key_path)
app = firebase_admin.initialize_app(cred)

db = firestore.client()

doc_ref = db.collection("donors").document("isaidchia")
doc_ref.set({"first": "isaac", "last": "chia", "born": 1915})

# Read data from firebase
users_ref = db.collection("donors")
docs = users_ref.stream()

for doc in docs:
    print(f"{doc.id} => {doc.to_dict()}")

def get_all():
    donor_dict = db.collection("donors")