# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import requests
import os
import pika
import time
import uuid
import threading

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

# hospital_coords_dict = {
#         "CGH": {
#             "address": "2 Simei St 3, Singapore 529889",
#         },
#         "SGH": {
#             "address": "Outram Rd, Singapore 169608",
#         },
#         "TTSH": {
#             "address": "11 Jln Tan Tock Seng, Singapore 308433",
#         },
#         "SKGH": {
#             "address": "110 Sengkang E Wy, Singapore 544886",
#         },
#         "NUH": {
#             "address": "5 Lower Kent Ridge Rd, Singapore 119074",
#         },
#         "KTPH": {
#             "address": "90 Yishun Central, Singapore 768828",
#         },
#         "NTFGH": {
#             "address": "1 Jurong East Street 21, Singapore 609606",
#         }
#     }

# RabbitMQ connection parameters
rabbit_host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
rabbit_port = int(os.environ.get("RABBITMQ_PORT", "5672"))
print('RabbitMQ host:', rabbit_host)

# Exchanges and queues configuration
EXCHANGES = {
    "driver_match_exchange": "direct" # Publish driver match request
}

ROUTING_KEYS = {
    "driver_request": "driver.request"
}
print('exchange & keys declared')

HEADERS = {'Content-Type': 'application/json'}
TIMEOUT = 10  # API timeout for requests

# Global channel variable
channel = None
connection = None


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

# AMQP selection for driver
def publish_delivery_request(delivery_id, origin_address, destination_address):
    """Publish delivery request to RabbitMQ"""
    global channel
    
    if channel is None or not channel.is_open:
        print("Channel is not open, cannot publish message")
        return False
    
    message = {
        "deliveryId": delivery_id,
        "origin_address": origin_address,
        "destination_address": destination_address
    }
    
    try:
        channel.basic_publish(
            exchange='driver_match_exchange',
            routing_key='driver.request',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type='application/json'
            )
        )
        print(f"Published delivery request for delivery_id={delivery_id}")
        return True
    except Exception as e:
        print(f"Failed to publish message: {e}")
        return False

# def match_driver(destination_time, origin, destination):
#     """ Match a driver for the given route and time. """
#     payload = {"transplantDateTime": destination_time, "startHospital": origin, "endHospital": destination}
#     response = make_request(SERVICE_URLS["match_driver"] + "/selectDriver", payload=payload)

#     if response:
#         return response.get("data", {}).get("DriverId")
#     return None


def get_driver(driver_id):
    """ Get the driver's stationed hospital. """
    if not driver_id:
        return None

    response = make_request(f"{SERVICE_URLS['driver']}/drivers/{driver_id}", method="GET")

    if response:
        return response.get("stationed_hospital")
    return None


def create_delivery(origin, destination, polyline, organ_type, matchId, driver_coord=None, driver_id=None):
    """ Create a new delivery entry. """
    payload = {
        "pickup": origin,
        "pickup_time": "20250315 10:30:00 AM",
        "destination": destination,
        "destination_time": "20250315 11:30:00 AM",
        "status": "Searching",
        "polyline": polyline,
        "driverCoord": driver_coord,
        "driverId": driver_id,
        "organType": organ_type,
        "matchId": matchId,
    }
    
    response = make_request(SERVICE_URLS["delivery"] + "/deliveryinfo", payload=payload)

    if response:
        return response.get("data", {}).get("deliveryId")
    return None

def on_channel_open(ch):
    """Callback when the channel has been opened"""
    global channel
    channel = ch  # Save channel for later publishing
    print("Channel opened for publishing")
    
    # Declare exchanges
    for exchange_name, exchange_type in EXCHANGES.items():
        print(f"Declaring exchange: {exchange_name} of type {exchange_type}")
        ch.exchange_declare(exchange=exchange_name, exchange_type=exchange_type, durable=True)
        
    # Declare the queue and bind it to the exchange
    ch.queue_declare(
        queue='driver_match_request_queue',
        durable=True
    )
    
    ch.queue_bind(
        exchange='driver_match_exchange',
        queue='driver_match_request_queue',
        routing_key='driver.request'
    )
    
    print("Queue declared and bound to exchange")


def on_connection_open(conn):
    """Callback when the connection is opened; create a channel."""
    global connection
    connection = conn
    print("RabbitMQ connection opened")
    conn.channel(on_open_callback=on_channel_open)


def on_connection_closed(conn, reply_code, reply_text=None):
    """Callback when the connection is closed."""
    print(f"RabbitMQ connection closed: reply_code={reply_code}, reply_text={reply_text}")
    global connection, channel
    connection = None
    channel = None
    conn.ioloop.stop()


def run_async_publisher():
    """Set up the asynchronous connection for publishing and start the IOLoop with a retry loop."""
    print(f"Connecting to RabbitMQ with host={rabbit_host}, port={rabbit_port}")
    parameters = pika.ConnectionParameters(
        host=rabbit_host,
        port=rabbit_port,
        heartbeat=300,
        blocked_connection_timeout=300
    )
    while True:
        try:
            print(f"Attempting to connect to RabbitMQ at {rabbit_host}:{rabbit_port} ...")
            conn = pika.SelectConnection(
                parameters=parameters,
                on_open_callback=on_connection_open,
                on_close_callback=on_connection_closed
            )
            print("Starting IOLoop for publisher")
            conn.ioloop.start()
            break  # Exit the loop if the connection and loop run normally
        except pika.exceptions.AMQPConnectionError as e:
            print(f"AMQPConnectionError: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"Unexpected error: {e}. Retrying in 5 seconds...")
            time.sleep(5)

@app.route('/createDelivery', methods=['POST'])
def create_delivery_composite():
    """API endpoint to create a delivery."""
    print('Received request to create delivery')
    try:
        print('Request data:', request.data)
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        origin_address = data.get("startHospital")
        destination_address = data.get("endHospital")
        destination_time = data.get("transplantDateTime")
        organ_type = data.get("organType")
        matchId = data.get("matchId")

        # Convert addresses to coordinates
        origin_coord = address_to_coord(origin_address)
        destination_coord = address_to_coord(destination_address)
        
        if not origin_coord or not destination_coord:
            return jsonify({"error": "Failed to convert addresses to coordinates"}), 400

        # Get polyline route
        encoded_polyline = retrieve_polyline(origin_coord, destination_coord)
        if not encoded_polyline:
            return jsonify({"error": "Failed to retrieve polyline"}), 400
        
        # Create delivery record
        print('Creating delivery record...')
        delivery_id = create_delivery(origin_address, destination_address, encoded_polyline, organ_type, matchId)
        if not delivery_id:
            return jsonify({"error": "Failed to create delivery"}), 400

        # # Match a driver
        # driver_id = match_driver(destination_time, origin_address, destination_address)
        # if not driver_id:
        #     return jsonify({"error": "No matching driver found"}), 400

        # Publish driver request to RabbitMQ for asynchronous driver selection
        publish_delivery_request(delivery_id, data.get("startHospital"), data.get("endHospital"))
        
        # # Get driver’s stationed hospital
        # driver_address = get_driver(driver_id)
        # if not driver_address:
        #     return jsonify({"error": "Failed to retrieve driver information"}), 400

        # # Convert driver’s address to coordinates
        # driver_coord = address_to_coord(driver_address)
        # if not driver_coord:
        #     return jsonify({"error": "Failed to retrieve driver coordinates"}), 400

        return jsonify({"message": "Delivery successfully created and driver selection initiated", "data": {"DeliveryId": delivery_id}}), 200
    except Exception as e:
        print("Error in create_delivery_composite:", str(e))
        return jsonify({"code": 500, "message": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """ Health check endpoint. """
    return jsonify({"status": "healthy"})


if __name__ == '__main__':
    # Start the RabbitMQ publisher in a separate thread
    threading.Thread(target=run_async_publisher, daemon=True).start()

    app.run(host='0.0.0.0', port=5026)
