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

@app.route('/request_for_organ', methods=['POST'])
def request_for_organ():
    """
    Composite service that:
      1. Receives a JSON payload.
      2. Forwards the data to:
         - Personal Data Service
         - Pseudonym Service
         - Recipient Service
         - Lab Report Service
      3. Publishes the original data to RabbitMQ for activity logging.
      4. Returns a consolidated JSON response.
    """
    data = request.get_json() or {}
    responses = {}

    try:
        # Forward to Personal Data Service
        personal_url = os.getenv("PERSONAL_DATA_URL", "http://personal_data_service:5011/person")
        personal_resp = requests.post(personal_url, json=data)
        print("Personal Service:", personal_resp.status_code, personal_resp.text)
        responses["personal_data"] = safe_json_response(personal_resp)

        # Forward to Pseudonym Service
        pseudonym_url = os.getenv("PSEUDONYM_URL", "http://pseudonym_service:5012/pseudonymise")
        pseudonym_resp = requests.post(pseudonym_url, json=data)
        print("Pseudonym Service:", pseudonym_resp.status_code, pseudonym_resp.text)
        responses["pseudonym"] = safe_json_response(pseudonym_resp)

        # Forward to Recipient Service
        recipient_url = os.getenv("RECIPIENT_URL", "http://recipient_service:5013/recipient")
        recipient_resp = requests.post(recipient_url, json=data)
        print("Recipient Service:", recipient_resp.status_code, recipient_resp.text)
        responses["recipient"] = safe_json_response(recipient_resp)

        # Forward to Lab Report Service
        lab_url = os.getenv("LAB_REPORT_URL", "http://lab_report_service:5007/lab-reports")
        lab_resp = requests.post(lab_url, json=data)
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
        exchange = os.getenv("RABBITMQ_EXCHANGE", "order_topic")
        routing_key = os.getenv("RABBITMQ_ROUTING_KEY", "recipient.registered")
        
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port)
        )
        channel = connection.channel()
        channel.exchange_declare(exchange=exchange, exchange_type='topic', durable=True)
        channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(data)
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
