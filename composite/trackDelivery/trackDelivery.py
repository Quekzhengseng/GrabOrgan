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

@app.route('/trackDelivery', methods=['POST'])
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