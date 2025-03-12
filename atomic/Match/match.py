from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os

app = Flask(__name__)
CORS(app)

# Load the Firebase key from an environment variable
key_path = os.getenv("MATCH_DB_KEY")

if not key_path or not os.path.isfile(key_path):
    raise FileNotFoundError(f"Could not find the Firebase JSON at {key_path}")

# Initialize Firestore
cred = credentials.Certificate(key_path)
firebase_app = firebase_admin.initialize_app(cred)
db = firestore.client()

print("Firestore initialized successfully for Matches!")

@app.route("/matches", methods=['GET'])
def get_all_matches():
    try:
        matches_ref = db.collection("matches")
        docs = matches_ref.get()
        matches = [doc.to_dict() for doc in docs]

        return jsonify({
            "code": 200,
            "data": matches,
            "message": "Matches fetched successfully"
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "data": {"error": str(e)},
            "message": "An error occurred while fetching matches"
        }), 500


@app.route("/matches/<string:match_id>", methods=['GET'])
def get_match_by_id(match_id):
    try:
        match_ref = db.collection("matches").document(match_id)
        doc = match_ref.get()

        if doc.exists:
            match_data = doc.to_dict()
            return jsonify({
                "code": 200,
                "data": match_data,
                "message": "Match fetched successfully"
            }), 200
        else:
            return jsonify({
                "code": 404,
                "data": {"match_id": match_id},
                "message": "Match not found"
            }), 404

    except Exception as e:
        return jsonify({
            "code": 500,
            "data": {"error": str(e)},
            "message": "An error occurred while fetching the match"
        }), 500

#no puts cos matches shouldnt be edited?
# @app.route("/matches/<string:match_id>", methods=['PUT'])
# def update_match(match_id):
#     try:
#         update_data = request.get_json()

#         # Prevent updating the matchId field
#         if "matchId" in update_data:
#             update_data.pop("matchId")

#         match_ref = db.collection("matches").document(match_id)
#         doc = match_ref.get()

#         if doc.exists:
#             match_ref.update(update_data)
#             return jsonify({
#                 "code": 200,
#                 "data": {"match_id": match_id},
#                 "message": "Match updated successfully"
#             }), 200
#         else:
#             return jsonify({
#                 "code": 404,
#                 "data": {"match_id": match_id},
#                 "message": "Match not found"
#             }), 404

#     except Exception as e:
#         return jsonify({
#             "code": 500,
#             "data": {"error": str(e)},
#             "message": "An error occurred while updating the match"
#         }), 500


if __name__ == '__main__':
    print("This is Flask for " + os.path.basename(__file__) + ": manage matches ...")
    app.run(host='0.0.0.0', port=5005, debug=True)