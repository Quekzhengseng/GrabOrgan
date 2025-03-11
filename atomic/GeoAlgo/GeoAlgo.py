# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import math

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

# Helper function to calculate distance between two points using Haversine formula
def calculate_distance(point1, point2):
    """Calculate the distance between two lat/lng points in kilometers"""
    # Earth's radius in kilometers
    R = 6371
    
    # Convert lat/lng to radians
    lat1 = math.radians(point1['lat'])
    lng1 = math.radians(point1['lng'])
    lat2 = math.radians(point2['lat'])
    lng2 = math.radians(point2['lng'])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance

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


@app.route('/deviate', methods=['POST'])
def check_deviate():
    """
    API endpoint to check for deviation
    
    Expects JSON data with format: 
    {
        "polyline": "encoded_polyline_string",
        "driverCoord": {"lat": 37.12345, "lng": -122.54321}
    }
    
    Returns:
    {
        "code" : String,
        "data" : {
            "deviate": boolean
            }
    }
    """
    data = request.get_json()
    
    if not data or 'polyline' not in data or 'driverCoord' not in data:
        return jsonify({"error": "Missing required fields 'polyline' or 'driverCoord'"}), 400
    
    polyline = data['polyline']
    driver_coord = data['driverCoord']
    threshold_km = 0.05 #50 metres
    
    try:
        # Decode the polyline
        route_points = decode_polyline(polyline)
        
        # Calculate the minimum distance from driver to any point on the route
        min_distance = float('inf')
        closest_point = None
        
        for point in route_points:
            distance = calculate_distance(driver_coord, point)
            if distance < min_distance:
                min_distance = distance
                closest_point = point
        
        # Determine if driver has deviated
        is_deviated = min_distance > threshold_km
        
        return jsonify({
            "code" : 200,
            "data" : {
                "deviate": is_deviated
            },
            "message": "Success in calculating deviation"
        })
    
    except Exception as e:
        return jsonify({
            "code": 500,
            "message" : "Failed to process request"
            }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)