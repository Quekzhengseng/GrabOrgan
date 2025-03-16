from flask import Flask, jsonify, request
import pika
import json
import requests
import os
import threading

app = Flask(__name__)

# RabbitMQ Connection Details
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
QUEUE_NAME = "organ_matching_queue"

# API URLs
LAB_INFO_URL = "http://lab-info-service:5007/lab-reports"
MATCH_SERVICE_URL = "http://match-service:5008/matches"

# HLA Keys for Compatibility Check
HLA_KEYS = ["HLA_A_1", "HLA_A_2", "HLA_B_1", "HLA_B_2", "HLA_DR_1", "HLA_DR_2"]

def connect_rabbitmq():
    """Connect to RabbitMQ and declare the queue."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)
    return connection, channel

@app.route("/")
def health_check():
    """Health check endpoint."""
    return jsonify({"code": 200, "message": "Test Compatibility Service Running"}), 200

def fetch_lab_report(donor_id):
    """Fetch HLA markers for a donor from Lab Info Service."""
    try:
        response = requests.get(f"{LAB_INFO_URL}/{donor_id}")
        if response.status_code == 200:
            return response.json().get("data", {})
        elif response.status_code == 404:
            print(f"⚠️ Lab report for donor {donor_id} not found.")
            return None
        else:
            print(f"⚠️ Unexpected response from Lab Info Service: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching lab report: {str(e)}")
        return None

def process_message(body):
    """Process an organ matching request from RabbitMQ."""
    data = json.loads(body)
    recipient_id = data.get("RecipientId")
    organ_ids = data.get("OrganId", [])

    if not organ_ids:
        print("⚠️ No organs specified in request.")
        return

    matched_organs = []

    # Simulate recipient's HLA markers (For real implementation, fetch from a database)
    recipient_hla = {key: True for key in HLA_KEYS}  # Assume recipient has all markers True

    for donor_id in organ_ids:
        donor_data = fetch_lab_report(donor_id)
        if not donor_data:
            continue  # Skip if donor data is missing

        donor_hla = {key: donor_data.get(key, False) for key in HLA_KEYS}

        # Check HLA compatibility
        hla_matches = sum(1 for key in HLA_KEYS if recipient_hla[key] == donor_hla[key])

        if hla_matches >= 4:
            match = {
                "matchId": f"{donor_id}-{recipient_id}",
                "recipientId": recipient_id,
                "donorId": donor_id,
                "numOfHLA": hla_matches,
            }
            matched_organs.append(match)

    if matched_organs:
        # Sort matches: 6/6 first, then 5/6, then 4/6
        matched_organs.sort(key=lambda x: x["numOfHLA"], reverse=True)

        # Send matches to Match Service
        try:
            response = requests.post(MATCH_SERVICE_URL, json={"matches": matched_organs})
            response_data = response.json()

            if response.status_code == 201:
                print(f"✅ Matches posted successfully for Recipient {recipient_id}")
                return jsonify({
                    "code": 201,
                    "data": {"order_id": recipient_id},
                    "message": "Successful operation"
                }), 201
            elif response.status_code == 400:
                print(f"⚠️ Match Service returned Bad Request: {response_data}")
                return jsonify({
                    "code": 400,
                    "data": {"order_id": recipient_id},
                    "message": "Shipping record creation failure"
                }), 400
            else:
                print(f"⚠️ Unexpected response from Match Service: {response.status_code}")
                return jsonify({
                    "code": 500,
                    "message": "Invalid JSON output from Match Service."
                }), 500
        except requests.exceptions.RequestException as e:
            print(f"❌ Error posting to Match Service: {str(e)}")
            return jsonify({
                "code": 500,
                "message": f"Error connecting to Match Service: {str(e)}"
            }), 500
    else:
        print(f"❌ No valid matches for Recipient {recipient_id}")
        return jsonify({
            "code": 400,
            "data": {"order_id": recipient_id},
            "message": "No valid matches found"
        }), 400

def callback(ch, method, properties, body):
    """RabbitMQ message consumer callback."""
    print("📩 Received Organ Matching Request")
    process_message(body)

def start_rabbitmq_listener():
    """Start RabbitMQ listener in a separate thread."""
    connection, channel = connect_rabbitmq()
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)
    print("🐇 Listening for messages...")
    channel.start_consuming()

# Run RabbitMQ listener in a background thread
threading.Thread(target=start_rabbitmq_listener, daemon=True).start()

# Start Flask on port 5022
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5022, debug=True)
