# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/createDelivery', methods=['POST'])
def createDelivery():
    """
    API endpoint to decode a polyline
    
    Expects JSON data with format: 
    {
        "matchID" : String
    }
    
    Returns:
    {
        "Success" : boolean
        "deliveryID" : String
    }
    """
    
    #Draw from match with matchID
    #Retrieve driverID, DoctorID, originCoord, DestinationCoord, EndTime
    
    #Connect to delivery API
    #Create a new delivery with driverID, DoctorID, originCoord, DestinationCoord, EndTime, polyline, status


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
        "Polyline" : String
    }
    """
    
    #Draw the delivery with deliveryId
    #Check for deviation given driverCoord

    #If deviate, return new polyline
    
    #update the deliveryId with new polyline and driverCoord


@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)