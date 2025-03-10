from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

app = Flask(__name__)
CORS(app)

# Load the Firebase key from an environment variable
key_path = os.getenv("LABINFO_DB_KEY")

if not key_path or not os.path.isfile(key_path):
    raise FileNotFoundError(f"Could not find the Firebase JSON at {key_path}")

# Initialize Firestore
cred = credentials.Certificate(key_path)
firebase_app = firebase_admin.initialize_app(cred)
db = firestore.client()

print("Firestore initialized successfully for Lab Reports!")

class LabReport:
    def __init__(self, report_id, report_name, test_type, patient_name, date_of_report, results, comments, report_url):
        self.report_id = report_id
        self.report_name = report_name
        self.test_type = test_type
        self.patient_name = patient_name
        self.date_of_report = date_of_report
        self.results = results
        self.comments = comments
        self.report_url = report_url

    def to_dict(self):
        """Convert the object to a Firestore-compatible dictionary."""
        return {
            "reportId": self.report_id,
            "reportName": self.report_name,
            "testType": self.test_type,
            "patientName": self.patient_name,
            "dateOfReport": self.date_of_report,
            "results": self.results,
            "comments": self.comments,
            "report_url": self.report_url
        }

    @staticmethod
    def from_dict(report_id, data):
        """Create a LabReport object from Firestore document data."""
        return LabReport(
            report_id=report_id,
            report_name=data["reportName"],
            test_type=data["testType"],
            patient_name=data["patientName"],
            date_of_report=data["dateOfReport"],
            results=data["results"],
            comments=data["comments"],
            report_url=data["report_url"]
        )


@app.route("/lab-reports", methods=['GET'])
def get_all_lab_reports():
    try:
        lab_reports_ref = db.collection("lab_reports")
        docs = lab_reports_ref.get()
        lab_reports = {}

        for doc in docs:
            report_data = doc.to_dict()
            report_data["reportID"] = doc.id  # Add document ID
            lab_reports[doc.id] = report_data

        return jsonify({"success": True, "code": 200, "data": lab_reports}), 200
    except Exception as e:
        return jsonify({"success": False, "code": 500, "error": str(e)}), 500


@app.route("/lab-reports/<string:reportId>", methods=['GET'])
def get_lab_report(reportId):
    try:
        lab_reports_ref = db.collection("lab_reports").document(reportId)
        doc = lab_reports_ref.get()
        if doc.exists:
            lab_report_obj = LabReport.from_dict(reportId, doc.to_dict())
            return {"success": True, "code": 200, "data": lab_report_obj.to_dict()}  # Convert back to JSON-friendly format
        else:
            return jsonify({"success": False, "code": 404, "error": "Lab report does not exist"}), 404

    except Exception as e:
        return jsonify({"success": False, "code": 500, "error": str(e)}), 500


@app.route("/lab-reports", methods=['POST'])
def create_lab_report():
    try:
        new_report_data = request.get_json()
        
        # Assuming the data includes the required fields
        lab_report = LabReport(
            report_id=None,  # Firestore will assign this
            report_name=new_report_data['reportName'],
            test_type=new_report_data['testType'],
            patient_name=new_report_data['patientName'],
            date_of_report=datetime.now(),  # Set current date for the report
            results=new_report_data['results'],
            comments=new_report_data['comments'],
            report_url=new_report_data['report_url']
        )
        
        # Add to Firestore
        doc_ref = db.collection("lab_reports").add(lab_report.to_dict())
        
        # Return the newly created report with Firestore ID
        return jsonify({"success": True, "code": 201, "data": lab_report.to_dict()}), 201
    except Exception as e:
        return jsonify({"success": False, "code": 500, "error": str(e)}), 500

@app.route("/lab-reports/<string:reportId>", methods=['PUT'])
def update_lab_report(reportId):
    try:
        # Retrieve the data from the request
        lab_report_data = request.get_json()

        # Check if the document with this reportId exists
        lab_reports_ref = db.collection("lab_reports").document(reportId)
        doc = lab_reports_ref.get()
        
        if doc.exists:
            # Update the document with the new data
            lab_reports_ref.update(lab_report_data)

            # Return success response
            return jsonify({"success": True, "code": 200, "message": "Lab report updated successfully"})

        else:
            # If the document does not exist, return a 404 error
            return jsonify({"success": False, "code": 404, "error": "Lab report not found"}), 404

    except Exception as e:
        # Handle any exceptions
        return jsonify({"success": False, "code": 500, "error": str(e)}), 500

@app.route("/lab-reports/<string:reportId>", methods=['DELETE'])
def delete_lab_report(reportId):
    try:
        # Reference to the specific lab report document in Firestore
        lab_reports_ref = db.collection("lab_reports").document(reportId)
        
        # Check if the document exists
        doc = lab_reports_ref.get()
        
        if doc.exists:
            # Delete the document
            lab_reports_ref.delete()
            
            # Return success response
            return jsonify({"success": True, "code": 200, "message": "Lab report deleted successfully"})

        else:
            # If the document does not exist, return a 404 error
            return jsonify({"success": False, "code": 404, "error": "Lab report not found"}), 404

    except Exception as e:
        # Handle any exceptions
        return jsonify({"success": False, "code": 500, "error": str(e)}), 500

if __name__ == '__main__':
    print("This is flask for " + os.path.basename(__file__) + ": manage lab reports ...")
    app.run(host='0.0.0.0', port=5003, debug=True)