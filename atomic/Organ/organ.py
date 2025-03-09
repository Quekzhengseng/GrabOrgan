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
        self, organ_id, donor_id, organ_type, retrieval_datetime, expiry_datetime,
        status, condition, blood_type, weight_grams, hla_typing, histopathology,
        storage_temp_celsius, preservation_solution, notes
    ):
        self.organ_id = organ_id
        self.donor_id = donor_id
        self.organ_type = organ_type
        self.retrieval_datetime = retrieval_datetime
        self.expiry_datetime = expiry_datetime
        self.status = status
        self.condition = condition
        self.blood_type = blood_type
        self.weight_grams = weight_grams
        self.hla_typing = hla_typing
        self.histopathology = histopathology
        self.storage_temp_celsius = storage_temp_celsius
        self.preservation_solution = preservation_solution
        self.notes = notes

    def to_dict(self):
        """Convert the object to a Firestore-compatible dictionary."""
        return {
            "organId": self.organ_id,
            "donorId": self.donor_id,
            "organType": self.organ_type,
            "retrievalDatetime": self.retrieval_datetime,  # Store as ISO string
            "expiryDatetime": self.expiry_datetime,  # Store as ISO string
            "status": self.status,
            "condition": self.condition,
            "bloodType": self.blood_type,
            "weightGrams": self.weight_grams,
            "hlaTyping": self.hla_typing,
            "histopathology": self.histopathology,
            "storageTempCelsius": self.storage_temp_celsius,
            "preservationSolution": self.preservation_solution,
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(organId, data):
        """Create an Organ object from Firestore document data."""
        return Organ(
            organ_id=organId,
            donor_id=data["donorId"],
            organ_type=data["organType"],
            retrieval_datetime=data["retrievalDatetime"],  # Corrected field name
            expiry_datetime=data["expiryDatetime"],  # Corrected field name
            status=data["status"],
            condition=data["condition"],
            blood_type=data["bloodType"],  # Corrected field name
            weight_grams=data["weightGrams"],  # Corrected field name
            hla_typing=data["hlaTyping"],  # Corrected field name
            histopathology=data["histopathology"],
            storage_temp_celsius=data["storageTempCelsius"],  # Corrected field name
            preservation_solution=data["preservationSolution"],  # Corrected field name
            notes=data["notes"]
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

        return jsonify({"success": True, "code": 200, "data": organ_list}), 200

    except Exception as e:
        return jsonify({"success": False, "code": 500, "error": str(e)}), 500

@app.route("/organ/<string:organId>", methods=['GET'])
def get_organ(organId):
    """Retrieve a specific organ by organId."""
    try:
        organ_ref = db.collection("organs").document(organId)
        doc = organ_ref.get()
        if doc.exists:
            organ_obj = Organ.from_dict(organId, doc.to_dict())
            return {"success" : True, "code":200, "data": organ_obj.to_dict()}  # Convert back to JSON-friendly format
        else:
            return jsonify({"success" : False, "code":404, "error": "Organ does not exist"}), 404

    except Exception as e:
        return jsonify({"success" : False, "code":500, "error": str(e)}), 500

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

        return jsonify({"success": True, "code": 200, "data": organ_list}), 200

    except Exception as e:
        return jsonify({"success": False, "code": 500, "error": str(e)}), 500

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

        return jsonify({"success": True, "code": 200, "data": organ_list}), 200

    except Exception as e:
        return jsonify({"success": False, "code": 500, "error": str(e)}), 500

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

        return jsonify({"success": True, "code": 200, "data": organ_list}), 200

    except Exception as e:
        return jsonify({"success": False, "code": 500, "error": str(e)}), 500

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

        return jsonify({"success": True, "code": 200, "data": organ_list}), 200

    except Exception as e:
        return jsonify({"success": False, "code": 500, "error": str(e)}), 500

@app.route("/organ", methods=['POST'])
def create_organ():
    """Create a new organ in Firestore."""
    try:
        data = request.get_json()

        # Generate a unique organId (can be done using UUID or custom logic)
        organ_id = str(uuid.uuid4())

        # Create Organ object
        organ = Organ(
            organ_id=organ_id,
            donor_id=data['donorId'],
            organ_type=data['organType'],
            retrieval_datetime=data['retrievalDatetime'],
            expiry_datetime=data['expiryDatetime'],
            status=data['status'],
            condition=data['condition'],
            blood_type=data['bloodType'],
            weight_grams=data['weightGrams'],
            hla_typing=data['hlaTyping'],
            histopathology=data['histopathology'],
            storage_temp_celsius=data['storageTempCelsius'],
            preservation_solution=data['preservationSolution'],
            notes=data['notes']
        )

        # Save organ to Firestore
        db.collection("organs").document(organ_id).set(organ.to_dict())

        return jsonify({"success": True, "code": 201, "message": "Organ created successfully", "organId": organ_id}), 201

    except Exception as e:
        return jsonify({"success": False, "code": 500, "error": str(e)}), 500

@app.route("/organ/<string:organId>", methods=['PUT'])
def update_organ(organId):
    """Update an existing organ in Firestore."""
    try:
        data = request.get_json()

        # Check if organ exists
        organ_ref = db.collection("organs").document(organId)
        doc = organ_ref.get()

        if not doc.exists:
            return jsonify({"success": False, "code": 404, "error": "Organ not found"}), 404

        # Prepare updated data
        updated_data = {
            "donorId": data.get('donorId', doc.to_dict().get('donorId')),
            "organType": data.get('organType', doc.to_dict().get('organType')),
            "retrievalDatetime": data.get('retrievalDatetime', doc.to_dict().get('retrievalDatetime')),
            "expiryDatetime": data.get('expiryDatetime', doc.to_dict().get('expiryDatetime')),
            "status": data.get('status', doc.to_dict().get('status')),
            "condition": data.get('condition', doc.to_dict().get('condition')),
            "bloodType": data.get('bloodType', doc.to_dict().get('bloodType')),
            "weightGrams": data.get('weightGrams', doc.to_dict().get('weightGrams')),
            "hlaTyping": data.get('hlaTyping', doc.to_dict().get('hlaTyping')),
            "histopathology": data.get('histopathology', doc.to_dict().get('histopathology')),
            "storageTempCelsius": data.get('storageTempCelsius', doc.to_dict().get('storageTempCelsius')),
            "preservationSolution": data.get('preservationSolution', doc.to_dict().get('preservationSolution')),
            "notes": data.get('notes', doc.to_dict().get('notes')),
        }

        # Update the organ document in Firestore
        organ_ref.update(updated_data)

        return jsonify({"success": True, "code": 200, "message": "Organ updated successfully"}), 200

    except Exception as e:
        return jsonify({"success": False, "code": 500, "error": str(e)}), 500

@app.route("/organ/<string:organId>", methods=['DELETE'])
def delete_organ(organId):
    """Delete an organ from Firestore."""
    try:
        organ_ref = db.collection("organs").document(organId)
        doc = organ_ref.get()

        if not doc.exists:
            return jsonify({"success": False, "code": 404, "error": "Organ not found"}), 404

        # Delete the organ document from Firestore
        organ_ref.delete()

        return jsonify({"success": True, "code": 200, "message": "Organ deleted successfully"}), 200

    except Exception as e:
        return jsonify({"success": False, "code": 500, "error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask server for organ management...")
    app.run(host='0.0.0.0', port=5008, debug=True)
