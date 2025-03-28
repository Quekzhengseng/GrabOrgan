import os
import json
import uuid
from flask import Flask, request, jsonify
from common import amqp_lib  # Reusable AMQP functions
from common.invokes import invoke_http  # Import the invoke_http function
from flask_cors import CORS
import pika
import random

app = Flask(__name__)
CORS(app)

rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
rabbitmq_port = int(os.getenv("RABBITMQ_PORT", "5672"))
exchange_name = os.getenv("RABBITMQ_EXCHANGE", "request_organ_exchange")
routing_key = os.getenv("RABBITMQ_ROUTING_KEY", "match.request")
PERSONAL_DATA_URL = os.getenv("PERSONAL_DATA_URL", "http://personalData:5011/person")
PSEUDONYM_URL = os.getenv("PSEUDONYM_URL", "http://pseudonym:5012/pseudonymise")
RECIPIENT_URL = os.getenv("RECIPIENT_URL", "http://recipient:5013/recipient")
LAB_REPORT_URL = os.getenv("LAB_REPORT_URL", "http://labInfo:5007/lab-reports")
LAB_REPORT_URL = os.getenv("LAB_REPORT_URL", "http://labInfo:5007/lab-reports")
OUTSYSTEMS_PERSONAL_DATA_URL = os.getenv("OUTSYSTEMS_PERSONAL_DATA_URL", "https://personal-gbst4bsa.outsystemscloud.com/PatientAPI/rest/patientAPI/patients/")

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

def generate_hla_profile():
    # Simulate two alleles for each of the 3 key loci
    hla_options = {
    "A": ["A1", "A2", "A3", "A11", "A24", "A26"],
    "B": ["B7", "B8", "B27", "B35", "B44", "B51"],
    "DR": ["DR1", "DR3", "DR4", "DR7", "DR11", "DR15"]
}
    profile = {}
    for locus, alleles in hla_options.items():
        profile[locus] = random.sample(alleles, 2)
    return profile # output: {'A': ['A24', 'A3'], 'B': ['B7', 'B27'], 'DR': ['DR11', 'DR1']}

@app.route('/request-for-organ', methods=['POST'])
def request_for_organ():
    # Set a default for payload in case request.get_json() fails.
    payload = {}
    try:
        payload = request.get_json() or {}
        data = payload.get("data", {})
        recipient_data = data.get("recipient", {})
        lab_info_data = data.get("labInfo", {})

        # Generate a unique ID for this request.
        new_uuid = str(uuid.uuid4())

        # Prepare payload for the pseudonym service.
        pseudonym_payload = {
            new_uuid: {**recipient_data, "uuid": new_uuid}
        }
        responses = {}

        # --- Call the Pseudonym Service ---
        pseudonym_resp = invoke_http(PSEUDONYM_URL, method="POST", json=pseudonym_payload)
        code = pseudonym_resp.get("code", 500)
        pseudonym_data = pseudonym_resp.get("data", {})
        message = json.dumps(pseudonym_resp)

        if code not in range(200, 300):
            print("Publishing message with routing key =", "request_pseudo.error")
            channel.basic_publish(
                exchange="error_handling_exchange",
                routing_key="request_pseudo.error",
                body=message,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            return jsonify({
                "code": 500,
                "message": pseudonym_resp.get("message", "Error from pseudonym service")
            }), 500

        # Remove the code field from the pseudonym response.
        pseudonym_resp = remove_code_field(pseudonym_resp)
        responses["pseudonym"] = pseudonym_data

        # --- Extract Masked Data ---
        masked_data = pseudonym_data.get("maskedData", {}).get(new_uuid, {})
        if not masked_data:
            err_msg = "Pseudonym service did not return masked data"
            print(err_msg)
            channel.basic_publish(
                exchange="error_handling_exchange",
                routing_key="request_pseudo.error",
                body=err_msg,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            return jsonify({"error": err_msg}), 500

        # --- Build Personal Data Payload ---
        personal_data_from_ps = pseudonym_data.get("personalData", {})
        if not personal_data_from_ps:
            err_msg = "Pseudonym service did not return personalData"
            print(err_msg)
            channel.basic_publish(
                exchange="error_handling_exchange",
                routing_key="request_pseudo.error",
                body=err_msg,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            return jsonify({"error": err_msg}), 500

        personal_payload = {
            "uuid": new_uuid,
            "firstName": personal_data_from_ps.get("firstName"),
            "lastName": personal_data_from_ps.get("lastName"),
            "dateOfBirth": personal_data_from_ps.get("dateOfBirth"),
            "nric": personal_data_from_ps.get("nric"),
            "email": personal_data_from_ps.get("email"),
            "address": personal_data_from_ps.get("address"),
            "nokContact": personal_data_from_ps.get("nokContact")
        }

        # --- Build Recipient and Lab Payloads ---
        recipient_payload = {**masked_data, "recipientId": new_uuid}
        lab_payload = lab_info_data.copy()
        lab_payload["uuid"] = new_uuid
        lab_payload["hlaTyping"] = generate_hla_profile()

        # --- Call the Personal Data Service ---
        personal_resp = invoke_http(PERSONAL_DATA_URL, method="POST", json=personal_payload) # as a backup for now
        os_personal_resp = invoke_http(OUTSYSTEMS_PERSONAL_DATA_URL, method="POST", json=personal_payload)
        code = os_personal_resp.get("code", 500)
        message = json.dumps(os_personal_resp.get("message", ""))
        if code not in range(200, 300):
            print("Publishing message with routing key =", "request_personalData.error")
            channel.basic_publish(
                exchange="error_handling_exchange",
                routing_key="request_personalData.error",
                body=message,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            return jsonify({
                "code": 500,
                "data": {"personal_data_result": pseudonym_resp},
                "message": "Error handling Personal Data."
            }), 500

        print("Publishing message with routing key =", "stored_personal_data.info")
        channel.basic_publish(
            exchange="activity_log_exchange",
            routing_key="stored_personal_data.info",
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )

        # --- Call the Recipient Service ---
        recipient_resp = invoke_http(RECIPIENT_URL, method="POST", json=recipient_payload)
        code = recipient_resp.get("code", 500)
        message = json.dumps(recipient_resp)
        if code not in range(200, 300):
            print("Publishing message with routing key =", "request_recipient.error")
            channel.basic_publish(
                exchange="error_handling_exchange",
                routing_key="request_recipient.error",
                body=message,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            return jsonify({
                "code": 500,
                "data": {"recipient_result": recipient_resp},
                "message": "Error handling recipient."
            }), 500

        recipient_resp = remove_code_field(recipient_resp)
        responses["recipient"] = recipient_resp

        # --- Call the Lab Report Service ---
        lab_resp = invoke_http(LAB_REPORT_URL, method="POST", json=lab_payload)
        code = lab_resp.get("code", 500)
        message = json.dumps(lab_resp)
        
        if code not in range(200, 300):
            print("Publishing message with routing key =", "request_lab.error")
            channel.basic_publish(
                exchange="error_handling_exchange",
                routing_key="request_lab.error",
                body=message,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            return jsonify({
                "code": 500,
                "data": {"lab_result": lab_resp},
                "message": "Error handling Lab Info."
            }), 500

        lab_resp = remove_code_field(lab_resp)
        responses["lab_report"] = lab_resp

        # --- Publish Composite Payload for Activity Logging ---
        composite_for_logging = {}
        composite_for_logging.update(recipient_data)
        composite_for_logging.update(lab_info_data)
        composite_for_logging["recipientId"] = new_uuid
        message = json.dumps({"recipientId": composite_for_logging["recipientId"]})
        
        print("Publishing message with routing key =", routing_key)
        channel.basic_publish(
            exchange=exchange_name, 
            routing_key=routing_key, 
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        print("Publishing message with routing key =", "request_organ.info")
        channel.basic_publish(
            exchange="activity_log_exchange",
            routing_key="request_organ.info",
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )

        responses["message"] = "Composite request processed successfully."
        return jsonify(responses), 201

    except Exception as e:
        error_message = str(e)
        print("Error in request_for_organ:", error_message)
        error_payload = json.dumps({
            "error": error_message,
            "payload": payload
        })
        try:
            channel.basic_publish(
                exchange="error_handling_exchange",
                routing_key="request_organ.exception",
                body=error_payload,
                properties=pika.BasicProperties(delivery_mode=2)
            )
        except Exception as publish_exception:
            print("Failed to publish error message:", str(publish_exception))
        return jsonify({"code": 500, "message": "Error processing organ request."}), 500

if __name__ == '__main__':
    connectAMQP()
    app.run(host='0.0.0.0', port=5021, debug=True)
