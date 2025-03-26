from flask import Flask, jsonify
from flask_cors import CORS
import pika
import json
import requests
import os
import ast
import threading
import time
from datetime import datetime
import sys
from common import amqp_lib  # Assumes your reusable AMQP functions are here
from common.invokes import invoke_http


app = Flask(__name__)
CORS(app)

"""
for testing:
routing_key = test.compatibility
amqp message:
{"recipientId": "5RWWwCxq2M2eoXX91Z5BBsONTLs=", 
"listOfOrganId": ["27e4f60b-cornea", "27e4f60b-lungs", "6b94627a-lungs", "8e32a037-cornea", "8e32a037-liver"]
}

{
  "recipientId": "015051e7-0c87-4c13-9bb0-dd5e7584aabc",
  "listOfOrganId": [
    "1fdd282d-5eb7-42a8-b672-3dbb44557a29"
  ]
}
"""

# RabbitMQ Connection Details
rabbit_host = os.getenv("rabbit_host", "localhost")
rabbit_port = os.getenv("rabbit_port", "5672")

# RabbitMQ Exchange & Routing Keys
TEST_COMPATIBILITY_EXCHANGE = "test_compatibility_exchange"
TEST_COMPATIBILITY_QUEUE = "test_compatibility_queue"
TEST_RESULT_EXCHANGE = "test_result_exchange"
TEST_COMPATIBILITY_ROUTING_KEY = "test.compatibility"
MATCH_TEST_RESULT_ROUTING_KEY = "test.result"

# Lab Info & Match Atomic Service URLs
RECIPIENT_URL = os.environ.get("RECIPIENT_URL") or "http://localhost:5013/recipient"
LAB_INFO_URL = os.getenv("LAB_INFO_URL", "http://localhost:5007/lab-reports")
MATCH_SERVICE_URL = os.getenv("MATCH_SERVICE_URL", "http://localhost:5008/matches")

# Global connection and channel variables for reuse
@app.route("/", methods=['GET'])
def health_check():
    return jsonify({"code": 200, "status": "ok"}), 200

channel = None

def handle_message(ch, method, properties, body):
    """Callback function to process incoming messages."""
    try:
        message_dict = ast.literal_eval(body.decode())
        print(f"Received message from {method.routing_key}: {message_dict}")
    except Exception as e:
        print(f"Failed to parse message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag)
        return

    if method.routing_key == "test.compatibility":
        print("Processing compatibility request...")
        response = process_message(message_dict)
        print("Publishing match results...")
        channel.basic_publish(
            exchange=TEST_RESULT_EXCHANGE,
            routing_key=MATCH_TEST_RESULT_ROUTING_KEY,
            body=json.dumps(response),
            properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
        )
        print(f"Match results sent: {response}")
    else:
        print("Unknown routing key.")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def on_channel_open(ch):
    """Callback when the channel has been opened; set up consumers for all queues."""
    global channel
    channel = ch  # Save channel for later publishing
    print("Channel opened, setting up consumers...")
    print(f"Subscribing to queue: {TEST_COMPATIBILITY_QUEUE}")
    ch.basic_consume(
        queue=TEST_COMPATIBILITY_QUEUE,
        on_message_callback=handle_message,
        auto_ack=True
        )
    print("Consumers are set up. Waiting for messages...")

def on_connection_open(conn):
    """Callback when the connection is opened; create a channel."""
    print("Connection opened")
    conn.channel(on_open_callback=on_channel_open)

def on_connection_closed(conn, reply_code, reply_text=None):
    """Callback when the connection is closed."""
    print(f"Connection closed: reply_code={reply_code}, reply_text={reply_text}")
    conn.ioloop.stop()

def run_async_consumer():
    """Set up the asynchronous connection and start the IOLoop with a retry loop."""
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
            print("Starting IOLoop")
            conn.ioloop.start()
            break  # Exit the loop if the connection and loop run normally
        except pika.exceptions.AMQPConnectionError as e:
            print(f"AMQPConnectionError: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"Unexpected error: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def ensure_exchange_exists(channel, exchange, exchange_type):
    # Declare the exchange (it will only create it if it does not already exist)
    channel.exchange_declare(exchange=exchange, exchange_type=exchange_type, durable=True)

def fetch_lab_info(uuid):
    """Fetch a lab report from Lab Info Atomic using UUID."""
    try:
        response = requests.get(f"{LAB_INFO_URL}/{uuid}")
        if response.status_code == 200:
            lab_data = response.json().get("data", {})
            results = lab_data.get("results", {})
            lab_data.update(results)
            return lab_data
        elif response.status_code == 404:
            print(f"Lab report for UUID {uuid} not found.")
            return None
        else:
            print(f"Unexpected response from Lab Info Service: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching lab report: {str(e)}")
        return None

def fetch_recipient_lab_report(recipient_uuid):
    """Fetch recipient's lab report from Lab Info Atomic using UUID."""
    return fetch_lab_info(recipient_uuid)

def post_matches_to_match_service(matches):
    """POST valid matches to Match Atomic Service."""
    payload = {"matches": matches}
    try:
        response = requests.post(MATCH_SERVICE_URL, json=payload)
        if response.status_code == 201:
            print(f"Matches posted successfully: {json.dumps(payload)}")
        else:
            print(f"Failed to post matches. Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error posting matches: {str(e)}")
    sys.stdout.flush()

def process_message(message_dict):
    """
    Process an HLA matching request message.
    If the connection is closed, we reconnect (this check is optional).
    """
    global connection

    recipient_uuid = message_dict["recipientId"] # "recipientId" : string
    organ_uuids = message_dict["listOfOrganId"]  # "listOfOrganId": [String organId#1, organId#2 ...] 
    # check if the recipient exists first
    recipient_URL = RECIPIENT_URL + "/" + recipient_uuid
    print("Invoking recipient atomic service...")
    recipient_result = invoke_http(recipient_URL, method="GET", json=message_dict)
    message = json.dumps(recipient_result)
    code = recipient_result["code"]

    if code not in range(200, 300):
            return jsonify({
                "code": code,
                "data": {"recipientId": recipient_uuid},
                "message": recipient_result["message"]
            }), code 
    if len(organ_uuids) == 0:
        print("No organs specified in request.")
        return {"listOfMatchId": []}

    recipient_data = fetch_recipient_lab_report(recipient_uuid)
    if not recipient_data:
        return {"listOfMatchId": []}

    recipient_hla = recipient_data.get("hlaScore", 0)
    matches = []
    HLA_THRESHOLD = 4

    for organ_uuid in organ_uuids:
        donor_data = fetch_lab_info(organ_uuid)
        if not donor_data:
            continue

        donor_hla = donor_data.get("hlaScore", 0)
        if donor_hla < HLA_THRESHOLD:
            print(f"HLA mismatch: donor HLA {donor_hla} is below threshold {HLA_THRESHOLD}")
            continue

        match_id = f"{organ_uuid}-{recipient_uuid}"
        match_record = {
            "OrganId": donor_data.get("uuid"),
            "Test_DateTime": datetime.now().isoformat(),
            "donorId": donor_data.get("uuid"),
            "donor_details": {
                "blood_type": donor_data.get("blood_type", "B+"),
                "first_name": donor_data.get("first_name", "Chartreuse"),
                "gender": donor_data.get("gender", "Male"),
                "last_name": donor_data.get("last_name", "Lavender")
            },
            "matchId": match_id,
            "numOfHLA": donor_hla,
            "recipientId": recipient_uuid,
            "recipient_details": {
                "blood_type": recipient_data.get("blood_type", "AB+"),
                "first_name": recipient_data.get("first_name", "Nicholas"),
                "gender": recipient_data.get("gender", "Female"),
                "last_name": recipient_data.get("last_name", "Lam")
            }
        }
        matches.append(match_record)

    if matches:
        post_matches_to_match_service(matches)

    matched_ids = [m["matchId"] for m in matches]
    return {"listOfMatchId": matched_ids}

if __name__ == "__main__":
    print(f"This is {os.path.basename(__file__)} - Test Compatibility Service")
    # Start the RabbitMQ listener in a daemon thread so it doesn't block the main thread.
    consumer_thread = threading.Thread(target=run_async_consumer, daemon=True)
    consumer_thread.start()

    # Start the Flask app in the main thread.
    app.run(host="0.0.0.0", port=5022, debug=True)