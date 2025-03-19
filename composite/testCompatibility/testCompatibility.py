from flask import Flask, jsonify
import pika
import json
import requests
import os
import threading
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# RabbitMQ Connection Details
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")

# RabbitMQ Exchange & Routing Keys
TEST_COMPATIBILITY_EXCHANGE = "test_compatibility_exchange"
MATCH_TEST_RESULT_EXCHANGE = "match_test_result_exchange"
TEST_COMPATIBILITY_ROUTING_KEY = "test.compatibility"
MATCH_TEST_RESULT_ROUTING_KEY = "test.result"

# Lab Info & Match Atomic Service URLs
LAB_INFO_URL = os.getenv("LAB_INFO_URL", "http://lab-info-service:5007/lab-reports")
MATCH_SERVICE_URL = os.getenv("MATCH_SERVICE_URL", "http://match-service:5008/matches")

def connect_rabbitmq():
    """Connect to RabbitMQ and declare the exchange."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.exchange_declare(exchange=TEST_COMPATIBILITY_EXCHANGE, exchange_type="direct", durable=True)
    channel.exchange_declare(exchange=MATCH_TEST_RESULT_EXCHANGE, exchange_type="direct", durable=True)
    return connection, channel

@app.route("/")
def health_check():
    """Health check endpoint."""
    return jsonify({"code": 200, "message": "Test Compatibility Service Running"}), 200

def fetch_lab_info(uuid):
    """Fetch donor's lab report from Lab Info Atomic using UUID."""
    try:
        response = requests.get(f"{LAB_INFO_URL}/{uuid}")
        if response.status_code == 200:
            lab_data = response.json().get("data", {})

            # ✅ Extract relevant matching fields from results
            results = lab_data.get("results", {})
            return {
                "uuid": uuid,
                "tissueType": results.get("tissueType", ""),
                "antibodyScreen": results.get("antibodyScreen", ""),
                "crossMatch": results.get("crossMatch", ""),
                "organ_donated": lab_data.get("organ_donated", "")
            }
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
    """Fetch recipient's lab report from Firestore using UUID."""
    try:
        doc_ref = db.collection("matches").where("recipientId", "==", recipient_uuid).get()
        if doc_ref:
            recipient_data = doc_ref[0].to_dict()
            results = recipient_data.get("results", {})
            return {
                "uuid": recipient_uuid,
                "tissueType": results.get("tissueType", ""),
                "organ_needed": recipient_data.get("organ_needed", "")
            }
        else:
            print(f"⚠️ No recipient data found in Firestore for {recipient_uuid}")
            return None
    except Exception as e:
        print(f"❌ Error fetching recipient lab report: {str(e)}")
        return None

def process_message(body):
    """Process an organ matching request from RabbitMQ."""
    data = json.loads(body)
    recipient_uuid = data.get("recipientId")
    organ_uuids = data.get("listOfOrganId")  # ✅ Expecting UUIDs for donor organs

    if not organ_uuids:
        print("⚠️ No organs specified in request.")
        return {"listOfMatchId": []}

    matched_ids = []

    # Fetch recipient's lab report from Firestore
    recipient_data = fetch_recipient_lab_report(recipient_uuid)
    if not recipient_data:
        return {"listOfMatchId": []}

    recipient_tissue_type = recipient_data.get("tissueType", "")
    recipient_organ_type = recipient_data.get("organ_needed")

    for organ_uuid in organ_uuids:
        donor_data = fetch_lab_info(organ_uuid)  # ✅ Now using UUID to fetch Lab Info
        if not donor_data:
            continue  # Skip if donor data is missing

        donor_tissue_type = donor_data.get("tissueType", "")
        donor_organ_type = donor_data.get("organ_donated")

        # ✅ Organ Type Must Match
        if recipient_organ_type != donor_organ_type:
            print(f"⚠️ Organ type mismatch: {recipient_organ_type} vs {donor_organ_type}")
            continue

        # ✅ Check Tissue Type Compatibility
        if recipient_tissue_type != donor_tissue_type:
            print(f"⚠️ Tissue type mismatch: {recipient_tissue_type} vs {donor_tissue_type}")
            continue

        # ✅ Use correct matchId format: <UUID>-<OrganType>-<RecipientUUID>
        match_id = f"{organ_uuid}-{donor_organ_type}-{recipient_uuid}"
        matched_ids.append(match_id)

    # ✅ Post Matches to Match Service (HTTP)
    if matched_ids:
        post_matches_to_match_service(matched_ids)

    return {"listOfMatchId": matched_ids}

def post_matches_to_match_service(matched_ids):
    """POST valid matches to Match Atomic Service (HTTP)."""
    match_payload = {"matches": [{"matchId": match_id} for match_id in matched_ids]}

    try:
        response = requests.post(MATCH_SERVICE_URL, json=match_payload)
        if response.status_code == 201:
            print(f"✅ Matches posted successfully to Match Service: {matched_ids}")
        else:
            print(f"⚠️ Failed to post matches. Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error posting matches: {str(e)}")

def callback(ch, method, properties, body):
    """RabbitMQ message consumer callback."""
    print("📩 Received Organ Matching Request")
    response = process_message(body)

    # ✅ Publish results to matchOrgan
    print("📬 Sending results to MatchOrgan...")
    channel.basic_publish(
        exchange=MATCH_TEST_RESULT_EXCHANGE,
        routing_key=MATCH_TEST_RESULT_ROUTING_KEY,
        body=json.dumps(response),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    print(f"✅ Match results sent: {response}")

def start_rabbitmq_listener():
    """Start RabbitMQ listener in a separate thread."""
    connection, channel = connect_rabbitmq()
    channel.queue_declare(queue="test_compatibility_queue", durable=True)
    channel.queue_bind(
        exchange=TEST_COMPATIBILITY_EXCHANGE, queue="test_compatibility_queue", routing_key=TEST_COMPATIBILITY_ROUTING_KEY
    )

    print("🐇 Listening for messages on test_compatibility_queue...")
    channel.basic_consume(queue="test_compatibility_queue", on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

# Run RabbitMQ listener in a background thread
threading.Thread(target=start_rabbitmq_listener, daemon=True).start()

# Start Flask on port 5022
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5022, debug=True)