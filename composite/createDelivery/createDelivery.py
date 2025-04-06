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
    "location": "https://zsq.outsystemscloud.com/Location/rest/Location"
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
    "driver_match_exchange": "direct",  # Publish driver match request
    "order_exchange": "direct"          # Add this to listen for order messages
}

ROUTING_KEYS = {
    "driver_request": "driver.request"
}

SUBSCRIBE_QUEUES = [
    {"name": "order_queue", "exchange": "order_exchange", "routing_key": "order.organ", "type": "direct"}
]

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
def publish_delivery_request(origin_address):
    """Publish delivery request to RabbitMQ"""
    global channel
    
    if channel is None or not channel.is_open:
        print("Channel is not open, cannot publish message")
        return False
    
    message = {
        "origin_address": origin_address,
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

def create_delivery(origin, destination, destination_time, polyline, organ_type, doctorId, matchId, driver_coord=None, driver_id=None):    
    """ Create a new delivery entry. """
    payload = {
        "pickup": origin,
        "pickup_time": "20250315 10:30:00 AM",
        "destination": destination,
        "destination_time": destination_time,
        "status": "Searching",
        "polyline": polyline,
        "driverCoord": driver_coord,
        "driverId": driver_id,
        "organType": organ_type,
        "doctorId": doctorId,
        "matchId": matchId,
    }
    
    response = make_request(SERVICE_URLS["delivery"] + "/deliveryinfo", payload=payload)

    if response:
        return response.get("data", {}).get("deliveryId")
    return None

# Modify your on_channel_open function to set up consumers
def on_channel_open(ch):
    """Callback when the channel has been opened"""
    global channel
    channel = ch  # Save channel for later publishing
    print("Channel opened for publishing and consuming")
    
    # Declare exchanges
    for exchange_name, exchange_type in EXCHANGES.items():
        print(f"Declaring exchange: {exchange_name} of type {exchange_type}")
        ch.exchange_declare(exchange=exchange_name, exchange_type=exchange_type, durable=True)
        
    # Declare the queue and bind it to the exchange for publishing
    ch.queue_declare(
        queue='driver_match_request_queue',
        durable=True
    )
    
    ch.queue_bind(
        exchange='driver_match_exchange',
        queue='driver_match_request_queue',
        routing_key='driver.request'
    )
    
    # Set up consumers for subscribing
    for queue in SUBSCRIBE_QUEUES:
        queue_name = queue["name"]
        exchange = queue["exchange"]
        routing_key = queue["routing_key"]
        
        print(f"Declaring queue: {queue_name}")
        ch.queue_declare(queue=queue_name, durable=True)
        
        print(f"Binding queue {queue_name} to exchange {exchange} with routing key {routing_key}")
        ch.queue_bind(
            exchange=exchange,
            queue=queue_name,
            routing_key=routing_key
        )
        
        print(f"Setting up consumer for queue: {queue_name}")
        ch.basic_consume(
            queue=queue_name,
            on_message_callback=handle_message,
            auto_ack=False
        )
    
    print("Queues declared, bound to exchanges, and consumers set up")

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


# Rename your main function
def run_async_rabbitmq():
    """Set up the asynchronous connection for both publishing and consuming."""
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
            print("Starting IOLoop for RabbitMQ")
            conn.ioloop.start()
            break  # Exit the loop if the connection and loop run normally
        except pika.exceptions.AMQPConnectionError as e:
            print(f"AMQPConnectionError: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"Unexpected error: {e}. Retrying in 5 seconds...")
            time.sleep(5)


def handle_message(ch, method, properties, body):
    try:
        print(f"Received message from {method.routing_key}: {body}")
        message_dict = json.loads(body.decode())
        
        # Process the message based on the routing key
        if method.routing_key == "order.organ":
            print("Processing order.organ message...")
            order_id = message_dict.get("orderId")
            
            if not order_id:
                print("No orderId found in message")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
                
            # Fetch order details from your order service
            order_url = f"http://order_service:5009/order/{order_id}"
            order_response = make_request(order_url, method="GET")
            
            if not order_response:
                print(f"Failed to retrieve order details for order_id: {order_id}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            
            order_details = order_response.get("data", {})
            print(f"Order details: {order_details}")

            try:
                # Extract the required fields from order_details
                origin_address = order_details.get("startHospital")
                destination_address = order_details.get("endHospital")
                destination_time = order_details.get("transplantDateTime")
                organ_type = order_details.get("organType")
                doctorId = order_details.get("doctorId")
                match_id = order_details.get("matchId")

                print({
                    origin_address, 
                    destination_address, 
                    destination_time, 
                    organ_type, 
                    doctorId,
                    match_id
                })
                
                # Convert addresses to coordinates
                origin_coord = address_to_coord(origin_address)
                destination_coord = address_to_coord(destination_address)
                
                if not origin_coord or not destination_coord:
                    print("Failed to convert addresses to coordinates")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return

                # Get polyline route
                encoded_polyline = retrieve_polyline(origin_coord, destination_coord)
                if not encoded_polyline:
                    print("Failed to retrieve polyline")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return
                
                # Create delivery record
                print('Creating delivery record...')
                delivery_id = create_delivery(
                    origin_address, 
                    destination_address, 
                    destination_time, 
                    encoded_polyline, 
                    organ_type, 
                    doctorId,
                    match_id
                )
                
                if not delivery_id:
                    print("Failed to create delivery")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return

                # Publish driver request to RabbitMQ for asynchronous driver selection
                publish_delivery_request(origin_address)
                
                print(f"Delivery successfully created with ID: {delivery_id}")

                message = json.dumps({
                    "event": "delivery_created",
                    "deliveryId": delivery_id,
                    "timestamp": time.time()
                })

                channel.basic_publish(
                exchange="activity_log_exchange",
                routing_key="create_delivery.info",
                body=message,
                properties=pika.BasicProperties(delivery_mode=2)
            )
                
            except Exception as inner_e:
                print(f"Error processing delivery: {inner_e}")
        
        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        print(f"Error processing message: {e}")
        error_payload = json.dumps({
            "event": "Error processing message",
            "error": e,
            "timestamp": time.time()
        })

        channel.basic_publish(
        exchange="error_handling_exchange",
        routing_key="create_delivery.error",
        body=error_payload,
        properties=pika.BasicProperties(delivery_mode=2)
            )
        
        # Negative acknowledge with requeue=False
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


@app.route('/health', methods=['GET'])
def health_check():
    """ Health check endpoint. """
    return jsonify({"status": "healthy"})


# Update your main block
if __name__ == '__main__':
    # Start the RabbitMQ handler in a separate thread
    threading.Thread(target=run_async_rabbitmq, daemon=True).start()

    app.run(host='0.0.0.0', port=5026)
