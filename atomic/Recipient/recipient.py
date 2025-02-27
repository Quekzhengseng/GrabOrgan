from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os

app = Flask(__name__)
CORS(app)

# Load Firebase credentials
key_path = os.getenv("RECIPIENT_DB_KEY", "secrets/firebase-key.json") 

if not key_path or not os.path.isfile(key_path):
    raise FileNotFoundError(f"Could not find the Firebase JSON at {key_path}")

# Initialize Firestore only if it hasn't been initialized
if not firebase_admin._apps:
    cred = credentials.Certificate("secrets/firebase-key.json")
    firebase_app = firebase_admin.initialize_app(cred, {
        'projectId': 'esd-recipient'  # Specify the project ID here
    })


print("Firestore initialized successfully for Recipient!")

db = firestore.client()

class Recipient:
    def __init__(self, recipient_id, first_name, last_name, date_of_birth,
                 gender, blood_type, organs_needed, medical_history, allergies, nok_contact):
        self.recipient_id = recipient_id
        self.name = {"firstName": first_name, "lastName": last_name}
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.blood_type = blood_type
        self.organs_needed = organs_needed
        self.medical_history = medical_history
        self.allergies = allergies
        self.nok_contact = nok_contact

    def to_dict(self):
        """Convert the object to a Firestore-compatible dictionary."""
        return {
            "name": self.name,
            "dateOfBirth": self.date_of_birth,
            "gender": self.gender,
            "bloodType": self.blood_type,
            "organsNeeded": self.organs_needed,
            "medicalHistory": self.medical_history,
            "allergies": self.allergies,
            "nokContact": self.nok_contact
        }

    @staticmethod
    def from_dict(recipient_id, data):
        """Create a Recipient object from Firestore document data."""
        return Recipient(
            recipient_id=recipient_id,
            first_name=data["name"]["firstName"],
            last_name=data["name"]["lastName"],
            date_of_birth=data["dateOfBirth"],
            gender=data["gender"],
            blood_type=data["bloodType"],
            organs_needed=data["organsNeeded"],
            medical_history=data["medicalHistory"],
            allergies=data["allergies"],
            nok_contact=data["nokContact"]
        )

@app.route("/", methods=['GET'])
def get_all():
    """Retrieve all recipients from Firestore."""
    try:
        recipient_ref = db.collection("recipients")
        docs = recipient_ref.get()
        recipient_list = []

        for doc in docs:
            recipient_data = doc.to_dict()
            recipient_data["recipientID"] = doc.id  # Add Firestore document ID
            recipient_list.append(recipient_data)

        return jsonify({"success": True, "code": 200, "data": recipient_list}), 200

    except Exception as e:
        return jsonify({"success": False, "code": 500, "error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask server for recipient management...")
    app.run(host='0.0.0.0', port=5001)
