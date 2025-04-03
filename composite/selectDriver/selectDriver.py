from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import random

from common import invoke_http

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

DRIVER_INFO_ENDPOINT = "http://driverInfo_service:5004/drivers"
DELIVERY_ENDPOINT = "http://delivery_service:5002/deliveryinfo"
PlaceToCoord_ENDPOINT = "https://zsq.outsystemscloud.com/Location/rest/Location/PlaceToCoord"
Route_ENDPOINT = "https://zsq.outsystemscloud.com/Location/rest/Location/route"

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

        print(f"all drivers: {drivers}")

        # Filter available drivers
        available_drivers = [
            driver for driver in drivers
            if (not driver.get("isBooked")) and (not driver.get("awaitingAcknowledgement")) and (driver.get("stationed_hospital") == origin_address)
        ]

        print(f"origin address available_drivers: {available_drivers}")

        #drivers available at origin address
        if available_drivers:
            driver = random.choice(available_drivers)
            print(f"Chosen driver first round {driver}")
            driver_id = driver.get("driver_id")
            if not driver_id:
                return jsonify({"error": "Driver found but missing ID"}), 500
            
            return jsonify({
                "code": 200,
                "message": "Driver successfully found",
                "data": {"DriverId": driver_id}
            }), 200
        
        #need start finding drivers from other hospitals
        else:
            replacement_driver = ""
            hospital_address_dict = get_other_hospitals()
            

            sorted_dict_hospital_distances= get_sorted_hospital_distances(origin_address, hospital_address_dict)

            print(f"sorted_dict of addresses: {sorted_dict_hospital_distances}")

            #similar process as earlier but it starts searching from nearest hospital
            for name,duration in sorted_dict_hospital_distances.items():
                print(f"Looking elsewhere at {name} now")
                replacement_address = hospital_address_dict[name]
                available_drivers = [
                    driver for driver in drivers
                    if (not driver.get("isBooked")) and (not driver.get("awaitingAcknowledgement")) and (driver.get("stationed_hospital") == replacement_address)
                ]
                print(f"the available drivers at {name} are {available_drivers}")

                if available_drivers:
                    replacement_driver = random.choice(available_drivers)
                    print(f"The chosen replacement driver is {replacement_driver}")
                    driver_id = replacement_driver.get("driver_id")
                    if not driver_id:
                        return jsonify({"error": "Driver found but missing ID"}), 500
                    
                    return jsonify({
                        "code": 200,
                        "message": "Driver (different hospital) successfully found",
                        "data": {"DriverId": driver_id}
                    }), 200

            return jsonify({
                "code": 404,
                "message": "No Driver Found",
                "data": {"DriverId": 0}
            }), 404

    except requests.RequestException as e:
        return jsonify({"error": f"Driver service request failed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/acknowledge-driver", methods=['POST'])
def acknowledge_driver():
    """
    Expected input JSON:
    {
        driverID: XXX,
        deliveryId: XXX
    }
    """
    try:
        data = request.json()
        driverId = data.get("driverId")
        deliveryId = data.get("deliveryId")

        if not driverId:
            return jsonify({"error": "Missing driverId in request body."}), 400

        if not deliveryId:
            return jsonify({"error": "Missing deliveryId in request body."}), 400

        # Update Delivery atomic service
        delivery_url = f"{DELIVERY_ENDPOINT}/{deliveryId}"
        delivery_update = {"driverId": driverId, "status": "Assigned"}
        delivery_resp = invoke_http(delivery_url, method="PUT", json=delivery_update)
        

        # Update DriverInfo atomic service
        driver_url = f"{DRIVER_INFO_ENDPOINT}/{driverId}"
        
        driver_update = {"isBooked": True, "awaitingAcknowledgement": False}
        driver_resp = invoke_http(driver_url, method="PATCH", json=driver_update)

        return jsonify({
            "code": 200,
            "message": "Driver acknowledged and updated Driver & Delivery successfully."
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



def get_other_hospitals():
    return {
                "CGH": "2 Simei St 3, Singapore 529889",
                "SGH": "Outram Rd, Singapore 169608",
                "TTSH": "11 Jln Tan Tock Seng, Singapore 308433",
                "SKGH": "110 Sengkang E Wy, Singapore 544886",
                "NUH": "5 Lower Kent Ridge Rd, Singapore 119074",
                "KTPH": "90 Yishun Central, Singapore 768828",
                "NTFGH": "1 Jurong East Street 21, Singapore 609606"
            }


def get_lat(longname):
    longname_dict = {"long_name": longname}
    response = requests.post(PlaceToCoord_ENDPOINT, json=longname_dict)
    data = response.json()
    print(f"response_lat: {response}")
    print(f"response_lat: {data}")
    print(f"response_lat lat: {data.get('latitude')}")
    if data.get('status') == 'OK':
        lat = data.get("latitude")
        if lat:
            return lat
        else:
            return "Unable to get latitude"
    else:
        return "Error fetching latitude"
    
def get_lng(longname):
    longname_dict = {"long_name": longname}
    response = requests.post(PlaceToCoord_ENDPOINT, json=longname_dict)
    data = response.json()
    print(f"response_lng: {response}")
    print(f"response_lng: {data}")
    print(f"response_lng lng: {data.get('longitude')}")
    if data.get('status') == 'OK':
        lng = data.get("longitude")
        if lng:
            return lng
        else:
            return "Unable to get longitude"
    else:
        return "Error fetching longitude"
    

def get_sorted_hospital_distances(origin_address, hospital_address_dict):
    origin_lat = get_lat(origin_address)
    origin_lng = get_lng(origin_address)
    hospital_distances = {}


    for hospital in hospital_address_dict:
        address = hospital_address_dict[hospital]
        if address == origin_address: #if not will always return itself as nearest hospital
            continue
        other_lat = get_lat(address)
        other_lng = get_lng(address)
        latlng_dict = {
            "routingPreference": "TRAFFIC_AWARE",
            "travelMode": "DRIVE",
            "computeAlternativeRoutes": 'false',
            "destination": {
                "location": {
                "latLng": {
                    "latitude": other_lat,
                    "longitude": other_lng
                }
                }
            },
            "origin": {
                "location": {
                "latLng": {
                    "latitude": origin_lat,
                    "longitude": origin_lng
                }
                }
            }
        }
        response_Route = requests.post(Route_ENDPOINT, json=latlng_dict)
        data = response_Route.json()

        print(f"response_Route: {response_Route}")
        print(f"response_Route data: {data}")
        print(f"response_Route duration: {data['Route'][0]['Duration']}")

        if data.get('Status') == 'OK':
            if "Route" in data and len(data["Route"]) > 0:
                duration_string= data["Route"][0]["Duration"]
                duration = int(duration_string[:-1])
                print(duration_string)
                print(duration)
                hospital_distances[hospital] = duration
            else:
                print(f"Warning: No route data for hospital {hospital}")
        else:
            print(f"Error: Unable to fetch route data for hospital {hospital}")

    
    sorted_hospital_distances = dict(sorted(hospital_distances.items(), key=lambda item: item[1]))
    return sorted_hospital_distances



@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5024)
