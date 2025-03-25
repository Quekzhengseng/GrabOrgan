import os
import json
import uuid
from flask import Flask, request, jsonify
from common import amqp_lib  # Reusable AMQP functions
from common.invokes import invoke_http  # Import the invoke_http function

app = Flask(__name__)

rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
rabbitmq_port = int(os.getenv("RABBITMQ_PORT", "5672"))
exchange_name = os.getenv("RABBITMQ_EXCHANGE", "request_organ_exchange")
routing_key = os.getenv("RABBITMQ_ROUTING_KEY", "match.request")
PERSONAL_DATA_URL = os.getenv("PERSONAL_DATA_URL", "http://personalData:5011/person")
PSEUDONYM_URL = os.getenv("PSEUDONYM_URL", "http://pseudonym:5012/pseudonymise")
RECIPIENT_URL = os.getenv("RECIPIENT_URL", "http://recipient:5013/recipient")
LAB_REPORT_URL = os.getenv("LAB_REPORT_URL", "http://labInfo:5007/lab-reports")

connection = None 
channel = None

@app.route("/", methods=['GET'])
def health_check():
    return jsonify({"code": 200, "status": "ok"}), 200

def connectAMQP():
    global connection, channel
    print("Connecting to AMQP broker...")
    try:
        connection, channel = amqp_lib.connect(
            hostname=rabbitmq_host,
            port=rabbitmq_port,
            exchange_name=exchange_name,
            exchange_type="direct",
        )
    except Exception as e:
        print(f"Unable to connect to RabbitMQ: {e}")
        exit(1)

def remove_code_field(response):
    """Helper to remove the 'code' field from a response dictionary."""
    if isinstance(response, dict) and "code" in response:
         del response["code"]
    return response

@app.route('/request-for-organ', methods=['POST'])
def request_for_organ():
    payload = request.get_json() or {}
    data = payload.get("data", {})
    recipient_data = data.get("recipient", {})
    lab_info_data = data.get("labInfo", {})

    # Generate a unique ID for this request.
    new_uuid = str(uuid.uuid4())

    # Send all recipient fields to the pseudonym service (plus generated recipientId)
    pseudonym_payload = {
        new_uuid: { **recipient_data, "personId": new_uuid }
    }

    responses = {}

    # Call the Pseudonym Service.
    pseudonym_resp = invoke_http(PSEUDONYM_URL, method="POST", json=pseudonym_payload)
    code = pseudonym_resp["code"]
    pseudonym_data = pseudonym_resp["data"]
    message = json.dumps(pseudonym_resp)

    if code not in range(200, 300):
        print("Publishing message with routing key =", "request_pseudo.error")
        channel.basic_publish(exchange="error_handling_exchange", routing_key="request_pseudo.error", body=message)
        return jsonify({"code": 500, "message": pseudonym_resp["message"]}), 500

    pseudonym_resp = remove_code_field(pseudonym_resp)
    responses["pseudonym"] = pseudonym_data

    # Extract the full masked record for our recipient from the pseudonym response.
    masked_data = pseudonym_data.get("maskedData", {}).get(new_uuid, {})
    if not masked_data:
        return jsonify({"error": "Pseudonym service did not return masked data"}), 500

    # Build the Personal Data payload using only the key personal fields.
    personal_data_from_ps = pseudonym_data.get("personalData", {})
    if not personal_data_from_ps:
        return jsonify({"error": "Pseudonym service did not return personalData"}), 500

    personal_payload = {
        "personId": new_uuid,
        "firstName": personal_data_from_ps.get("firstName"),
        "lastName": personal_data_from_ps.get("lastName"),
        "dateOfBirth": personal_data_from_ps.get("dateOfBirth"),
        "nric": personal_data_from_ps.get("nric"),
        "email": personal_data_from_ps.get("email"),
        "address": personal_data_from_ps.get("address"),
        "nokContact": personal_data_from_ps.get("nokContact")
    }

    # Use the complete masked data as the payload for the Recipient service.
    recipient_payload = { **masked_data, "recipientId": new_uuid }

    # Prepare Lab Report Service payload.
    lab_payload = lab_info_data.copy()
    lab_payload["uuid"] = new_uuid

    # Call the Personal Data Service internally (its response is not exposed to the client).
    _ = invoke_http(PERSONAL_DATA_URL, method="POST", json=personal_payload)
    code = _["code"]
    message = json.dumps(_["message"])

    if code not in range(200, 300):
        print("Publishing message with routing key =", "request_personalData.error")
        channel.basic_publish(exchange="error_handling_exchange", routing_key="request_pseudo.error", body=message)
        return jsonify({"code": 500, "data": {"personal_data_result": pseudonym_resp}, "message": "Error handling Personal Data."}), 500
    
    print("Publishing message with routing key =", "stored_personal_data.info")
    channel.basic_publish(exchange="activity_log_exchange", routing_key="stored_personal_data.info", body=message)
    # Call the Recipient Service.
    recipient_resp = invoke_http(RECIPIENT_URL, method="POST", json=recipient_payload)
    code = recipient_resp["code"]
    message = json.dumps(recipient_resp)

    if code not in range(200, 300):
        print("Publishing message with routing key =", "request_recipient.error")
        channel.basic_publish(exchange="error_handling_exchange", routing_key="request_recipient.error", body=message)
        return jsonify({"code": 500, "data": {"recipient_result": recipient_resp}, "message": "Error handling recipient."}), 500

    recipient_resp = remove_code_field(recipient_resp)
    responses["recipient"] = recipient_resp

    # Call the Lab Report Service.
    lab_resp = invoke_http(LAB_REPORT_URL, method="POST", json=lab_payload)
    code = lab_resp["code"]
    message = json.dumps(lab_resp)

    if code not in range(200, 300):
        print("Publishing message with routing key =", "request_lab.error")
        channel.basic_publish(exchange="error_handling_exchange", routing_key="request_lab.error", body=message)
        return jsonify({"code": 500, "data": {"lab_result": lab_resp}, "message": "Error handling Lab Info."}), 500
    
    lab_resp = remove_code_field(lab_resp)
    responses["lab_report"] = lab_resp

    # Publish composite payload for activity logging.
    composite_for_logging = {}
    composite_for_logging.update(recipient_data)
    composite_for_logging.update(lab_info_data)
    composite_for_logging["recipientId"] = new_uuid
    message = json.dumps({"recipientId": composite_for_logging["recipientId"]})
    try:
        print("Publishing message with routing key =", routing_key)
        channel.basic_publish(exchange=exchange_name, routing_key=routing_key, body=message)
        print("Publishing message with routing key =", "request_organ.info")
        channel.basic_publish(exchange="activity_log_exchange", routing_key="request_organ.info", body=message)
       
    except Exception as e:
        return jsonify({"error": "Error publishing message to RabbitMQ", "details": str(e)}), 500

    responses["message"] = "Composite request processed successfully."
    return jsonify(responses), 201

if __name__ == '__main__':
    connectAMQP()
    app.run(host='0.0.0.0', port=5021, debug=True)
