from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os

app = Flask(__name__)
CORS(app)

# Load the Firebase key from an environment variable
key_path = os.getenv("LABINFO_DB_KEY", "/usr/src/app/Lab_Info_Key.json")

if not key_path or not os.path.isfile(key_path):
    raise FileNotFoundError(f"Could not find the Firebase JSON at {key_path}")

# Initialize Firestore
cred = credentials.Certificate(key_path)
firebase_app = firebase_admin.initialize_app(cred)
db = firestore.client()

print("Firestore initialized successfully for Lab Reports!")


"""
LabInfo Class JSON Schema
{
  "uuid": "b0241838-3a17-4abc-a80e-530a325a3bec",
  "testType": "Compatibility",
  "dateOfReport": "2023-10-18",
  "report": {
    "name": "Compatibility Lab Test Report",
    "url": "https://beonbrand.getbynder.com/m/b351439ebceb7d39/original/Laboratory-Tests-for-Organ-Transplant-Rejection.pdf"
  },
  "result": {
    numOfHLA: 4,
    "negativeCrossMatch": true,
    },
    "comments": "To be reviewed."
  }
}
"""
class LabInfo:
    def __init__(self, uuid, test_type, date_of_report, report, hla_typing, comments):
        self.uuid = uuid
        self.test_type = test_type
        self.date_of_report = date_of_report
        self.report = report
        self.hla_typing = hla_typing
        self.comments = comments
        

    def to_dict(self):
        """Convert the object to a Firestore-compatible dictionary."""
        return {
            "uuid": self.uuid,
            "testType": self.test_type,
            "dateOfReport": self.date_of_report,
            "report": self.report,
            "hlaTyping": self.hla_typing,
            "comments": self.comments,
        }

    @staticmethod
    def from_dict(uuid, data):
        """Create a LabInfo object from Firestore document data."""
        return LabInfo(
            uuid=uuid,
            test_type=data["testType"],
            date_of_report=data["dateOfReport"],
            report=data["report"],
            hla_typing=data["hlaTyping"],
            comments=data["comments"],
            
        )
@app.route("/lab-reports", methods=['GET'])
def get_all():
    # Read data from firebase
    try:
        lab_info_ref = db.collection("lab_reports")
        docs = lab_info_ref.get()
        labInfo = {};

        for doc in docs:
            lab_info_data = doc.to_dict()
            lab_info_data["uuid"] = doc.id  # Add document ID
            labInfo[doc.id] = lab_info_data
        return jsonify({"code":200, "data": labInfo}), 200
    except Exception as e:
        return jsonify({"code":500, "message": str(e)}), 500


@app.route("/lab-reports/<string:uuid>")
def get_lab_info(uuid):
    try:
        lab_info_ref = db.collection("lab_reports").document(uuid)
        doc = lab_info_ref.get()
        if doc.exists:
            lab_info_obj = LabInfo.from_dict(uuid, doc.to_dict())
            return {"code":200, "data": lab_info_obj.to_dict()}  # Convert back to JSON-friendly format
        else:
            return jsonify({"code": 404, "message": "LabInfo does not exist"}), 404

    except Exception as e:
        return jsonify({"code":500, "message": str(e)}), 500


@app.route("/lab-reports/<string:uuid>", methods=['PUT'])
def update_lab_info(uuid):
    try:
        lab_info_ref = db.collection("lab_report").document(uuid)
        doc = lab_info_ref.get()
        if not doc.exists:
            return jsonify(
                {
                    "code": 404,
                    "data": {
                        "uuid": uuid
                    },
                    "message": "LabInfo not found."
                }
            ), 404

        # update status
        new_data = request.get_json()
        if new_data['status'] < 400:
            db.collection("donors").document(uuid).set(new_data["data"], merge=True)
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
                    "uuid": uuid
                },
                "message": "An error occurred while updating the LabInfo information. " + str(e)
            }
        ), 500
    
@app.route("/lab-reports", methods=['POST'])
def create_lab_info():
    try:
        # Get the JSON payload from the request
        lab_info_data = request.get_json()

        # Ensure donorId is provided in the request
        uuid = lab_info_data.get("uuid")
        if not uuid:
            return jsonify({
                "code": 400,
                "data": {},
                "message": "LabInfo Id is required."
            }), 400

        # Reference to the donor document in Firestore
        lab_info_ref = db.collection("lab_reports").document(uuid)
        if lab_info_ref.get().exists:
            return jsonify({
                "code": 409,
                "data": {"uuid": uuid},
                "message": "LabInfo already exists."
            }), 409

        # Create a new LabInfo object
        new_lab_info = LabInfo(
            uuid=uuid,
            test_type=lab_info_data["testType"],
            date_of_report=lab_info_data["dateOfReport"],
            report=lab_info_data["report"],
            hla_typing=lab_info_data.get("hlaTyping", {}), # Optional dict
            comments=lab_info_data["comments"],
        )

        # Save the new donor to Firestore
        lab_info_ref.set(new_lab_info.to_dict())

        # Return success response
        return jsonify({
            "code": 201,
            "data": new_lab_info.to_dict(),
            "message": "LabInfo created successfully."
        }), 201

    except Exception as e:
        print("Error: {}".format(str(e)))
        return jsonify({
            "code": 500,
            "data": {},
            "message": "An error occurred while creating the LabInfo: " + str(e)
        }), 500


@app.route("/lab-reports/<string:uuid>", methods=['DELETE'])
def delete_lab_info(uuid):
    """Delete an donor from Firestore."""
    try:
        lab_info_ref = db.collection("lab_reports").document(uuid)
        doc = lab_info_ref.get()

        if not doc.exists:
            return jsonify({"code": 404, "message": "LabInfo not found"}), 404

        # Delete the organ document from Firestore
        lab_info_ref.delete()

        return jsonify({"code": 200, "message": "LabInfo deleted successfully"}), 200

    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500

if __name__ == '__main__':
    print("This is Flask for " + os.path.basename(__file__) + ": manage lab reports ...")
    app.run(host='0.0.0.0', port=5007, debug=True)
