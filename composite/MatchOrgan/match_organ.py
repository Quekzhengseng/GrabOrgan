import os
import time
import json
import ast
import threading

from flask import Flask, jsonify, request
from flask_cors import CORS
import pika
import uuid
import requests

from common.invokes import invoke_http

app = Flask(__name__)
CORS(app, origins="http://localhost:3000")  # or origins="*"
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
ORDER_URL = os.environ.get("ORDER_URL") or "http://localhost:5009/order"

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

MAX_RETRIES = 3  # Maximum number of retry attempts

def handle_message(ch, method, properties, body):
    try:
        message_dict = ast.literal_eval(body.decode())
        print(f"Received message from {method.routing_key}: {message_dict}")
        
        # Process the message based on the routing key.
        if method.routing_key == "match.request":
            print("Processing match request...")
            process_match_request(message_dict)
        elif method.routing_key == "test.result":
            print("Processing test result...")
            process_match_result(message_dict)
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
    for queue in SUBSCRIBE_QUEUES:
        print(f"Subscribing to queue: {queue['name']}")
        ch.basic_consume(
            queue=queue["name"],
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
    try:
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
                properties=pika.BasicProperties(delivery_mode=2)
            )
            return jsonify({
                "code": 500, 
                "data": {"recipient_result": recipient_result}, 
                "message": "Error handling recipient."
            }), 500

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
                properties=pika.BasicProperties(delivery_mode=2)
            )
            return jsonify({
                "code": 500, 
                "data": {"organ_result": organ_result}, 
                "message": "Error handling organs."
            }), 500

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
                properties=pika.BasicProperties(delivery_mode=2)
            )
            return jsonify({"code": 204, "message": "No compatible matches found."}), 204

        print("Publish message with routing_key=match_request.info")
        channel.basic_publish(
            exchange="activity_log_exchange",
            routing_key="match_request.info",
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        print("Publish message with routing_key=test.compatibility")
        channel.basic_publish(
            exchange="test_compatibility_exchange",
            routing_key="test.compatibility",
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )
    except Exception as e:
        print("Error in process_match_request:", str(e))
        error_payload = json.dumps({
            "error": str(e),
            "match_request": match_request_dict
        })
        try:
            channel.basic_publish(
                exchange="error_handling_exchange",
                routing_key="match_request.error",
                body=error_payload,
                properties=pika.BasicProperties(delivery_mode=2)
            )
        except Exception as publish_exception:
            print("Failed to publish error message:", str(publish_exception))
        return jsonify({"code": 500, "message": "Error processing match request."}), 500

def process_match_result(match_test_result_dict):
    try:
        print("Invoking match atomic service...")
        match_result = invoke_http(MATCH_URL, method="GET", json=match_test_result_dict)
        match_data = match_result["data"]
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
            return jsonify({
                "code": 500,
                "data": {"matches_result": match_result},
                "message": "Error handling matches."
            }), 500

        list_of_match_ids = match_test_result_dict["listOfMatchId"]
        print(f"Shortlisted Matches: {list_of_match_ids}")

        message = json.dumps(match_test_result_dict)
        print("Publish message with routing_key=match_result.info")
        channel.basic_publish(
            exchange="activity_log_exchange",
            routing_key="match_result.info",
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),
        )
    # Need to somehow notify the frontend that the matches found are done, then allow user to confirm match
    # maybe it goes to a notification service?

    except Exception as e:
        print("Error in process_match_result:", str(e))
        error_payload = json.dumps({
            "error": str(e),
            "match_test_result_dict": match_test_result_dict
        })
        try:
            channel.basic_publish(
                exchange="error_handling_exchange",
                routing_key="match_result.error",
                body=error_payload,
                properties=pika.BasicProperties(delivery_mode=2)
            )
        except Exception as publish_exception:
            print("Failed to publish error message:", str(publish_exception))
        return jsonify({"code": 500, "message": "Error processing match result."}), 500


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

@app.route("/confirm-match", methods=['POST', 'OPTIONS'])
def confirm_match():
    """
    Store this in Order DB
    orderId = str(uuid.uuid4())
    orderId = {
        "orderId" : str(uuid.uuid4()),
	    "organType": "heart",
        "doctorId" : "isaidchia@gmail.com",
	    "transplantDateTime": "2025-03-30T23:30:00.000Z", # UTC
	    "startHospital": "CGH",
	    "endHospital": "TTSH",
	    "matchId": "015051e7-0c87-4c13-9bb0-dd5e7584aabc-heart-12",
	    "remarks": "description (if any)"
    }

    rabbitMQ Message
    exchange: order_exchange
    queue: order_queue
    routing_key = order.organ
    message:
    {
    "orderId": "String uuid"
    }
    """
    hospital_coords_dict = {
        "CGH": {
            "address": "2 Simei St 3, Singapore 529889",
            "latitude": 1.3402380226275528,
            "longitude": 103.9496741599837
        },
        "SGH": {
            "address": "Outram Rd, Singapore 169608",
            "latitude": 1.2805689453652151,
            "longitude": 103.83504895409699
        },
        "TTSH": {
            "address": "11 Jln Tan Tock Seng, Singapore 308433",
            "latitude": 1.3214817166088648,
            "longitude": 103.84583143700398
        },
        "SKGH": {
            "address": "110 Sengkang E Wy, Singapore 544886",
            "latitude": 1.3956165090489552, 
            "longitude": 103.89350071151229
        },
        "NUH": {
            "address": "5 Lower Kent Ridge Rd, Singapore 119074",
            "latitude": 1.295203845567723, 
            "longitude": 103.7828300893688
        },
        "KTPH": {
            "address": "90 Yishun Central, Singapore 768828",
            "latitude": 1.4245009834534053, 
            "longitude": 103.83861215383979
        },
        "NTFGH": {
            "address": "1 Jurong East Street 21, Singapore 609606",
            "latitude": 1.333905687585315, 
            "longitude": 103.74565971707347
        }
    }

    try:
        data =  request.get_json()
        # print(data)
        orderId = str(uuid.uuid4())
        matchId = data.get("matchId")
        startHosp_data = data.get("startHospital")
        endHosp_data = data.get("endHospital")
        startHospital = hospital_coords_dict.get(startHosp_data, {}).get("address")
        endHospital = hospital_coords_dict.get(endHosp_data, {}).get("address")

        if startHospital is None:
            raise ValueError(f"Invalid startHospital key: {startHosp_data}")
        if endHospital is None:
            raise ValueError(f"Invalid startHospital key: {endHosp_data}")
  
        # check if matchId exists first 
        print("Invoking match atomic service...")
        match_url = f"{MATCH_URL}/{matchId}"
        match_result = invoke_http(match_url, method="GET")
        message = json.dumps(match_result)
        code = match_result["code"]

        if code not in range(200, 300):
            return jsonify({
                "code": code,
                "data": {"matchId": matchId},
                "message": match_result["message"]
            }), code 
        else:
            try:
                order_payload = {
                    "orderId": orderId,
                    "organType": data.get("organType"),
                    "doctorId" : data.get("doctorId"),
                    "transplantDateTime": data.get("transplantDateTime"), # UTC
                    "startHospital": startHospital,
                    "endHospital": endHospital,
                    "matchId": matchId,
                    "remarks": data.get("remarks", "")
                }
                print("Invoking order atomic service...")
                order_resp = invoke_http(ORDER_URL, method="POST", json=order_payload)
                message = json.dumps(order_resp)
                code = order_resp["code"]

                if code not in range(200, 300):
                    return jsonify({
                        "code": code,
                        "data": {"matchId": matchId},
                        "message": order_resp["message"]
                    }), code 

            except Exception as e:
                raise Exception("Error invoking Order Service") from e

            print("Publishing message with routing_key=", "order.organ")
            # Prepare the message as a JSON string
            message_body = json.dumps({"orderId": orderId})
            channel.basic_publish(
                exchange="order_exchange",
                routing_key="order.organ",
                body=message_body,
                properties=pika.BasicProperties(delivery_mode=2)  # make message persistent
            )
            print("Publishing message with routing_key=", "order.info")
            # Prepare the message as a JSON string
            message_body = json.dumps({"orderId": orderId})
            channel.basic_publish(
                exchange="activity_log_exchange",
                routing_key="order.info",
                body=message_body,
                properties=pika.BasicProperties(delivery_mode=2)  # make message persistent
            )
            # Return a response immediately
            return jsonify({
                "code": 202,
                "message": "Match Confirmed. Scheduling Delivery Now."
            }), 202

    except Exception as e:
        print("Error confirming match:", str(e))
        channel.basic_publish(
            exchange="error_handling_exchange",
            routing_key="order.error",
            body=e,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        return jsonify({
            "code": 500,
            "message": "An error occurred while confirming the match: " + str(e)
        }), 500


if __name__ == "__main__":
    print("This is flask " + os.path.basename(__file__) + " for matching an organ...")
    # Run the asynchronous AMQP consumer in a separate daemon thread.
    consumer_thread = threading.Thread(target=run_async_consumer, daemon=True)
    consumer_thread.start()

    # Now run the Flask server in the main thread.
    app.run(host="0.0.0.0", port=5020, debug=True)