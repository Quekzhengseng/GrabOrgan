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

# Use a service account.
cred = credentials.Certificate('Donor_IAM_Admin_SDK.json')

app = firebase_admin.initialize_app(cred)

db = firestore.client()

doc_ref = db.collection("donors").document("alovelace")
doc_ref.set({"first": "Ada", "last": "Lovelace", "born": 1815})