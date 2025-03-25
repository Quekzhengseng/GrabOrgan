import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, jsonify, request
import os

key_path = os.getenv("DRIVERINFO_DB_KEY", "./secrets/driverInfo_Key.json")  # Default for local testing
cred = credentials.Certificate(key_path)

# cred = credentials.Certificate("/usr/src/app/driverInfo_Key.json")
firebase_admin.initialize_app(cred)

db = firestore.client()
app = Flask(__name__)

#landing page
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "This is Driver Info Service API!",
        "endpoints": {
            "Add Driver": "POST /drivers",
            "Get All Drivers": "GET /drivers",
            "Get Driver by ID": "GET /drivers/<driver_id>",
            "Update Driver": "PATCH /drivers/<driver_id>",
            "Add Trip to History": "PATCH /drivers/<driver_id>/trip",
            "Delete Driver": "DELETE /drivers/<driver_id>"
        }
    }), 200


#post (create) one driver
@app.route("/drivers", methods=["POST"])
def add_driver():
    try:
        driver_info = request.json
        if not driver_info:
            return jsonify({"error": "Request body cannot be empty"}), 400
        
        doc_ref = db.collection("drivers").add(driver_info) #auto generate ID
        return jsonify({"message": "Driver added successfully"}), 201
    
    except Exception as error:
        return jsonify({"error": str(error)}), 500


#get ALL drivers 
@app.route("/drivers", methods=["GET"])
def get_all_drivers():
    try:
        drivers_ref = db.collection("drivers")
        docs = drivers_ref.stream()
        
        all_drivers = []
        for doc in docs:
            driver_data = doc.to_dict()
            driver_data["driver_id"] = doc.id  #need to add back the firestore ID
            all_drivers.append(driver_data)

        if not all_drivers:
            return  jsonify({"message": "No drivers found"}), 404
        return jsonify(all_drivers), 200 
    
    except Exception as error:
        return jsonify({"error": str(error)}), 500
    

#get ONE driver
@app.route("/drivers/<driver_id>", methods=["GET"])
def get_one_driver(driver_id):
    try:
        doc_ref = db.collection("drivers").document(driver_id)
        doc = doc_ref.get()
        if doc.exists:
            return jsonify(doc.to_dict()), 200
        else:
            return jsonify({"error": "Driver not found"}), 404
        
    except Exception as error:
        return jsonify({"error": str(error)}), 500
        

#updates NON ARRAY fields
@app.route("/drivers/<driver_id>", methods=["PATCH"])
def update_driver(driver_id):
    try:

        #check if document exist
        #if exist then use arrayunion
        #if not js create
        #bring bottom func up


        #check if driver_id exists
        doc_ref = db.collection("drivers").document(driver_id)
        doc = doc_ref.get()
        if not doc.exists:
            return jsonify({"error": "Driver not found"}), 404
        
        data = request.json
        doc_ref.update(data) #can only update non array fields



        return jsonify({"message": "Driver updated successfully"}), 200
    
    except Exception as error:
        return jsonify({"error": str(error)}), 500
    

#updates ARRAY fields (trip history)
@app.route("/drivers/<driver_id>/trip", methods=["PATCH"])
def add_trip(driver_id):
    try:
        data = request.json  # Expecting a dictionary like {"trip": "trip data"}
        trip_info = data.get("trip")
        
        if not trip_info:
            return jsonify({"error": "Trip data is required"}), 400

        doc_ref = db.collection("drivers").document(driver_id)
        doc_ref.update({"trip_history": firestore.ArrayUnion([trip_info])})

        return jsonify({"message": "Trip added to history"}), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500

#delete driver
@app.route("/drivers/<driver_id>", methods=["DELETE"])
def delete_driver(driver_id):
    try:
        doc_ref = db.collection("drivers").document(driver_id)
        doc_ref.delete()
        return jsonify({"message": "Driver deleted successfully"}), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500
    


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004)