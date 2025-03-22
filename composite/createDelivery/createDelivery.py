# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Service Endpoints
SERVICE_URLS = {
    "delivery": "http://delivery_service:5002",
    "geoalgo": "http://geoalgo_service:5006",
    "driver": "http://driverInfo_service:5004",
    "match_driver": "http://selectDriver:5024",
    "location": "https://zsq.outsystemscloud.com/Location/rest/Location/"
}

HEADERS = {'Content-Type': 'application/json'}
TIMEOUT = 10  # API timeout for requests


def make_request(url, method="POST", payload=None):
    """ Helper function to send HTTP requests with error handling. """
    try:
        if method == "POST":
            response = requests.post(url, headers=HEADERS, json=payload, timeout=TIMEOUT)
        else:  # GET request
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"HTTP Request failed: {e}")
        return None


def address_to_coord(address):
    """ Convert an address to latitude and longitude coordinates. """
    payload = {"long_name": address}
    response = make_request(SERVICE_URLS["location"] + "/PlaceToCoord", payload=payload)
    
    if response:
        return {"lat": response.get("latitude"), "lng": response.get("longitude")}
    return None


def retrieve_polyline(coord1, coord2):
    """ Retrieve a polyline route between two coordinates. """
    payload = {
        "routingPreference": "TRAFFIC_AWARE",
        "travelMode": "DRIVE",
        "computeAlternativeRoutes": False,
        "destination": {"location": {"latLng": {"latitude": coord2["lat"], "longitude": coord2["lng"]}}},
        "origin": {"location": {"latLng": {"latitude": coord1["lat"], "longitude": coord1["lng"]}}}
    }
    response = make_request(SERVICE_URLS["location"] + "/route", payload=payload)

    if response:
        return response.get("Route", [{}])[0].get("Polyline", {}).get("encodedPolyline")
    return None


def match_driver(destination_time, origin, destination):
    """ Match a driver for the given route and time. """
    payload = {"transplantDateTime": destination_time, "startHospital": origin, "endHospital": destination}
    response = make_request(SERVICE_URLS["match_driver"] + "/selectDriver", payload=payload)

    if response:
        return response.get("data", {}).get("DriverId")
    return None


def get_driver(driver_id):
    """ Get the driver's stationed hospital. """
    if not driver_id:
        return None

    response = make_request(f"{SERVICE_URLS['driver']}/drivers/{driver_id}", method="GET")

    if response:
        return response.get("stationed_hospital")
    return None


def create_delivery(origin, destination, polyline, driver_coord, driver_id, doctor_id):
    """ Create a new delivery entry. """
    payload = {
        "pickup": origin,
        "pickup_time": "20250315 10:30:00 AM",
        "destination": destination,
        "destination_time": "20250315 11:30:00 AM",
        "status": "Assigned",
        "polyline": polyline,
        "driverCoord": driver_coord,
        "driverID": driver_id,
        "doctorID": doctor_id,
    }
    
    response = make_request(SERVICE_URLS["delivery"] + "/deliveryinfo", payload=payload)

    if response:
        return response.get("data", {}).get("deliveryId")
    return None


@app.route('/createDelivery', methods=['POST'])
def create_delivery_composite():
    """ API endpoint to create a delivery. """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        origin_address = data.get("startHospital")
        destination_address = data.get("endHospital")
        doctor_id = data.get("DoctorId")
        destination_time = data.get("transplantDateTime")

        # Convert addresses to coordinates
        origin_coord = address_to_coord(origin_address)
        destination_coord = address_to_coord(destination_address)
        
        if not origin_coord or not destination_coord:
            return jsonify({"error": "Failed to convert addresses to coordinates"}), 400

        # Get polyline route
        encoded_polyline = retrieve_polyline(origin_coord, destination_coord)
        if not encoded_polyline:
            return jsonify({"error": "Failed to retrieve polyline"}), 400

        # Match a driver
        driver_id = match_driver(destination_time, origin_address, destination_address)
        if not driver_id:
            return jsonify({"error": "No matching driver found"}), 400

        # Get driver’s stationed hospital
        driver_address = get_driver(driver_id)
        if not driver_address:
            return jsonify({"error": "Failed to retrieve driver information"}), 400

        # Convert driver’s address to coordinates
        driver_coord = address_to_coord(driver_address)
        if not driver_coord:
            return jsonify({"error": "Failed to retrieve driver coordinates"}), 400

        # Create delivery
        delivery_id = create_delivery(origin_address, destination_address, encoded_polyline, driver_coord, driver_id, doctor_id)
        if not delivery_id:
            return jsonify({"error": "Failed to create delivery"}), 400

        return jsonify({"message": "Delivery successfully created", "data": {"DeliveryId": delivery_id}}), 200
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """ Health check endpoint. """
    return jsonify({"status": "healthy"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5026)
