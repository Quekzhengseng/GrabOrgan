# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

DeliveryEndpoint = "http://127.0.0.1:5002"
DriverInfoEndpoint = "http://127.0.0.1:5020"
GeoAlgoEndpoint = "http://127.0.0.1:5000"
LocationEndpoint = "https://zsq.outsystemscloud.com/Location/rest/Location/"
headers = {'Content-Type': 'application/json'}

@app.route('/selectDriver', methods=["POST"])
def selectDriver():
    """
    API endpoint to decode a polyline

    Expects JSON data with format: 
    {
        transplantDateTime: DateTime,
        startHospital: String,
        endHospital: String
    }

    Returns:
    {
        "code" : int,
        "message" : String
        "data" : {
            "deliveryId" : String
        }
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No json data received"}), 400
        
        transplantDateTime = data.get("transplantDateTime")
        OriginAddress = data.get("startHospital")
        DestinationAddress = data.get("endHospital")

        DriverResponse = requests.get(DriverInfoEndpoint + "/driver")

        if DriverResponse.status_code == 200:
            DriverResponse_data = DriverResponse.json()  # Parse the JSON response
            try:
                print(f"All drivers info received")
            except Exception as e:
                print(f"Unable to fetch all drivers: {e}")
        else:
            print(f"Error: {DriverResponse.status_code}")  # Handle errors

        
        # Filter drivers who are free (status == True) and at OriginLocation
        available_drivers = [
            driver for driver in DriverResponse_data
            if driver.get("status") is True and driver.get("driverLocation") == OriginAddress
        ]

        #Find drivers that are free
        if available_drivers:
            selected_driver = available_drivers[0]  # Return the first matching driver
            DriverId = selected_driver["DriverId"]
            print("Selected Driver:", selected_driver)
        else:
            print("No available drivers found for the given conditions.")
            return jsonify({"code" : 200, "message": "No Driver Found", "data": {
            "DriverId" : 0
        }}), 200

        UpdateJson = {
            "driverId": DriverId,
            "Status": False
        }

        DriverResponse = requests.patch(DriverInfoEndpoint + "/drivers/" + DriverId ,
                                        json = UpdateJson)
        
        if DriverResponse.status_code == 200:
            DriverResponse_data = DriverResponse.json()  # Parse the JSON response
            try:
                print(f"Driver Status updated")
            except Exception as e:
                print(f"Unable to update driver status: {e}")
        else:
            print(f"Error: {DriverResponse.status_code}")  # Handle errors

        return jsonify({"code" : 200, "message": "Driver successfully found", "data": {
            "DriverId" : DriverId
        }}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)