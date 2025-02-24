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
firebase_app = firebase_admin.initialize_app(cred)

db = firestore.client()

# doc_ref = db.collection("donors").document("isaidchia")
# doc_ref.set({"first": "isaac", "last": "chia", "born": 1915})




# @app.route("/donor", methods=['GET'])
def get_all():
    # Read data from firebase
    donors_ref = db.collection("donors")
    # docs = donors_ref.stream()
    docs = donors_ref.get()
    for doc in docs:
        print(f"{doc.id} => {doc.to_dict()}")

# @app.route("/donor/<string:donorId>")
# def update_donor(donorId):

if __name__ == '__main__':
    print("This is flask for " + os.path.basename(__file__) + ": manage donors ...")
    app.run(host='0.0.0.0', port=5001, debug=True)