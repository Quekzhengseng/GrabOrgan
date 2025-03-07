from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
from os import environ
import os

app = Flask(__name__)
CORS(app)

# Load the key from an environment variable
key_path = os.getenv("PERSONAL_DATA_DB_KEY")

if not key_path or not os.path.isfile(key_path):
    raise FileNotFoundError(f"Could not find the Firebase JSON at {key_path}")

# Initialize Firestore
cred = credentials.Certificate(key_path)
firebase_app = firebase_admin.initialize_app(cred)
print("Firestore initialized successfully for Person!")

db = firestore.client()


class Person:
    def __init__(self, person_id, first_name, last_name, date_of_birth, nok_contact):
        self.person_id = person_id
        self.first_name = first_name
        self.last_name = last_name
        self.date_of_birth = date_of_birth
        self.nok_contact = nok_contact  # Next of kin contact details

    def to_dict(self):
        """Convert the object to a Firestore-compatible dictionary."""
        return {
            "firstName": self.first_name,
            "lastName": self.last_name,
            "dateOfBirth": self.date_of_birth,
            "nokContact": self.nok_contact
        }

    @staticmethod
    def from_dict(person_id, data):
        """Create a Person object from Firestore document data."""
        return Person(
            person_id=person_id,
            first_name=data.get("firstName"),
            last_name=data.get("lastName"),
            date_of_birth=data.get("dateOfBirth"),
            nok_contact=data.get("nokContact")
        )


@app.route("/person", methods=['GET'])
def get_all():
    # Read data from Firestore
    try:
        persons_ref = db.collection("PersonalData")
        docs = persons_ref.get()
        persons = {}

        for doc in docs:
            person_data = doc.to_dict()
            person_data["personID"] = doc.id  # Include the document ID
            persons[doc.id] = person_data
        return jsonify({"success": True, "code": 200, "data": persons}), 200
    except Exception as e:
        return jsonify({"success": False, "code": 500, "error": str(e)}), 500


@app.route("/person/<string:personId>")
def get_person(personId):
    try:
        person_ref = db.collection("PersonalData").document(personId)
        doc = person_ref.get()
        if doc.exists:
            person_obj = Person.from_dict(personId, doc.to_dict())
            return jsonify({"success": True, "code": 200, "data": person_obj.to_dict()})
        else:
            return jsonify({"success": False, "code": 404, "error": "Person does not exist"}), 404

    except Exception as e:
        return jsonify({"success": False, "code": 500, "error": str(e)}), 500


@app.route("/person/<string:personId>", methods=['PUT'])
def update_person(personId):
    try:
        person_ref = db.collection("PersonalData").document(personId)
        doc = person_ref.get()
        if not doc.exists:
            return jsonify({
                "code": 404,
                "data": {"personId": personId},
                "message": "Person not found."
            }), 404

        new_data = request.get_json()
        if new_data['status'] < 400:
            # Merge update into Firestore document.
            db.collection("PersonalData").document(personId).set(new_data["data"], merge=True)
            return jsonify({"code": 200, "data": new_data}), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "data": {"personId": personId},
            "message": "An error occurred while updating the person information: " + str(e)
        }), 500


@app.route("/person", methods=['POST'])
def create_person():
    try:
        # Get the JSON payload from the request
        person_data = request.get_json()

        # Ensure personId is provided in the request payload.
        person_id = person_data.get("personId")
        if not person_id:
            return jsonify({
                "code": 400,
                "data": {},
                "message": "Person ID is required."
            }), 400

        # Reference to the person document in Firestore
        person_ref = db.collection("PersonalData").document(person_id)
        if person_ref.get().exists:
            return jsonify({
                "code": 409,
                "data": {"personId": person_id},
                "message": "Person already exists."
            }), 409

        # Create a new Person object from the provided data.
        new_person = Person(
            person_id=person_id,
            first_name=person_data["firstName"],
            last_name=person_data["lastName"],
            date_of_birth=person_data["dateOfBirth"],
            nok_contact=person_data["nokContact"]
        )

        # Save the new person to Firestore.
        person_ref.set(new_person.to_dict())

        return jsonify({
            "code": 201,
            "data": new_person.to_dict(),
            "message": "Person created successfully."
        }), 201

    except Exception as e:
        return jsonify({
            "code": 500,
            "data": {},
            "message": "An error occurred while creating the person: " + str(e)
        }), 500


if __name__ == '__main__':
    print("This is flask for " + os.path.basename(__file__) + ": manage Personal Data ...")
    app.run(host='0.0.0.0', port=5007, debug=True)