# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

DeliveryEndpoint = "http://delivery_service:5002"
DriverInfoEndpoint = "http://driverInfo_service:5004"
GeoAlgoEndpoint = "http://geoalgo_service:5006"
LocationEndpoint = "https://zsq.outsystemscloud.com/Location/rest/Location/"
DriverEndpoint = ""
headers = {'Content-Type': 'application/json'}

@app.route('/trackDelivery', methods=['POST'])
def updateDelivery():
    """
    API endpoint to decode a polyline
    
    Expects JSON data with format: 
    {
        "deliveryId" : String,
        "driverCoord": String
    }
    
    Returns:
    {
        "Code" : String
        "data" : {
            "Polyline" : String
            },
        "message" : String
    }
    """
    
    #Draw the delivery with deliveryId
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No json data received"}), 400
        
        deliveryId = data.get("deliveryId")
        driverCoord = data.get("driverCoord")

        #NUMBER 1
        #Get the polyline via delivery api call
        DriverResponse = requests.get(DeliveryEndpoint + "/deliveryinfo/" + deliveryId)

        if DriverResponse.status_code == 200:
            DriverResponse_data = DriverResponse.json()  # Parse the JSON response
            try:
                polyline = DriverResponse_data["data"]["polyline"]
                print(f"Delivery Response: {DriverResponse_data}")
            except Exception as e:
                print(f"Unable to fetch delivery: {e}")

        #Check for deviation given driverCoord
        DeviationJson = {
                "polyline": polyline,
                "driverCoord": {"lat": driverCoord["lat"], "lng": driverCoord["lng"]}
                }

        DeviationResponse = requests.post(GeoAlgoEndpoint + "/deviate", headers=headers, data=json.dumps(DeviationJson))

        if DeviationResponse.status_code == 200:
            DeviationResponse_data = DeviationResponse.json()  # Parse the JSON response
            try:
                DeviationSuccess = DeviationResponse_data["data"]["deviate"]
                print(f"Delivery Response: {DeviationResponse_data}")
            except KeyError as e:
                print(f"KeyError: Missing expected key {e}")

        if (DeviationSuccess):
            #Retrieve coordinates of destination via address
            Destination_address = DriverResponse_data["data"]["destination"]

            Destination_PlaceToCoordJson = {
                    "long_name": Destination_address
            }

            Destination_PlaceToCoordResponse = requests.post(LocationEndpoint + "/PlaceToCoord", headers=headers, data=json.dumps(Destination_PlaceToCoordJson))

            if  Destination_PlaceToCoordResponse.status_code == 200:
                Destination_PlaceToCoordResponse_data = Destination_PlaceToCoordResponse.json()  # Parse the JSON response
                try:
                    DestinationCoord = {
                        "lat" : Destination_PlaceToCoordResponse_data["latitude"],
                        "lng" : Destination_PlaceToCoordResponse_data["longitude"]
                    }
                    print(f"Coordinates Received")
                except Exception as e:
                    print(f"Error in fetching coordinates: {e}")
            else:
                print(f"Error: {Destination_PlaceToCoordResponse.status_code}")  # Handle errors

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
                                "latitude": driverCoord["lat"],
                                "longitude": driverCoord["lng"]
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

            #NUMBER 2
            #Send the new polyline into delivery api
            updateJson = {
                "polyline" : encoded_polyline,
                "driverCoord" : driverCoord
            }

            updateResponse = requests.put(DeliveryEndpoint + "/deliveryinfo/" + deliveryId,
                                            json=updateJson)
            
            if updateResponse.status_code == 200:
                print("Success in updating delivery")
            else:
                print(f"Error: {LocationResponse.status_code}")  # Handle errors
        else:
            #Send the current polyline into delivery api
            updateJson = {
                "polyline" : polyline,
                "driverCoord" : driverCoord
            }

            updateResponse = requests.put(DeliveryEndpoint + "/deliveryinfo/" + deliveryId,
                                            json=updateJson)

            if updateResponse.status_code == 200:
                print("Success in updating delivery")
            else:
                print(f"Error: {LocationResponse.status_code}")  # Handle errors

        # At the end of your function, after all the processing:
        return jsonify({
            "code": 200,
            "message": "Tracking updated successfully",
            "data": {
                "polyline": encoded_polyline if DeviationSuccess else polyline,
                "deviation" : DeviationSuccess
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    #update the deliveryId with new polyline and driverCoord
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5025)