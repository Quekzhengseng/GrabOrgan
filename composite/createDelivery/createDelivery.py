# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

DeliveryEndpoint = "http://delivery_service:5002"
GeoAlgoEndpoint = "http://geoalgo_service:5006"
DriverEndpoint = "http://driverInfo_service:5004"
MatchDriverEndpoint = "http://selectDriver:5024"
LocationEndpoint = "https://zsq.outsystemscloud.com/Location/rest/Location/"
headers = {'Content-Type': 'application/json'}

@app.route('/createDelivery', methods=['POST'])
def createDelivery():

    """
    API endpoint to decode a polyline
    
    Expects JSON data with format: 
    {
        Status: (Scheduled, On Delivery, Delivered) => Not used
        transplantDateTime: DateTime, => Required
        startHospital: String, => Required
        endHospital: String, => Required
        doctorId: String, => Required
        matchId: String, => Not used
        Remarks: String => Not used
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

    #Retrieve the information from the post
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No json data received"}), 400
        
        #Retrieve DoctorID, originCoord, DestinationCoord, EndTime
        Origin_address = data.get("startHospital")
        Destination_address = data.get("endHospital")
        DoctorId = data.get("DoctorId")
        destinationTime = data.get("transplantDateTime")

        Origin_PlaceToCoordJson = {
                                    "long_name": Origin_address
                            }
        
        Destination_PlaceToCoordJson = {
                            "long_name": Destination_address
                    }

        Origin_PlaceToCoordResponse = requests.post(LocationEndpoint + "/PlaceToCoord", headers=headers, data=json.dumps(Origin_PlaceToCoordJson))
        Destination_PlaceToCoordResponse = requests.post(LocationEndpoint + "/PlaceToCoord", headers=headers, data=json.dumps(Destination_PlaceToCoordJson))

        if Origin_PlaceToCoordResponse.status_code == 200 and Destination_PlaceToCoordResponse.status_code == 200:
            Origin_PlaceToCoordResponse_data = Origin_PlaceToCoordResponse.json()  # Parse the JSON response
            Destination_PlaceToCoordResponse_data = Destination_PlaceToCoordResponse.json()  # Parse the JSON response
            try:
                OriginCoord = {
                    "lat" : Origin_PlaceToCoordResponse_data["latitude"],
                    "lng" : Origin_PlaceToCoordResponse_data["longitude"]
                }
                DestinationCoord = {
                    "lat" : Destination_PlaceToCoordResponse_data["latitude"],
                    "lng" : Destination_PlaceToCoordResponse_data["longitude"]
                }
                print(f"Coordinates Received")
            except Exception as e:
                print(f"Error in fetching coordinates: {e}")
        else:
            print(f"Error: {Origin_PlaceToCoordResponse.status_code}")  # Handle errors

        #Retreive Polyline
        LocationJson = {
                    "routingPreference": "TRAFFIC_AWARE",
                    "travelMode": "DRIVE",
                    "computeAlternativeRoutes": False,
                    "destination": {
                        "location": {
                        "latLng": {
                            "latitude": DestinationCoord["lat"],
                            "longitude": DestinationCoord["lng"]
                        }
                        }
                    },
                    "origin": {
                        "location": {
                        "latLng": {
                            "latitude": OriginCoord["lat"],
                            "longitude": OriginCoord["lng"]
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

        #Get a suitable Driver via matchDriver Composite
        MatchDriverRequestJson = {
            "transplantDateTime" : destinationTime,
            "startHospital": Origin_address,
            "endHospital": Destination_address
        }

        MatchDriverResponse = requests.post(MatchDriverEndpoint + "/selectDriver", headers=headers, data=json.dumps(MatchDriverRequestJson))

        if MatchDriverResponse.status_code == 200:
            MatchDriverResponse_data = MatchDriverResponse.json()  # Parse the JSON response
            try:
                driverId = MatchDriverResponse_data["data"]["DriverId"]
                print(f"Driver Found")
            except Exception as e:
                print(f"Cannot fetch a driver: {e}")
        else:
            print(f"Error: {MatchDriverResponse.status_code}")  # Handle errors

        #Get the driver details
        DriverResponse = requests.get(DriverEndpoint + "/drivers/" + driverId)

        if DriverResponse.status_code == 200:
            DriverResponse_data = DriverResponse.json()  # Parse the JSON response
            try:
                driverAddress = DriverResponse_data["stationed_hospital"]
                print(f"Driver Found")
            except Exception as e:
                print(f"Cannot fetch a driver: {e}")
        else:
            print(f"Error: {DriverResponse.status_code}")  # Handle errors

        #Convert driver address to coordinates
        Driver_PlaceToCoordJson = {
                            "long_name": driverAddress
                    }

        Driver_PlaceToCoordResponse = requests.post(LocationEndpoint + "/PlaceToCoord", headers=headers, data=json.dumps(Driver_PlaceToCoordJson))

        if Driver_PlaceToCoordResponse.status_code == 200:
            Driver_PlaceToCoordResponse_data = Driver_PlaceToCoordResponse.json()  # Parse the JSON response
            try:
                DriverCoord = {
                    "lat" : Driver_PlaceToCoordResponse_data["latitude"],
                    "lng" : Driver_PlaceToCoordResponse_data["longitude"]
                }
                print(f"Driver Coordinates Received")
            except Exception as e:
                print(f"Error in fetching Driver coordinates: {e}")
        else:
            print(f"Error: {Driver_PlaceToCoordResponse.status_code}")  # Handle errors

        #NUMBER 1
        #Create a new delivery json with driverID, DoctorID, originCoord, DestinationCoord, EndTime, polyline, status
        DeliveryJson = {
            "pickup": Origin_address,
            "pickup_time": "20250315 10:30:00 AM",
            "destination": Destination_address,
            "destination_time": "20250315 11:30:00 AM",  # One hour later
            "status": "Assigned",
            "polyline": encoded_polyline,
            "driverCoord": DriverCoord,
            "driverID": driverId,
            "doctorID": DoctorId,
        }

        #Connect to delivery API and create delivery
        DeliveryResponse = requests.post(DeliveryEndpoint + "/deliveryinfo", headers=headers, data=json.dumps(DeliveryJson))

        if DeliveryResponse.status_code == 201:
            DeliveryResponse_data = DeliveryResponse.json()  # Parse the JSON response
            try:
                DeliveryId = DeliveryResponse_data["data"]["orderID"]
                print(f"Delivery Response: {DeliveryResponse_data}")
            except KeyError as e:
                print(f"KeyError: Missing expected key {e}")
        else:
            print(f"Error: {DeliveryResponse}")  # Handle errors

        return jsonify({"message": "Delivery successfully created", "data": {
            "DeliveryId" : DeliveryId
        }}), 200
    except Exception as e:
        return jsonify({"code": 500,
                        "message": f"{e}"}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5026)