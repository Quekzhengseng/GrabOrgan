import os
import json
import uuid
import requests
import pika
from flask import Flask, request, jsonify

app = Flask(__name__)

rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
rabbitmq_port = int(os.getenv("RABBITMQ_PORT", "5672"))
exchange = os.getenv("RABBITMQ_EXCHANGE", "request_organ_exchange")
routing_key = os.getenv("RABBITMQ_ROUTING_KEY", "recipient.registered")
PERSONAL_DATA_URL = os.getenv("PERSONAL_DATA_URL", "http://personalData:5011/person")
PSEUDONYM_URL = os.getenv("PSEUDONYM_URL", "http://pseudonym:5012/pseudonymise")
RECIPIENT_URL = os.getenv("RECIPIENT_URL", "http://recipient:5013/recipient")
LAB_REPORT_URL = os.getenv("LAB_REPORT_URL", "http://labInfo:5007/lab-reports")

def safe_json_response(resp):
    try:
        return resp.json()
    except Exception:
        print("Failed to parse JSON from response:", resp.text)
        return {"error": "Invalid JSON", "raw": resp.text}

@app.route('/request_for_organ', methods=['POST'])
def request_for_organ():
    """
    Composite service workflow:
      1. Receives a JSON payload with structure:
         {
           "data": {
             "recipient": { ... already in camelCase ... },
             "labInfo": { ... already in camelCase ... }
           }
         }
      2. Generates a single UUID to be used for all atomic services.
      3. Builds payloads for each service:
            - Recipient service: expects "recipientId"
            - Personal Data service: expects "personId"
            - Lab Report service: expects "uuid"
            - Pseudonym service: expects inner "recipientId"
      4. Calls each service and publishes an activity log.
      5. Returns a consolidated JSON response.
    """
    payload = request.get_json() or {}
    data = payload.get("data", {})
    recipient_data = data.get("recipient", {})
    lab_info_data = data.get("labInfo", {})

    # Use input data that is already in camelCase.
    new_uuid = str(uuid.uuid4())

    # Prepare Recipient Service payload.
    recipient_payload = recipient_data.copy()
    recipient_payload["recipientId"] = new_uuid

    # Prepare Personal Data Service payload.
    personal_payload = {
        "personId": new_uuid,
        "firstName": recipient_data.get("firstName"),
        "lastName": recipient_data.get("lastName"),
        "dateOfBirth": recipient_data.get("dateOfBirth"),
        "nokContact": recipient_data.get("nokContact")
    }

    # Prepare Lab Report Service payload.
    lab_payload = lab_info_data.copy()
    lab_payload["uuid"] = new_uuid

    # Prepare Pseudonym Service payload.
    pseudonym_payload = {
        new_uuid: {
            "recipientId": new_uuid,
            "firstName": recipient_data.get("firstName"),
            "lastName": recipient_data.get("lastName"),
            "dateOfBirth": recipient_data.get("dateOfBirth"),
            "nokContact": recipient_data.get("nokContact")
        }
    }

    responses = {}

    # Call the Pseudonym Service.
    try:
        pseudonym_resp = requests.post(PSEUDONYM_URL, json=pseudonym_payload)
        print("Pseudonym Service:", pseudonym_resp.status_code, pseudonym_resp.text)
        responses["pseudonym"] = safe_json_response(pseudonym_resp)
    except Exception as e:
        return jsonify({"error": "Error calling Pseudonym service", "details": str(e)}), 500

    # Call the Personal Data Service.
    try:
        personal_resp = requests.post(PERSONAL_DATA_URL, json=personal_payload)
        print("Personal Data Service:", personal_resp.status_code, personal_resp.text)
        responses["personal_data"] = safe_json_response(personal_resp)
        # Inject the personId into the personal data response.
        if "data" in responses["personal_data"]:
            responses["personal_data"]["data"]["personId"] = new_uuid
    except Exception as e:
        return jsonify({"error": "Error calling Personal Data service", "details": str(e)}), 500

    # Call the Recipient Service.
    try:
        recipient_resp = requests.post(RECIPIENT_URL, json=recipient_payload)
        print("Recipient Service:", recipient_resp.status_code, recipient_resp.text)
        responses["recipient"] = safe_json_response(recipient_resp)
        # Add the generated UUID as "recipient_id" into the recipient response.
        if "data" in responses["recipient"]:
            responses["recipient"]["data"]["recipient_id"] = new_uuid
    except Exception as e:
        return jsonify({"error": "Error calling Recipient service", "details": str(e)}), 500

    # Call the Lab Report Service.
    try:
        lab_resp = requests.post(LAB_REPORT_URL, json=lab_payload)
        print("Lab Report Service:", lab_resp.status_code, lab_resp.text)
        responses["lab_report"] = safe_json_response(lab_resp)
    except Exception as e:
        return jsonify({"error": "Error calling Lab Report service", "details": str(e)}), 500

    # Publish a composite payload for activity logging.
    composite_for_logging = {}
    composite_for_logging.update(recipient_data)
    composite_for_logging.update(lab_info_data)
    composite_for_logging["recipientId"] = new_uuid

    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port))
        channel = connection.channel()
        channel.exchange_declare(exchange=exchange, exchange_type='direct', durable=True)
        channel.basic_publish(exchange=exchange, routing_key=routing_key, body=json.dumps(composite_for_logging))
        connection.close()
        responses["activity_log"] = {"code": 200, "message": "Activity logged successfully."}
    except Exception as e:
        return jsonify({"error": "Error publishing message to RabbitMQ", "details": str(e)}), 500

    responses["message"] = "Composite request processed successfully."
    return jsonify(responses), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5021, debug=True)
