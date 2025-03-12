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

@app.route("/lab-reports", methods=['GET'])
def get_all_lab_reports():
    try:
        lab_reports_ref = db.collection("lab_reports")
        docs = lab_reports_ref.get()
        lab_reports = [doc.to_dict() for doc in docs]

        return jsonify({
            "code": 200,
            "data": lab_reports,
            "message": "Lab reports fetched successfully"
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "data": {"error": str(e)},
            "message": "An error occurred while fetching lab reports"
        }), 500


@app.route("/lab-reports/<string:uuid>", methods=['GET'])
def get_lab_report(uuid):
    try:
        lab_reports_ref = db.collection("lab_reports").where("uuid", "==", uuid)
        docs = lab_reports_ref.get()

        if docs:
            report_data = docs[0].to_dict()
            return jsonify({
                "code": 200,
                "data": report_data,
                "message": "Lab report fetched successfully"
            }), 200
        else:
            return jsonify({
                "code": 404,
                "data": {"uuid": uuid},
                "message": "Lab report not found"
            }), 404

    except Exception as e:
        return jsonify({
            "code": 500,
            "data": {"error": str(e)},
            "message": "An error occurred while fetching the lab report"
        }), 500


@app.route("/lab-reports/<string:uuid>", methods=['PUT'])
def update_lab_report(uuid):
    try:
        update_data = request.get_json()

        # Prevent updating the UUID field
        if "uuid" in update_data:
            update_data.pop("uuid")

        lab_reports_ref = db.collection("lab_reports").where("uuid", "==", uuid)
        docs = lab_reports_ref.get()

        if docs:
            doc_ref = docs[0].reference
            doc_ref.update(update_data)
            return jsonify({
                "code": 200,
                "data": {"uuid": uuid},
                "message": "Lab report updated successfully"
            }), 200
        else:
            return jsonify({
                "code": 404,
                "data": {"uuid": uuid},
                "message": "Lab report not found"
            }), 404

    except Exception as e:
        return jsonify({
            "code": 500,
            "data": {"error": str(e)},
            "message": "An error occurred while updating the lab report"
        }), 500


if __name__ == '__main__':
    print("This is Flask for " + os.path.basename(__file__) + ": manage lab reports ...")
    app.run(host='0.0.0.0', port=5003, debug=True)
