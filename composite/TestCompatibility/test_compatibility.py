from flask import Flask, jsonify
import pika
import json
import requests
import os
import threading
from datetime import datetime
import sys

app = Flask(__name__)

# RabbitMQ Connection Details
rabbit_host= os.getenv("rabbit_host", "localhost")

# RabbitMQ Exchange & Routing Keys
TEST_COMPATIBILITY_EXCHANGE = "test_compatibility_exchange"
MATCH_TEST_RESULT_EXCHANGE = "match_test_result_exchange"
TEST_COMPATIBILITY_ROUTING_KEY = "test.compatibility"
MATCH_TEST_RESULT_ROUTING_KEY = "test.result"

# Lab Info & Match Atomic Service URLs
LAB_INFO_URL = os.getenv("LAB_INFO_URL", "http://localhost:5007/lab-reports")
MATCH_SERVICE_URL = os.getenv("MATCH_SERVICE_URL", "http://localhost:5008/matches")

def connect_rabbitmq():
    print(f"🔌 Trying to connect to RabbitMQ at host '{rabbit_host}'...")
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(rabbit_host))
        channel = connection.channel()
        channel.exchange_declare(exchange=TEST_COMPATIBILITY_EXCHANGE, exchange_type="direct", durable=True)
        channel.exchange_declare(exchange=MATCH_TEST_RESULT_EXCHANGE, exchange_type="direct", durable=True)
        print("✅ Connected to RabbitMQ and declared exchanges.")
        sys.stdout.flush()
        return connection, channel
    except Exception as e:
        print(f"❌ Failed to connect to RabbitMQ at host '{rabbit_host}': {e}")
        return None, None

@app.route("/")
def health_check():
    """Health check endpoint."""
    return jsonify({"code": 200, "message": "Test Compatibility Service Running"}), 200

def fetch_lab_info(uuid):
    """Fetch a lab report (donor or recipient) from Lab Info Atomic using UUID."""
    try:
        response = requests.get(f"{LAB_INFO_URL}/{uuid}")
        if response.status_code == 200:
            lab_data = response.json().get("data", {})
            results = lab_data.get("results", {})
            # Combine data from the report and the results map.
            lab_data.update(results)
            return lab_data
        elif response.status_code == 404:
            print(f"⚠️ Lab report for UUID {uuid} not found.")
            return None
        else:
            print(f"⚠️ Unexpected response from Lab Info Service: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching lab report: {str(e)}")
        return None

def fetch_recipient_lab_report(recipient_uuid):
    """Fetch recipient's lab report from Lab Info Atomic using UUID."""
    return fetch_lab_info(recipient_uuid)  # assuming same endpoint and format

def post_matches_to_match_service(matches):
    """POST valid matches to Match Atomic Service (HTTP)."""
    payload = {"matches": matches}
    try:
        response = requests.post(MATCH_SERVICE_URL, json=payload)
        if response.status_code == 201:
            print(f"✅ Matches posted successfully to Match Service: {json.dumps(payload)}")
        else:
            print(f"⚠️ Failed to post matches. Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error posting matches: {str(e)}")
    sys.stdout.flush()

def process_message(body):
    """Process an HLA matching request from RabbitMQ."""
    data = json.loads(body)
    recipient_uuid = data.get("recipientId")
    organ_uuids = data.get("listOfOrganId")  # Still using the same field for donor IDs

    if not organ_uuids:
        print("⚠️ No organs specified in request.")
        return {"listOfMatchId": []}

    # Fetch recipient's lab report
    recipient_data = fetch_recipient_lab_report(recipient_uuid)
    if not recipient_data:
        return {"listOfMatchId": []}

    # Get the recipient's HLA score (or default to 0 if not available)
    recipient_hla = recipient_data.get("hlaScore", 0)

    # List to hold match records (dictionaries)
    matches = []

    # Define your HLA threshold (for example, donor's HLA must be >= 4)
    HLA_THRESHOLD = 4

    for organ_uuid in organ_uuids:
        donor_data = fetch_lab_info(organ_uuid)  # Fetch donor lab report
        if not donor_data:
            continue

        # Get the donor's HLA score
        donor_hla = donor_data.get("hlaScore", 0)

        # Check HLA compatibility: here we assume donor_hla must be at least the threshold.
        if donor_hla < HLA_THRESHOLD:
            print(f"⚠️ HLA mismatch: donor HLA {donor_hla} is below threshold {HLA_THRESHOLD}")
            continue

        # Create a match id using the donor and recipient UUIDs
        match_id = f"{organ_uuid}-{recipient_uuid}"
        
        # Build a match record with HLA-based data
        match_record = {
            "OrganId": donor_data.get("uuid"),  # Here you might not need to combine with organ type
            "Test_DateTime": datetime.now().isoformat(),
            "donorId": donor_data.get("uuid"),
            "donor_details": {
                "blood_type": donor_data.get("blood_type", "B+"),
                "first_name": donor_data.get("first_name", "Chartreuse"),
                "gender": donor_data.get("gender", "Male"),
                "last_name": donor_data.get("last_name", "Lavender")
            },
            "matchId": match_id,
            "numOfHLA": donor_hla,  # This can be used to indicate the donor's HLA score
            "recipientId": recipient_uuid,
            "recipient_details": {
                "blood_type": recipient_data.get("blood_type", "AB+"),
                "first_name": recipient_data.get("first_name", "Nicholas"),
                "gender": recipient_data.get("gender", "Female"),
                "last_name": recipient_data.get("last_name", "Lam")
            }
        }
        matches.append(match_record)

    # Post valid matches if any match records were built.
    if matches:
        post_matches_to_match_service(matches)

    # Return just the list of match IDs for logging or further processing.
    matched_ids = [m["matchId"] for m in matches]
    return {"listOfMatchId": matched_ids}

def callback(ch, method, properties, body):
    """RabbitMQ message consumer callback."""
    print("📩 Received a message in callback!")
    print("Message body:", body)
    sys.stdout.flush()
    
    response = process_message(body)
    
    print("📬 Sending results to MatchOrgan...")
    ch.basic_publish(
        exchange=MATCH_TEST_RESULT_EXCHANGE,
        routing_key=MATCH_TEST_RESULT_ROUTING_KEY,
        body=json.dumps(response),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    print(f"✅ Match results sent: {response}")
    sys.stdout.flush()

def start_rabbitmq_listener():
    print("🧪 Attempting to start RabbitMQ listener...")
    try:
        connection, channel = connect_rabbitmq()
        if not connection or not channel:
            print("❌ Could not start listener due to RabbitMQ connection failure.")
            return

        channel.queue_declare(queue="test_compatibility_queue", durable=True)
        channel.queue_bind(
            exchange=TEST_COMPATIBILITY_EXCHANGE,
            queue="test_compatibility_queue",
            routing_key=TEST_COMPATIBILITY_ROUTING_KEY
        )

        print("🐇 Listening for messages on test_compatibility_queue...")
        channel.basic_consume(
            queue="test_compatibility_queue",
            on_message_callback=callback,
            auto_ack=True
        )
        channel.start_consuming()

    except Exception as e:
        print(f"❌ Unexpected error in listener thread: {e}")

# Run RabbitMQ listener in a background thread
threading.Thread(target=start_rabbitmq_listener, daemon=True).start()

# Start Flask on port 5022 with proper reloader check for debug mode
if __name__ == "__main__":
    import os
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        # Listener already started above in this process.
        pass
    app.run(host="0.0.0.0", port=5022, debug=True)