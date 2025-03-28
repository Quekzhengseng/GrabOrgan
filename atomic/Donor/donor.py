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

if not key_path or not os.path.isfile(key_path):
    raise FileNotFoundError(f"Could not find the Firebase JSON at {key_path}")
# Initialize Firestore
cred = credentials.Certificate(key_path)
firebase_app = firebase_admin.initialize_app(cred)

print("Firestore initialized successfully for Donor!")


db = firestore.client()


class Donor:
    def __init__(self, donor_id, first_name, last_name, age ,date_of_birth, datetime_of_death,
                 gender, blood_type, organs, medical_history, allergies, nok_contact):
        self.donor_id = donor_id
        self.first_name = first_name
        self.last_name = last_name
        self.age = age
        self.date_of_birth = date_of_birth
        self.datetime_of_death = datetime_of_death
        self.gender = gender
        self.blood_type = blood_type
        self.organs = organs  # List of organId
        self.medical_history = medical_history  # List of medical history records
        self.allergies = allergies  # List of allergies
        self.nok_contact = nok_contact  # Next of kin contact details

    def to_dict(self):
        """Convert the object to a Firestore-compatible dictionary."""
        return {
            "firstName": self.first_name,
            "lastName": self.last_name,
            "age": self.age,
            "dateOfBirth": self.date_of_birth,
            "datetimeOfDeath": self.datetime_of_death,
            "gender": self.gender,
            "bloodType": self.blood_type,
            "organs": self.organs,
            "medicalHistory": self.medical_history,
            "allergies": self.allergies,
            "nokContact": self.nok_contact
        }

    @staticmethod
    def from_dict(donor_id, data):
        """Create a Donor object from Firestore document data."""
        return Donor(
            donor_id=donor_id,
            first_name=data["firstName"],
            last_name=data["lastName"],
            age=data["age"],
            date_of_birth=data["dateOfBirth"],
            datetime_of_death=data["datetimeOfDeath"],
            gender=data["gender"],
            blood_type=data["bloodType"],
            organs=data["organs"],
            medical_history=data["medicalHistory"],
            allergies=data["allergies"],
            nok_contact=data["nokContact"]
        )

@app.route("/donor", methods=['GET'])
def get_all():
    # Read data from firebase
    try:
        donors_ref = db.collection("donors")
        # docs = donors_ref.stream()
        docs = donors_ref.get()
        donors = {};

        for doc in docs:
            donor_data = doc.to_dict()
            donor_data["donorID"] = doc.id  # Add document ID
            donors[doc.id] = donor_data
        return jsonify({"code":200, "data": donors}), 200
    except Exception as e:
        return jsonify({"code":500, "message": str(e)}), 500


@app.route("/donor/<string:donorId>")
def get_donor(donorId):
    try:
        donors_ref = db.collection("donors").document(donorId)
        doc = donors_ref.get()
        if doc.exists:
            donor_obj = Donor.from_dict(donorId, doc.to_dict())
            return {"code":200, "data": donor_obj.to_dict()}  # Convert back to JSON-friendly format
        else:
            return jsonify({"code":404, "message": "Donor does not exist"}), 404

    except Exception as e:
        return jsonify({"code":500, "message": str(e)}), 500


@app.route("/donor/<string:donorId>", methods=['PUT'])
def update_donor(donorId):
    try:
        donors_ref = db.collection("donors").document(donorId)
        doc = donors_ref.get()
        if not doc.exists:
            return jsonify(
                {
                    "code": 404,
                    "data": {
                        "donorId": donorId
                    },
                    "message": "Donor not found."
                }
            ), 404

        # update status
        new_data = request.get_json()
        if new_data['status'] < 400:
            db.collection("donors").document(donorId).set(new_data["data"], merge=True)
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
                    "donorId": donorId
                },
                "message": "An error occurred while updating the donor information. " + str(e)
            }
        ), 500
    
@app.route("/donor", methods=['POST'])
def create_donor():
    try:
        # Get the JSON payload from the request
        donor_data = request.get_json()

        # Ensure donorId is provided in the request
        donor_id = donor_data.get("donorId")
        if not donor_id:
            return jsonify({
                "code": 400,
                "data": {},
                "message": "Donor ID is required."
            }), 400

        # Reference to the donor document in Firestore
        donor_ref = db.collection("donors").document(donor_id)
        if donor_ref.get().exists:
            return jsonify({
                "code": 409,
                "data": {"donorId": donor_id},
                "message": "Donor already exists."
            }), 409

        # Create a new Donor object
        new_donor = Donor(
            donor_id=donor_id,
            first_name=donor_data["firstName"],
            last_name=donor_data["lastName"],
            age=donor_data["age"],
            date_of_birth=donor_data["dateOfBirth"],
            datetime_of_death=donor_data.get("datetimeOfDeath"),  # Optional field
            gender=donor_data["gender"],
            blood_type=donor_data["bloodType"],
            organs=donor_data.get("organs", []),  # Optional list
            medical_history=donor_data.get("medicalHistory", []),  # Optional list
            allergies=donor_data.get("allergies", []),  # Optional list
            nok_contact=donor_data["nokContact"]
        )

        # Save the new donor to Firestore
        donor_ref.set(new_donor.to_dict())

        # Return success response
        return jsonify({
            "code": 201,
            "data": new_donor.to_dict(),
            "message": "Donor created successfully."
        }), 201

    except Exception as e:
        print("Error: {}".format(str(e)))
        return jsonify({
            "code": 500,
            "data": {},
            "message": "An error occurred while creating the donor: " + str(e)
        }), 500

@app.route("/donors/<string:donorId>", methods=['DELETE'])
def delete_donor(donorId):
    """Delete an donor from Firestore."""
    try:
        donor_ref = db.collection("donors").document(donorId)
        doc = donor_ref.get()

        if not doc.exists:
            return jsonify({"code": 404, "message": "Donor not found"}), 404

        # Delete the organ document from Firestore
        donor_ref.delete()

        return jsonify({"code": 200, "message": "Donor deleted successfully"}), 200

    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500



if __name__ == '__main__':
    print("This is flask for " + os.path.basename(__file__) + ": manage donors ...")
    app.run(host='0.0.0.0', port=5003, debug=True)