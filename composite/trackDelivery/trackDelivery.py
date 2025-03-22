from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# Define service endpoints
SERVICE_URLS = {
    "delivery": "http://delivery_service:5002",
    "driver": "http://driver_service:5003",
    "driver_info": "http://driverInfo_service:5004",
    "geo_algo": "http://geoalgo_service:5006",
    "location": "https://zsq.outsystemscloud.com/Location/rest/Location"
}

HEADERS = {'Content-Type': 'application/json'}

def addressToCoord(address):
    """Convert an address to latitude/longitude coordinates."""
    try:
        response = requests.post(f"{SERVICE_URLS['location']}/PlaceToCoord", headers=HEADERS, json={"long_name": address}, timeout=5)
        response.raise_for_status()
        data = response.json()
        return {"lat": data.get("latitude"), "lng": data.get("longitude")}
    except requests.exceptions.RequestException as e:
        print(f"Error in addressToCoord: {e}")
        return None

def retrievePolyline(coord1, coord2):
    """Retrieve a polyline route between two coordinates."""
    payload = {
        "routingPreference": "TRAFFIC_AWARE",
        "travelMode": "DRIVE",
        "computeAlternativeRoutes": False,
        "destination": {"location": {"latLng": {"latitude": coord2['lat'], "longitude": coord2['lng']}}},
        "origin": {"location": {"latLng": {"latitude": coord1['lat'], "longitude": coord1['lng']}}}
    }
    try:
        response = requests.post(f"{SERVICE_URLS['location']}/route", headers=HEADERS, json=payload, timeout=5)
        response.raise_for_status()
        return response.json().get("Route", [{}])[0].get("Polyline", {}).get("encodedPolyline")
    except requests.exceptions.RequestException as e:
        print(f"Error in retrievePolyline: {e}")
        return None

def getDelivery(deliveryId):
    """Retrieve delivery information by ID."""
    try:
        response = requests.get(f"{SERVICE_URLS['delivery']}/deliveryinfo/{deliveryId}", timeout=5)
        response.raise_for_status()
        return response.json().get("data")
    except requests.exceptions.RequestException as e:
        print(f"Error in getDelivery: {e}")
        return None

def getDeviation(polyline, driverCoord):
    """Check if the driver has deviated from the route."""
    try:
        response = requests.post(f"{SERVICE_URLS['geo_algo']}/deviate", headers=HEADERS, json={"polyline": polyline, "driverCoord": driverCoord}, timeout=5)
        response.raise_for_status()
        return response.json().get("data", {}).get("deviate")
    except requests.exceptions.RequestException as e:
        print(f"Error in getDeviation: {e}")
        return None

def updateDelivery(encoded_polyline, driverCoord, status, deliveryId):
    """Update the delivery details."""
    try:
        response = requests.put(f"{SERVICE_URLS['delivery']}/deliveryinfo/{deliveryId}", json={"polyline": encoded_polyline, "driverCoord": driverCoord, "status": status}, timeout=5)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error in updateDelivery: {e}")
        return False

@app.route('/trackDelivery', methods=['POST'])
def updateDeliveryComposite():
    """Update delivery tracking information, handling deviations if necessary."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        deliveryId = data.get("deliveryId")
        driverCoord = data.get("driverCoord")

        if not (deliveryId and driverCoord):
            return jsonify({"error": "Missing required fields"}), 400

        # Retrieve delivery information
        deliveryData = getDelivery(deliveryId)
        if not deliveryData:
            return jsonify({"error": "Failed to retrieve delivery"}), 500

        polyline = deliveryData.get("polyline")
        if not polyline:
            return jsonify({"error": "Missing polyline in delivery data"}), 500

        # Check if the driver has deviated
        deviation = getDeviation(polyline, driverCoord)
        if deviation is None:
            return jsonify({"error": "Failed to check deviation"}), 500

        if deviation:
            # Retrieve new polyline if deviation occurs
            destination = addressToCoord(deliveryData.get("destination"))
            if not destination:
                return jsonify({"error": "Failed to retrieve destination coordinates"}), 500

            new_polyline = retrievePolyline(driverCoord, destination)
            if not new_polyline:
                return jsonify({"error": "Failed to retrieve new polyline"}), 500

            success = updateDelivery(new_polyline, driverCoord, "In Progress", deliveryId)
            if not success:
                return jsonify({"error": "Failed to update delivery"}), 500
        else:
            success = updateDelivery(polyline, driverCoord, "In Progress", deliveryId)
            if not success:
                return jsonify({"error": "Failed to update delivery"}), 500

        return jsonify({
            "code": 200,
            "message": "Tracking updated successfully",
            "data": {"polyline": new_polyline if deviation else polyline, "deviation": deviation}
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5025)
