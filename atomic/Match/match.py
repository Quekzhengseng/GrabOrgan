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

class Match:
    def __init__(self, match_id, recipient_id, donor_id, organ_id ,test_date_time, 
                 hla_1, hla_2, hla_3, hla_4, hla_5, hla_6, numofHLA):
        self.match_id = match_id
        self.recipient_id = recipient_id
        self.donor_id = donor_id
        self.organ_id = organ_id
        self.test_date_time = test_date_time
        self.hla_1 = hla_1
        self.hla_2 = hla_2
        self.hla_3 = hla_3
        self.hla_4 = hla_4
        self.hla_5 = hla_5
        self.hla_6 = hla_6
        self.num_of_hla = numofHLA

    def to_dict(self):
        """Convert the object to a Firestore-compatible dictionary."""
        return {
        "matchId": self.match_id, 
        "recipientId": self.recipient_id,
        "donorId": self.donor_id,
        "organId": self.organ_id,
        "testDateTime": self.test_date_time,
        "hla1": self.hla_1,
        "hla2": self.hla_2,
        "hla3": self.hla_3,
        "hla4": self.hla_4,
        "hla5": self.hla_5,
        "hla6": self.hla_6,
        "numOfHLA": self.num_of_hla,
        }

    @staticmethod
    def from_dict(match_id, data):
        """Create a Match object from Firestore document data."""
        return Match(
        match_id=match_id, 
        recipient_id=data["recipientId"],
        donor_id=data["donorId"],
        organ_id=data["organId"],
        test_date_time=data["testDateTime"],
        hla_1=data["hla1"],
        hla_2=data["hla2"],
        hla_3=data["hla3"],
        hla_4=data["hla4"],
        hla_5=data["hla5"],
        hla_6=data["hla6"],
        num_ofHLA=data["numOfHLA"] 
        )

@app.route("/matches", methods=['GET'])
def get_all():
    # Read data from firebase
    try:
        match_ref = db.collection("matches")
        # docs = matches_ref.stream()
        docs = match_ref.get()
        matches = {};

        for doc in docs:
            match_data = doc.to_dict()
            match_data["donorID"] = doc.id  # Add document ID
            matches[doc.id] = match_data
        return jsonify({"code":200, "data": matches}), 200
    except Exception as e:
        return jsonify({"code":500, "message": str(e)}), 500


@app.route("/matches/<string:matchId>")
def get_donor(matchId):
    try:
        match_ref = db.collection("matches").document(matchId)
        doc = match_ref.get()
        if doc.exists:
            match_obj = Match.from_dict(matchId, doc.to_dict())
            return {"code":200, "data": match_obj.to_dict()}  # Convert back to JSON-friendly format
        else:
            return jsonify({"code":404, "message": "Match does not exist"}), 404

    except Exception as e:
        return jsonify({"code":500, "message": str(e)}), 500


@app.route("/match/<string:matchId>", methods=['PUT'])
def update_donor(matchId):
    try:
        match_ref = db.collection("matches").document(matchId)
        doc = match_ref.get()
        if not doc.exists:
            return jsonify(
                {
                    "code": 404,
                    "data": {
                        "matchId": matchId
                    },
                    "message": "Match not found."
                }
            ), 404

        # update status
        new_data = request.get_json()
        if new_data['status'] < 400:
            db.collection("matches").document(matchId).set(new_data["data"], merge=True)
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
                    "matchId": matchId
                },
                "message": "An error occurred while updating the match information. " + str(e)
            }
        ), 500
    
@app.route("/matches", methods=['POST'])
def create_donor():
    try:
        # Get the JSON payload from the request
        match_data = request.get_json()

        # Ensure matchrId is provided in the request
        match_id = match_data.get("matchId")
        if not match_id:
            return jsonify({
                "code": 400,
                "data": {},
                "message": "Match Id is required."
            }), 400

        # Reference to the donor document in Firestore
        match_ref = db.collection("donors").document(match_id)
        if match_ref.get().exists:
            return jsonify({
                "code": 409,
                "data": {"matchId": match_id},
                "message": "Match already exists."
            }), 409

        # Create a new Donor object
        new_match = Match(
        match_id=match_id, 
        recipient_id=match_data["recipientId"],
        donor_id=match_data["donorId"],
        organ_id=match_data["organId"],
        test_date_time=match_data["testDateTime"],
        hla_1=match_data["hla1"],
        hla_2=match_data["hla2"],
        hla_3=match_data["hla3"],
        hla_4=match_data["hla4"],
        hla_5=match_data["hla5"],
        hla_6=match_data["hla6"],
        num_ofHLA=match_data["numOfHLA"] 
        )

        # Save the new donor to Firestore
        match_ref.set(new_match.to_dict())

        # Return success response
        return jsonify({
            "code": 201,
            "data": new_match.to_dict(),
            "message": "Match created successfully."
        }), 201

    except Exception as e:
        print("Error: {}".format(str(e)))
        return jsonify({
            "code": 500,
            "data": {},
            "message": "An error occurred while creating the Match: " + str(e)
        }), 500



if __name__ == '__main__':
    print("This is Flask for " + os.path.basename(__file__) + ": manage matches ...")
    app.run(host='0.0.0.0', port=5008, debug=True)