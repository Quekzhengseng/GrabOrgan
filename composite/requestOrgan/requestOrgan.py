import os
import json
import requests
import pika
from flask import Flask, request, jsonify

app = Flask(__name__)

def safe_json_response(resp):
    """
    Attempts to decode a JSON response.
    If decoding fails, logs the raw response text and returns an error dict.
    """
    try:
        return resp.json()
    except Exception:
        print("Failed to parse JSON from response:", resp.text)
        return {"error": "Invalid JSON", "raw": resp.text}

def extract_recipient_data(data):
    """
    Extracts only the fields needed by the Recipient service.
    We use "recipientId" as the unique identifier.
    """
    payload = {"recipientId": data.get("recipientId")}
    keys = [
        "firstName", "lastName", "dateOfBirth", "gender",
        "bloodType", "organsNeeded", "medicalHistory", "allergies", "nokContact"
    ]
    for key in keys:
        if key in data:
            payload[key] = data.get(key)
    return payload

def extract_lab_report_data(data):
    """Extracts only the fields needed by the Lab Report service."""
    keys = ["reportName", "testType", "dateOfReport", "reportUrl", "results", "uuid"]
    return {key: data.get(key) for key in keys if key in data}

def extract_personal_data(data):
    """
    Extracts only the fields needed by the Personal Data service.
    Since personId and recipientId are the same, we use "recipientId" as the unique identifier.
    """
    recipient_id = data.get("recipientId")
    payload = {"personId": recipient_id}
    keys = ["firstName", "lastName", "dateOfBirth", "nokContact"]
    for key in keys:
        if key in data:
            payload[key] = data.get(key)
    return payload

@app.route('/request_for_organ', methods=['POST'])
def request_for_organ():
    """
    Composite service that:
      1. Receives a JSON payload.
      2. Splits the composite payload into only the required fields for:
         - Personal Data Service
         - Pseudonym Service
         - Recipient Service
         - Lab Report Service
      3. Publishes the original data to RabbitMQ for logging.
      4. Returns a consolidated JSON response.
    """
    composite_data = request.get_json() or {}
    responses = {}

    # Extract minimal payloads for each atomic service
    recipient_payload = extract_recipient_data(composite_data)
    lab_payload = extract_lab_report_data(composite_data)
    personal_payload = extract_personal_data(composite_data)
    
    # For the pseudonym service, wrap the personal data keyed by recipientId.
    record_id = composite_data.get("recipientId", "unknown")
    pseudonym_payload = { record_id: personal_payload }

    try:
        # Forward to Personal Data Service
        personal_url = os.getenv("PERSONAL_DATA_URL", "http://personal_data_service:5011/person")
        personal_resp = requests.post(personal_url, json=personal_payload)
        print("Personal Service:", personal_resp.status_code, personal_resp.text)
        responses["personal_data"] = safe_json_response(personal_resp)

        # Forward to Pseudonym Service
        pseudonym_url = os.getenv("PSEUDONYM_URL", "http://pseudonym_service:5012/pseudonymise")
        pseudonym_resp = requests.post(pseudonym_url, json=pseudonym_payload)
        print("Pseudonym Service:", pseudonym_resp.status_code, pseudonym_resp.text)
        responses["pseudonym"] = safe_json_response(pseudonym_resp)

        # Forward to Recipient Service
        recipient_url = os.getenv("RECIPIENT_URL", "http://recipient_service:5013/recipient")
        recipient_resp = requests.post(recipient_url, json=recipient_payload)
        print("Recipient Service:", recipient_resp.status_code, recipient_resp.text)
        responses["recipient"] = safe_json_response(recipient_resp)

        # Forward to Lab Report Service
        lab_url = os.getenv("LAB_REPORT_URL", "http://lab_report_service:5007/lab-reports")
        lab_resp = requests.post(lab_url, json=lab_payload)
        print("Lab Report Service:", lab_resp.status_code, lab_resp.text)
        responses["lab_report"] = safe_json_response(lab_resp)

    except Exception as e:
        return jsonify({
            "error": "Error calling atomic microservices",
            "details": str(e)
        }), 500

    # Publish event to RabbitMQ for activity logging
    try:
        rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
        rabbitmq_port = int(os.getenv("RABBITMQ_PORT", "5672"))
        exchange = os.getenv("RABBITMQ_EXCHANGE", "request_organ_exchange")
        routing_key = os.getenv("RABBITMQ_ROUTING_KEY", "match.request")
        
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port)
        )
        channel = connection.channel()
        channel.exchange_declare(exchange=exchange, exchange_type='topic', durable=True)
        channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(composite_data)
        )
        connection.close()
    except Exception as e:
        return jsonify({
            "error": "Error publishing message to RabbitMQ",
            "details": str(e)
        }), 500

    responses["message"] = "Request processed and activity logged."
    return jsonify(responses), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5021, debug=True)
