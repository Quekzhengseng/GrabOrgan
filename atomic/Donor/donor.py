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


class Donor:
    def __init__(self, donor_id, first_name, last_name, date_of_birth, datetime_of_death,
                 gender, blood_type, organs, medical_history, allergies, nok_contact):
        self.donor_id = donor_id
        self.name = {"firstName": first_name, "lastName": last_name}
        self.date_of_birth = date_of_birth
        self.datetime_of_death = datetime_of_death
        self.gender = gender
        self.blood_type = blood_type
        self.organs = organs  # List of organ dictionaries
        self.medical_history = medical_history  # List of medical history records
        self.allergies = allergies  # List of allergies
        self.nok_contact = nok_contact  # Next of kin contact details

    def to_dict(self):
        """Convert the object to a Firestore-compatible dictionary."""
        return {
            "name": self.name,
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
            first_name=data["name"]["firstName"],
            last_name=data["name"]["lastName"],
            date_of_birth=data["dateOfBirth"],
            datetime_of_death=data["datetimeOfDeath"],
            gender=data["gender"],
            blood_type=data["bloodType"],
            organs=data["organs"],
            medical_history=data["medicalHistory"],
            allergies=data["allergies"],
            nok_contact=data["nokContact"]
        )

# new_donor = Donor(
#     donor_id="1",
#     first_name="John",
#     last_name="Doe",
#     date_of_birth="1980-01-01",
#     datetime_of_death="2069-01-01T24:12:34+00:00",
#     gender="Male",
#     blood_type="O+",
#     organs=[
#         {"organType": "heart", "status": "Donated", "condition": "Healthy"},
#         {"organType": "kidney", "status": "Available", "condition": "Good"}
#     ],
#     medical_history=[
#         {"condition": "Diabetes", "description": "Managed", "dateDiagnosed": "2010-01-01", "treatment": "Insulin"},
#     ],
#     allergies=["peanuts", "aspirin"],
#     nok_contact={"firstName": "Jane", "lastName": "Doe", "relationship": "Spouse", "phone": "12345678"}
# )
# new_donor = Donor(
#     donor_id="2",
#     first_name="Alice",
#     last_name="Tan",
#     date_of_birth="1975-06-15",
#     datetime_of_death="2070-03-22T18:45:00+00:00",
#     gender="Female",
#     blood_type="A-",
#     organs=[
#         {"organType": "liver", "status": "Donated", "condition": "Excellent"},
#         {"organType": "lungs", "status": "Available", "condition": "Good"},
#         {"organType": "pancreas", "status": "Available", "condition": "Normal"}
#     ],
#     medical_history=[
#         {"condition": "Hypertension", "description": "Controlled with medication", "dateDiagnosed": "2015-08-10", "treatment": "Beta-blockers"},
#         {"condition": "Asthma", "description": "Mild, triggered by dust", "dateDiagnosed": "1995-04-20", "treatment": "Inhalers"}
#     ],
#     allergies=["shellfish", "penicillin"],
#     nok_contact={"firstName": "Michael", "lastName": "Tan", "relationship": "Son", "phone": "98765432"}
# )

# db.collection("donors").document(new_donor.donor_id).set(new_donor.to_dict())

# print("Donor added successfully!")



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
        return jsonify({"success" : True, "code":200, "data": donors}), 200
    except Exception as e:
        return jsonify({"success" : False, "code":500, "error": str(e)}), 500


@app.route("/donor/<string:donorId>")
def get_donor(donorId):
    try:
        donors_ref = db.collection("donors").document(donorId)
        doc = donors_ref.get()
        if doc.exists:
            donor_obj = Donor.from_dict(donorId, doc.to_dict())
            return {"success" : True, "code":200, "data": donor_obj.to_dict()}  # Convert back to JSON-friendly format
        else:
            return jsonify({"success" : False, "code":404, "error": "Donor does not exist"}), 404

    except Exception as e:
        return jsonify({"success" : False, "code":500, "error": str(e)}), 500


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
        # print(new_data)
        print(new_data["data"])
        if new_data['status'] < 400:
            db.collection("donors").document(donorId).set(new_data["data"], merge=True)
            return jsonify(
                {
                    "code": 200,
                    "data": new_data.json()
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
            

# def create_donor(donorId):

if __name__ == '__main__':
    print("This is flask for " + os.path.basename(__file__) + ": manage donors ...")
    app.run(host='0.0.0.0', port=5001, debug=True)