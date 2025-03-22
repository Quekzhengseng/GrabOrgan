from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

DRIVER_INFO_ENDPOINT = "http://driverInfo_service:5004/drivers"


@app.route('/selectDriver', methods=["POST"])
def select_driver():
    """
    Selects an available driver based on hospital location.

    Expects JSON input:
    {
        "transplantDateTime": String,
        "startHospital": String,
        "endHospital": String
    }

    Returns JSON response:
    {
        "code": int,
        "message": String,
        "data": {"DriverId": String or 0}
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        origin_address = data.get("startHospital")

        # Fetch driver data
        response = requests.get(DRIVER_INFO_ENDPOINT)
        response.raise_for_status()  # Raise exception for HTTP errors
        drivers = response.json()

        # Filter available drivers
        available_drivers = [
            driver for driver in drivers
            if not driver.get("isBooked") and driver.get("stationed_hospital") == origin_address
        ]

        if available_drivers:
            driver_id = available_drivers[0].get("driver_id")
            if not driver_id:
                return jsonify({"error": "Driver found but missing ID"}), 500
            
            return jsonify({
                "code": 200,
                "message": "Driver successfully found",
                "data": {"DriverId": driver_id}
            }), 200

        return jsonify({
            "code": 200,
            "message": "No Driver Found",
            "data": {"DriverId": 0}
        }), 200

    except requests.RequestException as e:
        return jsonify({"error": f"Driver service request failed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5024)
