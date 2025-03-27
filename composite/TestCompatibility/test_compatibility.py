from flask import Flask, jsonify
from flask_cors import CORS
import pika
import json
import random
from datetime import datetime
import os
import threading
from common.invokes import invoke_http
import ast
import time

app = Flask(__name__)
CORS(app)

# RabbitMQ Connection Details
rabbit_host = os.environ.get("rabbit_host", "localhost") or "localhost"
rabbit_port = os.environ.get("rabbit_port", "5672")

# RabbitMQ Exchange & Routing Keys
TEST_COMPATIBILITY_EXCHANGE = "test_compatibility_exchange"
TEST_COMPATIBILITY_QUEUE = "test_compatibility_queue"
TEST_RESULT_EXCHANGE = "test_result_exchange"
MATCH_TEST_RESULT_ROUTING_KEY = "test.result"
ORGAN_ATOMIC_URL = os.environ.get("ORGAN_ATOMIC_URL") or "http://localhost:5009/organ"
MATCH_SERVICE_URL = os.environ.get("MATCH_SERVICE_URL") or "http://localhost:5008/matches"

@app.route("/", methods=['GET'])
def health_check():
    return jsonify({"code": 200, "status": "ok"}), 200

# Global channel for publishing messages (set when the channel opens)
channel = None

MAX_RETRIES = 3  # Maximum number of retry attempts

def handle_message(ch, method, properties, body):
    try:
        message_dict = ast.literal_eval(body.decode())
        print(f"Received message from {method.routing_key}: {message_dict}")
        
        if method.routing_key == "test.compatibility":
            print("Processing compatibility request...")
            response = process_message(message_dict)
            print("Publishing match results...")
            print(f"Match results sent: {response}")
        else:
            print("Unknown routing key.")
        
        # Acknowledge the message after successful processing.
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    except Exception as e:
        print(f"Error while handling message: {e}")
        
        # Retrieve current retry count from headers, defaulting to 0 if not present.
        retry_count = 0
        if properties.headers and 'x-retry-count' in properties.headers:
            retry_count = properties.headers['x-retry-count']
        print(f"Current retry count: {retry_count}")

        if retry_count < MAX_RETRIES:
            # Increase the retry count.
            new_retry_count = retry_count + 1

            # Create new properties with the updated retry count.
            new_properties = pika.BasicProperties(
                headers={"x-retry-count": new_retry_count},
                delivery_mode=properties.delivery_mode  # Preserve persistence if set.
            )

            # Republish the message with the updated headers.
            print(f"Republishing message, retry attempt {new_retry_count}")
            ch.basic_publish(
                exchange=method.exchange,
                routing_key=method.routing_key,
                body=body,
                properties=new_properties
            )
            # Acknowledge the current message so it is removed from the queue.
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            print("Max retries reached. Discarding message or sending to dead-letter queue.")
            # Here you could also publish the message to a dead-letter queue instead.
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
        auto_ack=False
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


def process_message(message_dict):
    """Process the matching request message as described earlier."""
    recipient_uuid = message_dict["recipientId"]
    organ_uuids = message_dict["listOfOrganId"]
    print(f"Received message for recipientId: {recipient_uuid}, organIds: {organ_uuids}")

    organ_data = {}
    for organ_uuid in organ_uuids:
        print(f"Fetching organ data for organId: {organ_uuid}...")
        organ_url = f"{ORGAN_ATOMIC_URL}/{organ_uuid}"
        organ_result = invoke_http(organ_url, method="GET", json=message_dict)
        

        if 'code' in organ_result and organ_result["code"] in range(200, 300):
            organ_data[organ_uuid] = organ_result
            print(f"Successfully fetched organ data: {organ_result}")
        else:
            print(f"Failed to fetch organ data for organId: {organ_uuid}. Error: {organ_result.get('message', 'Unknown error')}")
    
    # Generate randomized HLA matches
    matches = []
    HLA_THRESHOLD = 4
    for organ_uuid, organ_info in organ_data.items():
        donor_id = organ_info["donorId"]
        print(f"Creating match for organId: {organ_uuid} with donorId: {donor_id}")

        hla_matches = {f"hla-{i+1}": random.choice([True, False]) for i in range(6)}
        num_of_hla = sum(1 for match in hla_matches.values() if match)

        if num_of_hla >= HLA_THRESHOLD:
            match_id = f"{recipient_uuid}-{organ_uuid}"
            match_record = {
                "matchId": match_id,
                "recipientId": recipient_uuid,
                "donorId": donor_id,
                "organId": organ_uuid,
                **hla_matches,
                "numOfHLA": num_of_hla,
                "testDateTime": datetime.now().isoformat()
            }
            matches.append(match_record)
            print(f"Generated valid match: {match_record}")
        else:
            print(f"OrganId {organ_uuid} did not meet HLA threshold: {num_of_hla}/6")

    # Post valid matches to Match Atomic Service
    if matches:
        post_matches_to_match_service(matches)
    else:
        print("No valid HLA matches to post.")

    # Send match results to matchOrgan composite via AMQP
    match_ids = [match["matchId"] for match in matches]
    if match_ids:
        print(f"Sending match results via AMQP: {match_ids}")
        send_results_to_match_organ(match_ids)
    else:
        print("No matches found. Sending empty list to matchOrgan.")
        send_results_to_match_organ([])

    return {"listOfMatchId": match_ids}

def post_matches_to_match_service(matches):
    """POST valid matches to Match Atomic Service."""
    payload = {"matches": matches}
    response = invoke_http(MATCH_SERVICE_URL, method="POST", json=payload)
    if 'code' in response and response["code"] in range(200, 300):
        print("Matches posted successfully.")
    else:
        print(f"Failed to post matches. Error: {response.get('message', 'Unknown error')}")

def send_results_to_match_organ(match_ids):
    """Send results back to matchOrgan composite via AMQP (test.result)."""
    try:
        amqp_message = {"listOfMatchId": match_ids}
        channel.basic_publish(
            exchange=TEST_RESULT_EXCHANGE,
            routing_key=MATCH_TEST_RESULT_ROUTING_KEY,
            body=json.dumps(amqp_message),
            properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
        )
        print(f"AMQP message sent: {json.dumps(amqp_message)}")
    except Exception as e:
        print(f"Failed to send AMQP message: {str(e)}")

# Run the Flask app
if __name__ == "__main__":
    print(f"This is {os.path.basename(__file__)} - Test Compatibility Service")

    consumer_thread = threading.Thread(target=run_async_consumer, daemon=True)
    consumer_thread.start()

    # Start the Flask app in the main thread.
    app.run(host="0.0.0.0", port=5022, debug=True)
