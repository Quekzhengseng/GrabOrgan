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

# doc_ref = db.collection("donors").document("2")
# doc_ref.set({"first": "isaac", "last": "chia", "born": 1915})
# doc_ref = db.collection("donors").document("3")
# doc_ref.set({"first": "isaiah", "last": "ng", "born": 2001})




@app.route("/donor", methods=['GET'])
def get_all():
    # Read data from firebase
    try:
        donors_ref = db.collection("donors")
        # docs = donors_ref.stream()
        docs = donors_ref.get()
        donors = [];

        for doc in docs:
            donor_data = doc.to_dict()
            donor_data["donorID"] = doc.id  # Add document ID
            donors.append(donor_data)
        return jsonify({"success" : True, "data": donors}), 200
    except Exception as e:
        return jsonify({"success" : False, "error": str(e)}), 500

        # print(f"{doc.id} => {doc.to_dict()}")

# @app.route("/donor/<string:donorId>")
# def update_donor(donorId):

if __name__ == '__main__':
    print("This is flask for " + os.path.basename(__file__) + ": manage donors ...")
    app.run(host='0.0.0.0', port=5001, debug=True)