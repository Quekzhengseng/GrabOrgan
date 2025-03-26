from flask import Flask, jsonify
from flask_cors import CORS
import pika
import json
import random
from datetime import datetime
import os
from common.invokes import invoke_http
from common import amqp_lib  # Assuming your reusable AMQP functions are here

app = Flask(__name__)
CORS(app)

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
ORGAN_ATOMIC_URL = os.getenv("ORGAN_ATOMIC_URL", "http://localhost:5009/organ")

@app.route("/", methods=['GET'])
def health_check():
    return jsonify({"code": 200, "status": "ok"}), 200

# Step 1 - Receive RecipientId & List of OrganId via AMQP
def handle_message(ch, method, properties, body):
    """Callback function to process incoming messages."""
    try:
        print("Raw message body:", body)
        message_dict = json.loads(body.decode())
        print(f"Received message: {message_dict}")

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
    except Exception as e:
        print(f"Error while handling message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag)

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
    
    # Fetch recipient's lab report
    print(f"Fetching lab report for recipientId: {recipient_uuid}...")
    lab_report = get_lab_report(recipient_uuid)
    if lab_report:
        print(f"Successfully fetched lab report: {lab_report}")
    else:
        print(f"Failed to fetch lab report for recipientId: {recipient_uuid}")
        return jsonify({"code": 500, "message": "Failed to fetch lab report"}), 500

    # Generate randomized HLA matches
    matches = []
    HLA_THRESHOLD = 4
    for organ_uuid, organ_info in organ_data.items():
        donor_id = organ_info["donorId"]
        print(f"Creating match for organId: {organ_uuid} with donorId: {donor_id}")

        hla_matches = {f"HLA {i+1}": random.choice([True, False]) for i in range(6)}
        num_of_hla = sum(1 for match in hla_matches.values() if match)

        if num_of_hla >= HLA_THRESHOLD:
            match_id = f"{recipient_uuid}-{organ_uuid}"
            match_record = {
                "matchId": match_id,
                "recipientId": recipient_uuid,
                "donorId": donor_id,
                "OrganId": organ_uuid,
                **hla_matches,
                "numOfHLA": num_of_hla,
                "Test_DateTime": datetime.now().isoformat()
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

def get_lab_report(recipient_uuid):
    """Fetch recipient's lab report from Lab Info Atomic using UUID."""
    lab_info_url = f"{LAB_INFO_URL}/{recipient_uuid}"
    lab_result = invoke_http(lab_info_url, method="GET")
    if 'code' in lab_result and lab_result["code"] in range(200, 300):
        return lab_result
    else:
        print(f"Error fetching lab report: {lab_result.get('message', 'Unknown error')}")
        return None

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
    # Start the RabbitMQ listener in a daemon thread so it doesn't block the main thread.
    consumer_thread = threading.Thread(target=run_async_consumer, daemon=True)
    consumer_thread.start()

    # Start the Flask app in the main thread.
    app.run(host="0.0.0.0", port=5022, debug=True)
