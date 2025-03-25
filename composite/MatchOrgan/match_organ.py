import os
import time
import json
import ast
import threading

from flask import Flask, jsonify
from flask_cors import CORS
import pika

from common.invokes import invoke_http

app = Flask(__name__)
CORS(app)

"""
for testing:
routing_key = match.request
amqp message:
{
"recipientId" : "5RWWwCxq2M2eoXX91Z5BBsONTLs="
}

routing_key = test.result
amqp message:
{
"listOfMatchId" : ["015051e7-0c87-4c13-9bb0-dd5e7584aabc-heart-12", "015051e7-0c87-4c13-9bb0-dd5e7584aabc-heart-29", "015051e7-0c87-4c13-9bb0-dd5e7584aabc-heart-5"]
}
"""

# Service URLs (these should come from environment variables or default to localhost)
RECIPIENT_URL = os.environ.get("RECIPIENT_URL") or "http://localhost:5013/recipient"
DONOR_URL = os.environ.get("DONOR_URL") or "http://localhost:5003/donor"
ORGAN_URL = os.environ.get("ORGAN_URL") or "http://localhost:5010/organ"
MATCH_URL = os.environ.get("MATCH_URL") or "http://localhost:5008/matches"

# RabbitMQ connection parameters
rabbit_host = os.environ.get("rabbit_host", "localhost")
rabbit_port = int(os.environ.get("rabbit_port", "5672"))

# Exchanges and queues configuration
EXCHANGES = {
    "request_organ_exchange": "direct",       # Listen for incoming organ requests
    "test_compatibility_exchange": "direct",    # Publish test requests
    "match_test_result_exchange": "direct",     # Listen for test results
    "match_result_exchange": "direct",          # Publish final match results
}

SUBSCRIBE_QUEUES = [
    {"name": "match_request_queue", "exchange": "request_organ_exchange", "routing_key": "match.request", "type": "direct"},
    {"name": "match_test_result_queue", "exchange": "test_result_exchange", "routing_key": "test.result", "type": "direct"},
]
@app.route("/", methods=['GET'])
def health_check():
    return jsonify({"code": 200, "status": "ok"}), 200

# Global channel for publishing messages (set when the channel opens)
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

    if method.routing_key == "match.request":
        print("Processing match request...")
        process_match_request(message_dict)
    elif method.routing_key == "test.result":
        print("Processing test result...")
        process_match_result(message_dict)
    else:
        print("Unknown routing key.")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def on_channel_open(ch):
    """Callback when the channel has been opened; set up consumers for all queues."""
    global channel
    channel = ch  # Save channel for later publishing
    print("Channel opened, setting up consumers...")
    for queue in SUBSCRIBE_QUEUES:
        print(f"Subscribing to queue: {queue['name']}")
        ch.basic_consume(
            queue=queue["name"],
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


def is_compatible(recipient_bloodType, donor_bloodType):
    blood_transfusion_rules = {
        "O-": {"O-"},
        "O+": {"O-", "O+"},
        "A-": {"O-", "A-"},
        "A+": {"O-", "O+", "A-", "A+"},
        "B-": {"O-", "B-"},
        "B+": {"O-", "O+", "B-", "B+"},
        "AB-": {"O-", "A-", "B-", "AB-"},
        "AB+": {"O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"}
    }
    return donor_bloodType in blood_transfusion_rules[recipient_bloodType]

def process_match_request(match_request_dict):
    recipient_id = match_request_dict["recipientId"]
    recipient_URL = RECIPIENT_URL + "/" + recipient_id
    print("Invoking recipient atomic service...")
    recipient_result = invoke_http(recipient_URL, method="GET", json=match_request_dict)
    message = json.dumps(recipient_result)
    code = recipient_result["code"]

    if code not in range(200, 300):
        print("Publish message with routing_key=match_request.error")
        channel.basic_publish(
            exchange="error_handling_exchange",
            routing_key="match_request.error",
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),
        )
        return jsonify({"code": 500, "data": {"recipient_result": recipient_result}, "message": "Error handling recipient."}), 500

    recipient_data = recipient_result["data"]
    recipient_bloodType = recipient_data["bloodType"]
    recipient_organsNeeded = recipient_data["organsNeeded"]
    print(f"Recipient blood type: {recipient_bloodType}")
    print(f"Recipient organs needed: {recipient_organsNeeded}")

    print("Invoking organ atomic service...")
    organ_result = invoke_http(ORGAN_URL, method="GET", json=match_request_dict)
    message = json.dumps(organ_result)
    code = organ_result["code"]

    if code not in range(200, 300):
        print("Publish message with routing_key=match_request.error")
        channel.basic_publish(
            exchange="error_handling_exchange",
            routing_key="match_request.error",
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),
        )
        return jsonify({"code": 500, "data": {"organ_result": organ_result}, "message": "Error handling organs."}), 500

    organ_data = organ_result["data"]
    organList = [organ["organId"] for organ in organ_data
                 if is_compatible(recipient_bloodType, organ["bloodType"]) and organ["organType"] in recipient_organsNeeded]
    print(f"Compatible Donor Organs: {organList}")

    message = json.dumps({"recipientId": recipient_id, "listOfOrganId": organList})

    if not organList:
        print("Publish message with routing_key=match_request.info")
        channel.basic_publish(
            exchange="activity_log_exchange",
            routing_key="match_request.info",
            body="No matches available",
            properties=pika.BasicProperties(delivery_mode=2),
        )
        return jsonify({"code": 204, "message": "No compatible matches found."}), 204

    print("Publish message with routing_key=match_request.info")
    channel.basic_publish(
        exchange="activity_log_exchange",
        routing_key="match_request.info",
        body=message,
        properties=pika.BasicProperties(delivery_mode=2),
    )
    print("Publish message with routing_key=test.compatibility")
    channel.basic_publish(
        exchange="test_compatibility_exchange",
        routing_key="test.compatibility",
        body=message,
        properties=pika.BasicProperties(delivery_mode=2),
    )

def process_match_result(match_test_result_dict):
    print("Invoking match atomic service...")
    match_result = invoke_http(MATCH_URL, method="GET", json=match_test_result_dict)
    message = json.dumps(match_result)
    code = match_result["code"]

    if code not in range(200, 300):
        print("Publish message with routing_key=match_test_result.error")
        channel.basic_publish(
            exchange="error_handling_exchange",
            routing_key="match_test_result.error.error",
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),
        )
        return jsonify({"code": 500, "data": {"matches_result": match_result}, "message": "Error handling matches."}), 500

    match_data = match_result["data"]
    match_test_result_list = [match for match in match_data if match["matchId"] in match_test_result_dict["listOfMatchId"]]
    print(f"match_details: {match_test_result_list}")

    message = json.dumps(match_test_result_list)

    print("Publish message with routing_key=match_result.info")
    channel.basic_publish(
        exchange="activity_log_exchange",
        routing_key="match_result.info",
        body=message,
        properties=pika.BasicProperties(delivery_mode=2),
    )
    # Need to somehow notify the frontend that the matches found are done, then allow user to confirm match
    # maybe it goes to a notification service?


@app.route("/initiate-match/<string:recipientId>", methods=['POST'])
def initiate_match(recipientId):
    try:
        recipient_URL = RECIPIENT_URL + "/" + recipientId
        print("Invoking recipient atomic service...")
        recipient_result = invoke_http(recipient_URL, method="GET")
        message = json.dumps(recipient_result)
        code = recipient_result["code"]

        if code not in range(200, 300):
            return jsonify({
                "code": code,
                "data": {"recipientId": recipientId},
                "message": recipient_result["message"]
            }), code 
        else:
            print("Publishing message with routing_key=", "match.request")
            # Prepare the message as a JSON string
            message_body = json.dumps({"recipientId": recipientId})
            channel.basic_publish(
                exchange="request_organ_exchange",
                routing_key="match.request",
                body=message_body,
                properties=pika.BasicProperties(delivery_mode=2)  # make message persistent
            )
            # Return a response immediately
            return jsonify({
                "code": 202,
                "message": "Match initiation request accepted. You will be notified once the match is completed."
            }), 202

    except Exception as e:
        print("Error initiating match:", str(e))
        return jsonify({
            "code": 500,
            "message": "An error occurred while initiating the match: " + str(e)
        }), 500

@app.route("/confirm-match/<string:matchId>", methods=['POST'])
def confirm_match(matchId):

    try:
        # Extract recipientId from the JSON payload
        print("Invoking match atomic service...")
        match_url = MATCH_URL + "/" + matchId
        match_result = invoke_http(match_url, method="GET")
        message = json.dumps(match_result)
        code = match_result["code"]

        if code not in range(200, 300):
            return jsonify({
                "code": code,
                "data": {"recipientId": matchId},
                "message": match_result["message"]
            }), code 
        else:
            print("Publishing message with routing_key=", "match.confirm")
            # Prepare the message as a JSON string
            message_body = json.dumps({"matchId": matchId})
            channel.basic_publish(
                exchange="confirm_match_exchange",
                routing_key="match.confirm",
                body=message_body,
                properties=pika.BasicProperties(delivery_mode=2)  # make message persistent
            )
            # Return a response immediately
            return jsonify({
                "code": 202,
                "message": "Match initiation request accepted. You will be notified once the match is completed."
            }), 202

    except Exception as e:
        print("Error initiating match:", str(e))
        return jsonify({
            "code": 500,
            "message": "An error occurred while initiating the match: " + str(e)
        }), 500


if __name__ == "__main__":
    print("This is flask " + os.path.basename(__file__) + " for matching an organ...")
    # Run the asynchronous AMQP consumer in a separate daemon thread.
    consumer_thread = threading.Thread(target=run_async_consumer, daemon=True)
    consumer_thread.start()

    # Now run the Flask server in the main thread.
    app.run(host="0.0.0.0", port=5020, debug=True)