# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

DeliveryEndpoint = "http://delivery_service:5002"
GeoAlgoEndpoint = "http://geoalgo_service:5006"
DriverInfoEndpoint = "http://driverInfo_service:5004"
LocationEndpoint = "https://zsq.outsystemscloud.com/Location/rest/Location/"
headers = {'Content-Type': 'application/json'}

@app.route('/selectDriver', methods=["POST"])
def selectDriver():
    """
        Expects JSON data with format: 
        {
            "transplantDateTime" : String,
            "startHospital": String,
            "endHospital" : String
        }
        
        Returns:
        {
            "Code" : String
            "data" : {
                "driverId" : String
                },
            "message" : String
        }
    """
    try:
        data = request.get_json()
        print(f"Request received: {data}")  # Debug log

        if not data:
            return jsonify({"error": "No json data received"}), 400
        
        transplantDateTime = data.get("transplantDateTime")
        OriginAddress = data.get("startHospital")
        DestinationAddress = data.get("endHospital")

        print(f"Attempting to get drivers from: {DriverInfoEndpoint}/drivers")  # Debug log
        DriverResponse = requests.get(DriverInfoEndpoint + "/drivers")
        print(f"Driver response status: {DriverResponse.status_code}")  # Debug log

        # Initialize the variable outside the conditional
        available_drivers = []

        if DriverResponse.status_code == 200:
            DriverResponse_data = DriverResponse.json()
            print(f"Drivers data received: {len(DriverResponse_data)} drivers")  # Debug log

            # Now set the available_drivers
            available_drivers = [
                driver for driver in DriverResponse_data
                if driver.get("isBooked") is False and driver.get("stationed_hospital") == OriginAddress
            ]
            print(f"Available drivers: {len(available_drivers)}")  # Debug log
        else:
            print(f"Error fetching drivers: {DriverResponse.status_code}")
            return jsonify({"error": f"Failed to fetch drivers: {DriverResponse.status_code}"}), 500

        # Now check if we have available drivers
        # Now check if we have available drivers
        if available_drivers:
            selected_driver = available_drivers[0]
            DriverId = selected_driver.get("driver_id")
            if not DriverId:
                return jsonify({"error": "Driver found but has no ID"}), 500
                    
            print(f"Selected driver: {DriverId}")  # Debug log

            # UpdateJson = {"isBooked": True}

            # # Update the driver status
            # UpdateResponse = requests.patch(
            #     f"{DriverInfoEndpoint}/drivers/{DriverId}",
            #     json=UpdateJson
            # )
            
            # if UpdateResponse.status_code == 200:
            return jsonify({
                "code": 200,
                "message": "Driver successfully found",
                "data": {"DriverId": DriverId}
            }), 200
            # else:
            #     return jsonify({
            #         "error": f"Failed to update driver: {UpdateResponse.status_code}"
            #     }), 500
        else:
            return jsonify({
                "code": 200,
                "message": "No Driver Found",
                "data": {"DriverId": 0}
            }), 200
    except Exception as e:
        import traceback
        print(f"Exception in selectDriver: {e}")
        print(traceback.format_exc())  # Print stack trace
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5024)