# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def decode_polyline(polyline_str):
    """
    Decodes a Google Maps encoded polyline string into list of lat/lng coordinates.
    
    Args:
        polyline_str: The encoded polyline string
        
    Returns:
        A list of coordinate pairs [latitude, longitude]
    """
    # Initialize the index and output array
    index = 0
    lat = 0
    lng = 0
    coordinates = []
    
    # Process the entire string
    while index < len(polyline_str):
        # Process latitude
        result = 1
        shift = 0
        while True:
            b = ord(polyline_str[index]) - 63 - 1
            index += 1
            result += b << shift
            shift += 5
            if b < 0x1f:
                break
        lat += (~(result >> 1) if (result & 1) else (result >> 1))
        
        # Process longitude
        result = 1
        shift = 0
        while True:
            b = ord(polyline_str[index]) - 63 - 1
            index += 1
            result += b << shift
            shift += 5
            if b < 0x1f:
                break
        lng += (~(result >> 1) if (result & 1) else (result >> 1))
        
        # Add the coordinate pair to the output
        coordinates.append({
            "lat": lat * 1e-5,
            "lng": lng * 1e-5
        })
    
    return coordinates

@app.route('/decode', methods=['POST'])
def decode_route():
    """
    API endpoint to decode a polyline
    
    Expects JSON data with format: 
    {
        "polyline": "encoded_polyline_string"
    }
    
    Returns:
    {
        "coordinates": [
            {"lat": 37.12345, "lng": -122.54321},
            ...
        ]
    }
    """
    data = request.get_json()
    
    if not data or 'polyline' not in data:
        return jsonify({"error": "Missing required field 'polyline'"}), 400
        
    polyline = data['polyline']
    
    try:
        coordinates = decode_polyline(polyline)
        return jsonify({"coordinates": coordinates})
    except Exception as e:
        return jsonify({"error": f"Failed to decode polyline: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)