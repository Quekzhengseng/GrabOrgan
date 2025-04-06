import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os

app = Flask(__name__)
CORS(app)

# Load Firebase credentials
key_path = os.getenv("ORGAN_DB_KEY", "/usr/src/app/secrets/organ_Key.json") 

if not key_path or not os.path.isfile(key_path):
    raise FileNotFoundError(f"Could not find the Firebase JSON at {key_path}")

# Initialize Firestore only if it hasn't been initialized
if not firebase_admin._apps:
    cred = credentials.Certificate(key_path)  
    firebase_app = firebase_admin.initialize_app(cred, {
        'projectId': 'organs-7ede9'  # Specify the project ID here
    })


print("Firestore initialized successfully for Organ!")

db = firestore.client()

class Organ:
    def __init__(
        self, organ_id, donor_id, organ_type, blood_type, condition):
        self.organ_id = organ_id
        self.donor_id = donor_id
        self.organ_type = organ_type
        self.blood_type = blood_type
        self.condition = condition


    def to_dict(self):
        """Convert the object to a Firestore-compatible dictionary."""
        return {
            "organId": self.organ_id,
            "donorId": self.donor_id,
            "organType": self.organ_type,
            "bloodType": self.blood_type,
            "condition": self.condition,

        }

    @staticmethod
    def from_dict(organId, data):
        """Create an Organ object from Firestore document data."""
        return Organ(
            organ_id=organId,
            donor_id=data["donorId"],
            organ_type=data["organType"],
            blood_type=data["bloodType"],
            condition=data["condition"],

        )

@app.route("/organ", methods=['GET'])
def get_all_organs():
    """Retrieve all organs from Firestore."""
    try:
        organ_ref = db.collection("organs")
        docs = organ_ref.get()
        organ_list = []

        for doc in docs:
            organ_data = doc.to_dict()
            organ_data["organId"] = doc.id  # Add Firestore document ID
            organ_list.append(organ_data)

        return jsonify({"code": 200, "data": organ_list,"message": "Successfully get all organs"}), 200

    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500

@app.route("/organ/<string:organId>", methods=['GET'])
def get_organ(organId):
    """Retrieve a specific organ by organId."""
    try:
        organ_ref = db.collection("organs").document(organId)
        doc = organ_ref.get()
        if doc.exists:
            organ_obj = Organ.from_dict(organId, doc.to_dict())
            return {"code":200, "data": organ_obj.to_dict(), "message": "Successfully get organs by Id"}  # Convert back to JSON-friendly format
        else:
            return jsonify({"code":404, "message": "Organ does not exist"}), 404

    except Exception as e:
        return jsonify({"code":500, "message": str(e)}), 500

@app.route("/organ/donor/<string:donorId>", methods=['GET'])
def get_organs_for_donor(donorId):
    """Retrieve all organs for a specific donor."""
    try:
        organ_ref = db.collection("organs")
        docs = organ_ref.where('donorId', '==', donorId).get()
        organ_list = []

        for doc in docs:
            organ_data = doc.to_dict()
            organ_data["organId"] = doc.id  # Add Firestore document ID
            organ_list.append(organ_data)

        return jsonify({"code": 200, "data": organ_list, "message": "Successfully get organs by donor"}), 200

    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500

@app.route("/organ/type/<string:organType>", methods=['GET'])
def get_organs_by_type(organType):
    """Retrieve all organs of a specific type."""
    try:
        organ_ref = db.collection("organs")
        docs = organ_ref.where('organType', '==', organType).get()
        organ_list = []

        for doc in docs:
            organ_data = doc.to_dict()
            organ_data["organId"] = doc.id  # Add Firestore document ID
            organ_list.append(organ_data)

        return jsonify({"code": 200, "data": organ_list, "message": "Successfully get organs by type"}), 200

    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500

@app.route("/organ/status/<string:status>", methods=['GET'])
def get_organs_by_status(status):
    """Retrieve all organs of a specific status."""
    try:
        organ_ref = db.collection("organs")
        docs = organ_ref.where('status', '==', status).get()
        organ_list = []

        for doc in docs:
            organ_data = doc.to_dict()
            organ_data["organId"] = doc.id  # Add Firestore document ID
            organ_list.append(organ_data)

        return jsonify({"code": 200, "data": organ_list, "message": "Successfully get organs by status"}), 200

    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500

@app.route("/organ/condition/<string:condition>", methods=['GET'])
def get_organs_by_condition(condition):
    """Retrieve all organs of a specific condition."""
    try:
        organ_ref = db.collection("organs")
        docs = organ_ref.where('condition', '==', condition).get()
        organ_list = []

        for doc in docs:
            organ_data = doc.to_dict()
            organ_data["organId"] = doc.id  # Add Firestore document ID
            organ_list.append(organ_data)

        return jsonify({"code": 200, "data": organ_list, "message": "Successfully get organs by condition"}), 200

    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500

@app.route("/organ", methods=['POST'])
def create_organ():
    """Create a new organ in Firestore."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "message": "No data provided"
            }), 400

        organ = Organ(
            organ_id=data["organId"],
            donor_id=data["donorId"],
            organ_type=data["organType"],
            blood_type=data["bloodType"],
            condition=data["condition"],
        )

        db.collection("organs").document(data["organId"]).set(organ.to_dict())

        return jsonify({
            "code": 201,
            "data": organ.to_dict(),
            "message": "Organ created successfully"
        }), 201

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal server error: {str(e)}"
        }), 500

@app.route("/organ/<string:organId>", methods=['PUT'])
def update_organ(organId):
    """Update an existing organ in Firestore."""
    try:
        organ_ref = db.collection("organs").document(organId)
        doc = organ_ref.get()
        if not doc.exists:
            return jsonify(
                {
                    "code": 404,
                    "data": {
                        "organId": organId
                    },
                    "message": "Organ not found."
                }
            ), 404

        # update status
        new_data = request.get_json()
        if new_data:
            db.collection("organs").document(organId).set(new_data["data"], merge=True)
            return jsonify(
                {
                    "code": 200,
                    "data": new_data["data"]
                }
            ), 200
        else:
            return jsonify({
                "code": 400,
                "message": "No data provided for update."
            }), 400
    except Exception as e:
        print("Error: {}".format(str(e)))
        return jsonify(
            {
                "code": 500,
                "data": {
                    "organId": organId
                },
                "message": "An error occurred while updating the organ information. " + str(e)
            }
        ), 500

@app.route("/organ/<string:organId>", methods=['DELETE'])
def delete_organ(organId):
    """Delete an organ from Firestore."""
    try:
        organ_ref = db.collection("organs").document(organId)
        doc = organ_ref.get()

        if not doc.exists:
            return jsonify({"code": 404, "message": "Organ not found"}), 404

        # Delete the organ document from Firestore
        organ_ref.delete()

        return jsonify({"code": 200, "message": "Organ deleted successfully"}), 200

    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask server for organ management...")
    app.run(host='0.0.0.0', port=5010, debug=True)