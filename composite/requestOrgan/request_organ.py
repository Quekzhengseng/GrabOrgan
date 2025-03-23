import os
import json
import uuid
import requests
import pika
import uuid
from flask import Flask, request, jsonify
from common import amqp_lib  # Assumes your reusable AMQP functions are here
from common.invokes import invoke_http

app = Flask(__name__)

rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
rabbitmq_port = int(os.getenv("RABBITMQ_PORT", "5672"))
exchange = os.getenv("RABBITMQ_EXCHANGE", "request_organ_exchange")
routing_key = os.getenv("RABBITMQ_ROUTING_KEY", "recipient.registered")
PERSONAL_DATA_URL = os.getenv("PERSONAL_DATA_URL", "http://personalData:5011/person")
PSEUDONYM_URL = os.getenv("PSEUDONYM_URL", "http://pseudonym:5012/pseudonymise")
RECIPIENT_URL = os.getenv("RECIPIENT_URL", "http://recipient:5013/recipient")
LAB_REPORT_URL = os.getenv("LAB_REPORT_URL", "http://labInfo:5007/lab-reports")

connection = None 
channel = None

def connectAMQP():
    # Use global variables to reduce number of reconnection to RabbitMQ
    # There are better ways but this suffices for our lab
    global connection
    global channel

    print("  Connecting to AMQP broker...")
    try:
        connection, channel = amqp_lib.connect(
                hostname=rabbitmq_host,
                port=rabbitmq_port,
                exchange_name=exchange_name,
                exchange_type="direct",
        )
    except Exception as exception:
        print(f"  Unable to connect to RabbitMQ.\n     {exception=}\n")
        exit(1) # terminate


def safe_json_response(resp):
    try:
        return resp.json()
    except Exception:
        print("Failed to parse JSON from response:", resp.text)
        return {"error": "Invalid JSON", "raw": resp.text}


def transform_recipient(recipient):
    """
    Transform recipient keys from snake_case to camelCase.
    Mapping:
      first_name   -> firstName
      last_name    -> lastName
      date_of_birth -> dateOfBirth
      blood_type   -> bloodType
      organs_needed -> organsNeeded
      medical_history -> medicalHistory
      nok_contact  -> nokContact
      gender       -> gender
      allergies    -> allergies
    """
    mapping = {
        "first_name": "firstName",
        "last_name": "lastName",
        "date_of_birth": "dateOfBirth",
        "blood_type": "bloodType",
        "organs_needed": "organsNeeded",
        "medical_history": "medicalHistory",
        "nok_contact": "nokContact",
        "gender": "gender",
        "allergies": "allergies"
    }
    transformed = {}
    for key, value in recipient.items():
        new_key = mapping.get(key, key)
        transformed[new_key] = value
    return transformed


@app.route('/request_for_organ', methods=['POST'])
def request_for_organ():
    """
    Composite service workflow:
      1. Receives a JSON payload with structure:
         {
           "data": {
             "recipient": { ... snake_case fields ... },
             "labInfo": { ... already in camelCase ... }
           }
         }
      2. Transforms recipient data from snake_case to camelCase.
      3. Generates a single UUID to be used for the recipient, personal data, lab report, and pseudonym.
      4. Builds a pseudonym payload and sends it to the Pseudonym service.
      5. Prepares payloads for the Personal Data, Recipient, and Lab Report services.
      6. Publishes a composite payload to RabbitMQ for logging.
      7. Returns a consolidated JSON response including the pseudonym service result.
    """
    payload = request.get_json() or {}
    data = payload.get("data", {})
    recipient_data = data.get("recipient", {})
    lab_info_data = data.get("labInfo", {})

    # Transform recipient data from snake_case to camelCase
    transformed_recipient = transform_recipient(recipient_data)
    new_uuid = str(uuid.uuid4())
    transformed_recipient["recipientId"] = new_uuid

    # Build pseudonym payload (only includes fields needed for pseudonymisation)
    pseudonym_payload = {
        new_uuid: {
            "recipientId": new_uuid,
            "firstName": transformed_recipient.get("firstName"),
            "lastName": transformed_recipient.get("lastName"),
            "dateOfBirth": transformed_recipient.get("dateOfBirth"),
            "nokContact": transformed_recipient.get("nokContact")
        }
    }

    # Call the Pseudonym service and capture its result
    try:
        pseudonym_resp = requests.post(PSEUDONYM_URL, json=pseudonym_payload)
        print("Pseudonym Service:", pseudonym_resp.status_code, pseudonym_resp.text)
        pseudonym_result = safe_json_response(pseudonym_resp)
    except Exception as e:
        return jsonify({"error": "Error calling Pseudonym service", "details": str(e)}), 500

    # Prepare payloads for downstream services using the same UUID
    personal_payload = {
        "personId": new_uuid,
        "firstName": transformed_recipient.get("firstName"),
        "lastName": transformed_recipient.get("lastName"),
        "dateOfBirth": transformed_recipient.get("dateOfBirth"),
        "nokContact": transformed_recipient.get("nokContact")
    }
    recipient_payload = transformed_recipient

    # Ensure the lab report payload includes the UUID
    lab_payload = lab_info_data.copy()
    lab_payload["uuid"] = new_uuid

    responses = {}

    # Forward data to Personal Data Service
    try:
        personal_resp = requests.post(PERSONAL_DATA_URL, json=personal_payload)
        print("Personal Data Service:", personal_resp.status_code, personal_resp.text)
        responses["personal_data"] = safe_json_response(personal_resp)
    except Exception as e:
        return jsonify({"error": "Error calling Personal Data service", "details": str(e)}), 500

    # Forward data to Recipient Service
    try:
        recipient_resp = requests.post(RECIPIENT_URL, json=recipient_payload)
        print("Recipient Service:", recipient_resp.status_code, recipient_resp.text)
        responses["recipient"] = safe_json_response(recipient_resp)
    except Exception as e:
        return jsonify({"error": "Error calling Recipient service", "details": str(e)}), 500

    # Forward data to Lab Report Service
    try:
        lab_resp = requests.post(LAB_REPORT_URL, json=lab_payload)
        print("Lab Report Service:", lab_resp.status_code, lab_resp.text)
        responses["lab_report"] = safe_json_response(lab_resp)
    except Exception as e:
        return jsonify({"error": "Error calling Lab Report service", "details": str(e)}), 500

    # Include pseudonym service result in the final response
    responses["pseudonym"] = pseudonym_result

    # Prepare a flattened composite payload for activity logging
    composite_for_logging = {}
    composite_for_logging.update(transformed_recipient)
    composite_for_logging.update(lab_info_data)
    composite_for_logging["recipientId"] = new_uuid

    # Publish event to RabbitMQ for activity logging
    try:
        channel.basic_publish(
            exchange=exchange_name,
            routing_key=routing_key,
            body=json.dumps(composite_for_logging)
        )
        connection.close()
    except Exception as e:
        return jsonify({"error": "Error publishing message to RabbitMQ", "details": str(e)}), 500

    responses["message"] = "Request processed and activity logged."
    return jsonify(responses), 201


if __name__ == '__main__':
    connectAMQP()
    app.run(host='0.0.0.0', port=5021, debug=True)
