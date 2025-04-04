from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import random
from common import invoke_http
import os
import pika
import json
import threading
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

DRIVER_INFO_ENDPOINT = "http://driverInfo_service:5004/drivers"
DELIVERY_ENDPOINT = "http://delivery_service:5002/deliveryinfo"
PlaceToCoord_ENDPOINT = "https://zsq.outsystemscloud.com/Location/rest/Location/PlaceToCoord"
Route_ENDPOINT = "https://zsq.outsystemscloud.com/Location/rest/Location/route"

# RabbitMQ connection parameters
rabbit_host = os.environ.get("rabbit_host", "rabbitmq")
rabbit_port = int(os.environ.get("rabbit_port", "5672"))

# Exchanges and queues configuration
EXCHANGES = {
    "driver_match_exchange": "direct", # Publish driver match request
    "notification_status_exchange": "topic"  # Add exchange for notification status
}

SUBSCRIBE_QUEUES = [
    {"name": "driver_match_request_queue", "exchange": "driver_match_exchange", "routing_key": "driver.request", "type": "direct"}
]

# Global connection and channel variables
connection = None
channel = None

def on_message(ch, method, properties, body):
    """Process incoming messages from RabbitMQ"""
    try:
        print(f"Received message: {body}")
        message = json.loads(body)
        
        delivery_id = message.get("deliveryId")
        origin_address = message.get("origin_address")
        destination_address = message.get("destination_address")
        
        print(f"Processing delivery request: id={delivery_id}, origin={origin_address}, destination={destination_address}")
        
        # Here you would implement any asynchronous processing needed
        # For example, updating driver status, sending notifications, etc.
        
        # Acknowledge the message to remove it from the queue
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        print(f"Error processing message: {e}")
        # Negative acknowledgment - message will be requeued
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def on_channel_open(ch):
    """Callback when the channel has been opened"""
    global channel
    channel = ch
    print("Channel opened for consuming")
    
    # Declare exchanges
    for exchange_name, exchange_type in EXCHANGES.items():
        print(f"Declaring exchange: {exchange_name} of type {exchange_type}")
        ch.exchange_declare(exchange=exchange_name, exchange_type=exchange_type, durable=True)
    
    # Declare queue and bind to exchange
    for queue_config in SUBSCRIBE_QUEUES:
        queue_name = queue_config["name"]
        
        ch.queue_declare(
            queue=queue_name,
            durable=True
        )
        
        ch.queue_bind(
            exchange=queue_config["exchange"],
            queue=queue_name,
            routing_key=queue_config["routing_key"]
        )
        
        # Set up consumer with QoS (prefetch count)
        ch.basic_qos(prefetch_count=1)
        ch.basic_consume(
            queue=queue_name,
            on_message_callback=on_message
        )
        
        print(f"Consumer set up for queue: {queue_name}")

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

def run_async_consumer():
    """Set up the asynchronous connection for consuming and start the IOLoop with a retry loop."""
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
            print("Starting IOLoop for consumer")
            conn.ioloop.start()
            break  # Exit the loop if the connection and loop run normally
        except pika.exceptions.AMQPConnectionError as e:
            print(f"AMQPConnectionError: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"Unexpected error: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def select_driver_internal(start_hospital, end_hospital, transplant_date_time):
    """Internal function to select a driver"""
    try:
        # Fetch driver data
        response = requests.get(DRIVER_INFO_ENDPOINT)
        response.raise_for_status()  # Raise exception for HTTP errors
        drivers = response.json()
        
        # Filter available drivers
        available_drivers = [
            driver for driver in drivers
            if not driver.get("isBooked") and driver.get("stationed_hospital") == start_hospital
        ]
        
        if available_drivers:
            driver_id = available_drivers[0].get("driver_id")
            if not driver_id:
                print("Driver found but missing ID")
                return None
            
            return driver_id
        
        print("No driver found for this request")
        return None
    except Exception as e:
        print(f"Error selecting driver: {e}")
        return None

def send_driver_notification(driver_id, driver_email, status):
    """Send notification about driver assignment via AMQP"""
    try:
        if not channel:
            print("RabbitMQ channel not available. Cannot send notification.")
            return False
            
        message = {
            "driverId": driver_id,
            "email": driver_email
        }
        
        # Choose the appropriate routing key based on status
        routing_key = f"{status}.status"
        
        print(f"Sending notification with routing key: {routing_key}")
        channel.basic_publish(
            exchange="notification_status_exchange",
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                content_type='application/json'
            )
        )
        print(f"Notification sent for driver {driver_id}")
        return True
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False

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
    print("Received request to select driver")
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
            print("Driver found")
            # driver_email = driver.get("email")
            driver_email = "weesuan.ang.2023@scis.smu.edu.sg"
            
            if not driver_id:
                return jsonify({"error": "Driver found but missing ID"}), 500
            
            # Send driver assigned notification
            if driver_email:
                send_driver_notification(driver_id, driver_email, "assigned")
            
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
    # Start RabbitMQ consumer in a separate thread
    consumer_thread = threading.Thread(target=run_async_consumer, daemon=True)
    consumer_thread.start()
    
    app.run(host='0.0.0.0', port=5024)