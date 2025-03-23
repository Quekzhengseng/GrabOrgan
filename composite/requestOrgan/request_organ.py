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
      3. Generates a single UUID to be used for the Recipient, Personal Data, Lab Report, and Pseudonym services.
      4. Builds payloads for each atomic service.
      5. Publishes a composite payload to RabbitMQ for activity logging.
      6. Returns a consolidated JSON response including the responses from each service.
    """
    payload = request.get_json() or {}
    data = payload.get("data", {})
    recipient_data = data.get("recipient", {})
    lab_info_data = data.get("labInfo", {})

    # Transform recipient data.
    transformed_recipient = transform_recipient(recipient_data)
    new_uuid = str(uuid.uuid4())
    transformed_recipient["recipientId"] = new_uuid

    # Prepare Recipient Service payload.
    recipient_payload = transformed_recipient.copy()

    # Prepare Personal Data Service payload.
    personal_payload = {
        "personId": new_uuid,
        "firstName": transformed_recipient.get("firstName"),
        "lastName": transformed_recipient.get("lastName"),
        "dateOfBirth": transformed_recipient.get("dateOfBirth"),
        "nokContact": transformed_recipient.get("nokContact")
    }

    # Prepare Lab Report Service payload.
    lab_payload = lab_info_data.copy()
    lab_payload["uuid"] = new_uuid

    # Prepare Pseudonym Service payload.
    pseudonym_payload = {
        new_uuid: {
            "recipientId": new_uuid,
            "firstName": transformed_recipient.get("firstName"),
            "lastName": transformed_recipient.get("lastName"),
            "dateOfBirth": transformed_recipient.get("dateOfBirth"),
            "nokContact": transformed_recipient.get("nokContact")
        }
    }

    # Call the Pseudonym Service.
    try:
        pseudonym_resp = requests.post(PSEUDONYM_URL, json=pseudonym_payload)
        print("Pseudonym Service:", pseudonym_resp.status_code, pseudonym_resp.text)
        pseudonym_result = safe_json_response(pseudonym_resp)
    except Exception as e:
        return jsonify({"error": "Error calling Pseudonym service", "details": str(e)}), 500

    responses = {}

    # Call the Personal Data Service.
    try:
        personal_resp = requests.post(PERSONAL_DATA_URL, json=personal_payload)
        print("Personal Data Service:", personal_resp.status_code, personal_resp.text)
        responses["personal_data"] = safe_json_response(personal_resp)
    except Exception as e:
        return jsonify({"error": "Error calling Personal Data service", "details": str(e)}), 500

    # Call the Recipient Service.
    try:
        recipient_resp = requests.post(RECIPIENT_URL, json=recipient_payload)
        print("Recipient Service:", recipient_resp.status_code, recipient_resp.text)
        responses["recipient"] = safe_json_response(recipient_resp)
    except Exception as e:
        return jsonify({"error": "Error calling Recipient service", "details": str(e)}), 500

    # Add the generated UUID as "recipient_id" in the recipient response.
    if "recipient" in responses and "data" in responses["recipient"]:
        responses["recipient"]["data"]["recipient_id"] = new_uuid

    # Call the Lab Report Service.
    try:
        lab_resp = requests.post(LAB_REPORT_URL, json=lab_payload)
        print("Lab Report Service:", lab_resp.status_code, lab_resp.text)
        responses["lab_report"] = safe_json_response(lab_resp)
    except Exception as e:
        return jsonify({"error": "Error calling Lab Report service", "details": str(e)}), 500

    # Include pseudonym service result.
    responses["pseudonym"] = pseudonym_result

    # Prepare a composite payload for activity logging.
    composite_for_logging = {}
    composite_for_logging.update(transformed_recipient)
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
