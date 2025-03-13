from datetime import datetime
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os

app = Flask(__name__)
CORS(app)

# Load Firebase credentials
key_path = os.getenv("RECIPIENT_DB_KEY") 

if not key_path or not os.path.isfile(key_path):
    raise FileNotFoundError(f"Could not find the Firebase JSON at {key_path}")

# Initialize Firestore only if it hasn't been initialized
if not firebase_admin._apps:
    cred = credentials.Certificate(key_path)  
    firebase_app = firebase_admin.initialize_app(cred, {
        'projectId': 'esd-recipient'  # Specify the project ID here
    })


print("Firestore initialized successfully for Recipient!")

db = firestore.client()

class Recipient:
    def __init__(self, recipient_id, first_name, last_name, date_of_birth,
                 gender, blood_type, organs_needed, medical_history, allergies, nok_contact):
        self.recipient_id = recipient_id
        self.first_name = first_name
        self.last_name = last_name
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
            "firstName": self.first_name,
            "lastName": self.last_name,
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
            first_name=data["firstName"],
            last_name=data["lastName"],
            date_of_birth=data["dateOfBirth"],
            gender=data["gender"],
            blood_type=data["bloodType"],
            organs_needed=data["organsNeeded"],
            medical_history=data["medicalHistory"],
            allergies=data["allergies"],
            nok_contact=data["nokContact"]
        )

@app.route("/recipient", methods=['GET'])
def get_all():
    """Retrieve all recipients from Firestore."""
    try:
        recipient_ref = db.collection("recipients")
        docs = recipient_ref.get()
        recipients = {}

        for doc in docs:
            recipient_data = doc.to_dict()
            recipient_data["recipientId"] = doc.id  # Add Firestore document ID
            recipients[doc.id] = recipient_data

        return jsonify({"code": 200, "data": recipients}), 200

    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500

@app.route("/recipient/<string:recipientId>", methods=['GET'])
def get_recipient(recipientId):
    try:
        recipient_ref = db.collection("recipients").document(recipientId)
        doc = recipient_ref.get()
        if doc.exists:
            recipient_obj = Recipient.from_dict(recipientId, doc.to_dict())
            return {"code":200, "data": recipient_obj.to_dict()}  # Convert back to JSON-friendly format
        else:
            return jsonify({"code":404, "message": "Recipient does not exist"}), 404

    except Exception as e:
        return jsonify({"code":500, "message": str(e)}), 500


@app.route("/recipient/<string:recipientId>", methods=['PUT'])
def update_recipient(recipientId):
    try:
        recipient_ref = db.collection("recipients").document(recipientId)
        doc = recipient_ref.get()
        if not doc.exists:
            return jsonify(
                {
                    "code": 404,
                    "data": {
                        "recipientId": recipientId
                    },
                    "message": "Recipient not found."
                }
            ), 404

        # update status
        new_data = request.get_json()
        if new_data['status'] < 400:
            db.collection("recipients").document(recipientId).set(new_data["data"], merge=True)
            return jsonify(
                {
                    "code": 200,
                    "data": new_data
                }
            ), 200
    except Exception as e:
        print("Error: {}".format(str(e)))
        return jsonify(
            {
                "code": 500,
                "data": {
                    "recipientId": recipientId
                },
                "message": "An error occurred while updating the recipient information. " + str(e)
            }
        ), 500
    
@app.route("/recipient/<string:recipientId>", methods=["DELETE"])
def delete_recipient(recipientId):
    try:
        recipient_ref = db.collection("recipients").document(recipientId)
        doc = recipient_ref.get()
        
        if not doc.exists:
            return jsonify(
                {
                    "code": 404,
                    "data": {
                        "recipientId": recipientId
                    },
                    "message": "Recipient not found."
                }
            ), 404

        # Delete the document
        recipient_ref.delete()

        return jsonify(
            {
                "code": 200,
                "data": {
                    "recipientId": recipientId
                },
                "message": "Recipient successfully deleted."
            }
        ), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify(
            {
                "code": 500,
                "data": {
                    "recipientId": recipientId
                },
                "message": "An error occurred while deleting the recipient. " + str(e)
            }
        ), 500


@app.route("/recipient", methods=["POST"])
def create_recipient():
    try:
        data = request.get_json()

        # Ensure donorId is provided in the request
        recipient_id = data.get("recipientId")
        if not recipient_id:
            return jsonify({
                "code": 400,
                "data": {},
                "message": "Recipient ID is required."
            }), 400

        # Reference to the donor document in Firestore
        recipient_ref = db.collection("recipients").document(recipient_id)
        if recipient_ref.get().exists:
            return jsonify({
                "code": 409,
                "data": {"recipientId": recipient_id},
                "message": "Recipient already exists."
            }), 409

        # Create a new recipient object
        new_recipient = Recipient(
            recipient_id=recipient_id,
            first_name=data["firstName"],
            last_name=data["lastName"],
            date_of_birth=data["dateOfBirth"],
            gender=data["gender"],
            blood_type=data["bloodType"],
            medical_history=data["medicalHistory"],
            organs_needed=data["organsNeeded"],
            allergies=data["allergies"],
            nok_contact= data["nokContact"],
            )
        

        # Store the recipient data in Firestore
        recipient_ref = db.collection("recipients").document(recipient_id)
        recipient_ref.set(new_recipient.to_dict())

        return jsonify(
            {
                "code": 201,
                "data": new_recipient.to_dict(),
                "message": "Recipient successfully created."
            }
        ), 201

    except Exception as e:
        print("Error:", str(e))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred while creating the recipient. " + str(e)
            }
        ), 500

if __name__ == '__main__':
    print("Starting Flask server for recipient management...")
    app.run(host='0.0.0.0', port=5013, debug=True)
