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

@app.route('/createDelivery', methods=['POST'])
def createDelivery():

    """
    API endpoint to decode a polyline
    
    Expects JSON data with format: 
    {
        OrganType: 
        Status: (Scheduled, On Delivery, Delivered)
        transplantDateTime:
        startHospital:
        endHospital:
        matchId:
        Remarks:
    }

    Returns:
    {
        "code" : int,
        "message" : String
    }
    """

    #Retrieve the information from the post
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No json data received"}), 400
        
        #Retrieve driverID, DoctorID, originCoord, DestinationCoord, EndTime
        originCoord = data.get("startHospital")
        destinationCoord = data.get("endHospital")

        #Retreive Polyline
        LocationJson = {
                    "routingPreference": "",
                    "travelMode": "",
                    "computeAlternativeRoutes": False,
                    "destination": {
                        "location": {
                        "latLng": {
                            "latitude": 0.1,
                            "longitude": 0.1
                        }
                        }
                    },
                    "origin": {
                        "location": {
                        "latLng": {
                            "latitude": 0.1,
                            "longitude": 0.1
                        }
                        }
                    }
                    }

        LocationResponse = requests.post(LocationEndpoint + "/route", headers=headers, data=json.dumps(LocationJson))

        if LocationResponse.status_code == 200:
            LocationResponse_data = LocationResponse.json()  # Parse the JSON response
            try:
                encoded_polyline = LocationResponse_data["Route"][0]["Polyline"]["encodedPolyline"]
                print(f"Encoded Polyline: {encoded_polyline}")
            except KeyError as e:
                print(f"KeyError: Missing expected key {e}")
        else:
            print(f"Error: {LocationResponse.status_code}")  # Handle errors

        #Create a new delivery json with driverID, DoctorID, originCoord, DestinationCoord, EndTime, polyline, status

        DeliveryJson = {
                    "polyline" : encoded_polyline,
                    "pickup" : ,
                    "pickup_time" : ,
                    "destination" : ,
                    "destination_time" : ,
                    "status" : ,
                    "polyline": ,
                    "driverCoord": ,
                    "driverId" : ,
                    "doctorId" : ,
        }

        #Connect to delivery API
        DeliveryResponse = requests.post(DeliveryEndpoint + "/route", headers=headers, data=json.dumps(DeliveryJson))

        if DeliveryResponse.status_code == 200:
            DeliveryResponse_data = DeliveryResponse.json()  # Parse the JSON response
            try:
                #Done
                print(f"Delivery Response: {DeliveryResponse_data}")
            except KeyError as e:
                print(f"KeyError: Missing expected key {e}")
        else:
            print(f"Error: {DeliveryResponse.status_code}")  # Handle errors

        return jsonify({"message": "JSON received successfully", "data": data}), 200
    except Exception as e:
        return jsonify({"code": 500,
                        "message": f"{e}"}), 500


@app.route('/updateDelivery', methods=['POST'])
def updateDelivery():
    """
    API endpoint to decode a polyline
    
    Expects JSON data with format: 
    {
        "deliveryID" : String,
        "driverCoord": String

    }
    
    Returns:
    {
        "Code" : String
        "data“ ：{
            "Polyline" : String
            }
    }
    """
    
    #Draw the delivery with deliveryId
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No json data received"}), 400
        
        deliveryId = data.get("deliveryId")
        driverCoord = data.get("driverCoord")

    #Check for deviation given driverCoord

        DeviationJson = {}

        DeviationResponse = requests.post(GeoAlgoEndpoint + "", headers=headers, data=json.dumps(DeviationJson))

        if DeviationResponse.status_code == 200:
            DeviationResponse_data = DeviationResponse.json()  # Parse the JSON response
            try:
                DeviationSuccess = DeviationResponse_data.get("Success")
                print(f"Delivery Response: {DeviationResponse_data}")
            except KeyError as e:
                print(f"KeyError: Missing expected key {e}")

        if (DeviationSuccess):


    #If deviate, return new polyline

    

    #update the deliveryId with new polyline and driverCoord

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)