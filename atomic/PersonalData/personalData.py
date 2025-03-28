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
    def __init__(self, uuid, first_name, last_name, date_of_birth, nok_contact):
        self.uuid = uuid
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
    def from_dict(uuid, data):
        """Create a Person object from Firestore document data."""
        return Person(
            uuid=uuid,
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
            person_data["uuid"] = doc.id  # Include the document ID
            persons[doc.id] = person_data
        return jsonify({"code": 200, "data": persons}), 200
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500


@app.route("/person/<string:uuid>")
def get_person(uuid):
    try:
        person_ref = db.collection("PersonalData").document(uuid)
        doc = person_ref.get()
        if doc.exists:
            person_obj = Person.from_dict(uuid, doc.to_dict())
            return jsonify({"code": 200, "data": person_obj.to_dict()})
        else:
            return jsonify({"code": 404, "message": "Person does not exist"}), 404

    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500


@app.route("/person/<string:uuid>", methods=['PUT'])
def update_person(uuid):
    try:
        person_ref = db.collection("PersonalData").document(uuid)
        doc = person_ref.get()
        if not doc.exists:
            return jsonify({
                "code": 404,
                "data": {"uuid": uuid},
                "message": "Person not found."
            }), 404

        new_data = request.get_json()
        if new_data['status'] < 400:
            # Merge update into Firestore document.
            db.collection("PersonalData").document(uuid).set(new_data["data"], merge=True)
            return jsonify({"code": 200, "data": new_data}), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "data": {"uuid": uuid},
            "message": "An error occurred while updating the person information: " + str(e)
        }), 500


@app.route("/person", methods=['POST'])
def create_person():
    try:
        # Get the JSON payload from the request
        person_data = request.get_json()

        # Ensure uuid is provided in the request payload.
        uuid = person_data.get("uuid")
        if not uuid:
            return jsonify({
                "code": 400,
                "data": {},
                "message": "uuid is required."
            }), 400

        # Reference to the person document in Firestore
        person_ref = db.collection("PersonalData").document(uuid)
        if person_ref.get().exists:
            return jsonify({
                "code": 409,
                "data": {"uuid": uuid},
                "message": "Person already exists."
            }), 409

        # Create a new Person object from the provided data.
        new_person = Person(
            uuid=uuid,
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

@app.route("/person/<string:uuid>", methods=['DELETE'])
def delete_match(uuid):
    """Delete a PersonalData from Firestore."""
    try:
        personal_data_ref = db.collection("PersonalData").document(uuid)
        doc = personal_data_ref.get()

        if not doc.exists:
            return jsonify({"code": 404, "message": "PersonalData not found"}), 404

        # Delete the organ document from Firestore
        personal_data_ref.delete()

        return jsonify({"code": 200, "message": "PersonalData deleted successfully"}), 200

    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500


if __name__ == '__main__':
    print("This is flask for " + os.path.basename(__file__) + ": manage Personal Data ...")
    app.run(host='0.0.0.0', port=5011, debug=True)