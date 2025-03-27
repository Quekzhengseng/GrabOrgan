#!/usr/bin/env python3
from os import environ
import json
import os
from common.invokes import invoke_http
import pika  # or your preferred AMQP library
import ast
import threading
import time
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
# Retrieve connection parameters from the environment if available.
rabbit_host = environ.get("rabbit_host") or "localhost"
rabbit_port = int(environ.get("rabbit_port")) or 5672
EMAIL_SUBDOMAIN = environ.get("email_subdomain") or 'DoNotReply@c4de2af4-af42-4134-8003-492f444c8562.azurecomm.net'
AZURE_EMAIL_URL = environ.get("AZURE_EMAIL_URL") or "http://localhost:5014/email"

SUBSCRIBE_QUEUES = [
    {"name": "noti_delivery_status_queue", "exchange": "notification_status_exchange", "routing_key": "*.status", "type": "topic"},
    {"name": "noti_acknowledgement_queue","exchange":"notification_acknowledge_exchange", "routing_key": "*.acknowledge", "type": "topic"},
]
MAX_RETRIES = 3
# Global channel for publishing messages (set when the channel opens)
channel = None

def handle_message(ch, method, properties, body):
    try:
        message_dict = ast.literal_eval(body.decode())
        print(f"Received message from {method.routing_key}: {message_dict}")
        parts = method.routing_key.split(".")
        # Simulate processing
        if len(parts) == 2 and parts[1] == "status":            
            print("Processing status request with routing_key: ", method.routing_key)
            process_delivery_status(message_dict, method.routing_key)
        elif len(parts) == 2 and parts[1] == "acknowledge":
            print("Processing acknowledgement request...")
            process_acknowledgment_request(message_dict, method.routing_key)
        else:
            print("Unknown routing key.")
       # Acknowledge the message after successful processing.
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    except Exception as e:
        print(f"Error while handling message: {e}")
        
        # Retrieve current retry count from headers, defaulting to 0 if not present.
        retry_count = 0
        if properties.headers and 'x-retry-count' in properties.headers:
            retry_count = properties.headers['x-retry-count']
        print(f"Current retry count: {retry_count}")

        if retry_count < MAX_RETRIES:
            # Increase the retry count.
            new_retry_count = retry_count + 1

            # Create new properties with the updated retry count.
            new_properties = pika.BasicProperties(
                headers={"x-retry-count": new_retry_count},
                delivery_mode=properties.delivery_mode  # Preserve persistence if set.
            )

            # Republish the message with the updated headers.
            print(f"Republishing message, retry attempt {new_retry_count}")
            ch.basic_publish(
                exchange=method.exchange,
                routing_key=method.routing_key,
                body=body,
                properties=new_properties
            )
            # Acknowledge the current message so it is removed from the queue.
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            print("Max retries reached. Discarding message or sending to dead-letter queue.")
            # Here you could also publish the message to a dead-letter queue instead.
            ch.basic_ack(delivery_tag=method.delivery_tag)

def on_channel_open(ch):
    """Callback when the channel has been opened; set up consumers for all queues."""
    global channel
    channel = ch  # Save channel for later publishing
    print("Channel opened, setting up consumers...")
    for queue in SUBSCRIBE_QUEUES:
        print(f"Subscribing to queue: {queue['name']}")
        ch.basic_consume(
            queue=queue["name"],
            on_message_callback=handle_message,
            auto_ack=False
        )
    print("Consumers are set up. Waiting for messages...")

def on_connection_open(conn):
    """Callback when the connection is opened; create a channel."""
    print("Connection opened")
    conn.channel(on_open_callback=on_channel_open)

def on_connection_closed(conn, reply_code, reply_text=None):
    """Callback when the connection is closed."""
    print(f"Connection closed: reply_code={reply_code}, reply_text={reply_text}")
    conn.ioloop.stop()

def run_async_consumer():
    """Set up the asynchronous connection and start the IOLoop with a retry loop."""
    parameters = pika.ConnectionParameters(
        host=rabbit_host,
        port=rabbit_port,
        heartbeat=300,
        blocked_connection_timeout=300
    )
    while True:
        try:
            print(f"Attempting to connect to RabbitMQ at {rabbit_host}:{rabbit_port} ...")
            conn = pika.SelectConnection(
                parameters=parameters,
                on_open_callback=on_connection_open,
                on_close_callback=on_connection_closed
            )
            print("Starting IOLoop")
            conn.ioloop.start()
            break  # Exit the loop if the connection and loop run normally
        except pika.exceptions.AMQPConnectionError as e:
            print(f"AMQPConnectionError: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"Unexpected error: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def ensure_exchange_exists(channel, exchange, exchange_type):
    # Declare the exchange (it will only create it if it does not already exist)
    channel.exchange_declare(exchange=exchange, exchange_type=exchange_type, durable=True)

def delivery_status_email(status):
    """
    Returns a tuple of (plain_text, html_text)
    incorporating the delivery status into the email body.
    """
    plain_text = f"Hello there! Your GrabOrgan delivery status is: {status}."
    html_text = f"""
    <html>
      <body>
        <h1>Hello there!</h1>
        <p>Your GrabOrgan delivery status is: <strong>{status}</strong></p>
      </body>
    </html>
    """
    return plain_text, html_text
def request_acknowledgement_email():
    """
    Returns a tuple of (plain_text, html_text)
    incorporating the delivery status into the email body.
    """
    plain_text = f"Hello there! Your acknowledgement is required on GrabOrgan"
    html_text = f"""
    <html>
      <body>
        <h1>Hello there!</h1>
        <p>Your <strong>acknowledgement</strong> is required on GrabOrgan</p>
      </body>
    </html>
    """
    return plain_text, html_text

def create_email_message(driver_email, subject, plain_text, html_text):
    # Build the final email message dictionary.
    email_message = {
        "senderAddress": EMAIL_SUBDOMAIN,
        "recipients": {
            "to": [{"address": driver_email}]
        },
        "content": {
            "subject": subject,
            "plainText": plain_text,
            "html": html_text
        }
    }
    return email_message

def process_delivery_status(message_dict, routing_key):
    """
    Process delivery status and send an email notification.

    routing_key: a string indicating the status, e.g.:
      - searching.status
      - assigned.status 
      - on_the_way.status   (driver started delivery)
      - halfway.status 
      - close_by.status      (driver is 80% there)
      - arrived.status
      - completed.status     (delivery completed/acknowledged)

    amqp message example:
    {
        "driverId": "driver123",
        "email": "example@gmail.com"
    }
    """
    try:
        # Extract information from the message
        driver_id = message_dict.get("driverId", "Driver")
        driver_email = message_dict.get("email")

        # Build email subject and body based on routing_key
        subject_prefix = "Delivery Status Update: "
        subject_status_dict = {
            "searching": "Searching for Driver",
            "assigned": "Driver Assigned",
            "on_the_way": "Driver On The Way",
            "halfway": "Driver Halfway",
            "close_by": "Driver Close By",
            "arrived": "Driver Has Arrived",
            "completed": "Delivery Completed",
        }

        # Get the status (before .status) from the routing key.
        status_key = routing_key.split(".")[0]
        subject = subject_prefix + subject_status_dict.get(status_key, "Status Updated")

            # Generate email body using our helper function.
        if status_key in subject_status_dict:
            plain_text, html_text = delivery_status_email(subject_status_dict[status_key])
        else:
            plain_text, html_text = delivery_status_email("Status Updated")
        
        email_message = create_email_message(driver_email, subject, plain_text, html_text)
        print("Sending Email with status: " + routing_key)
        email_resp = invoke_http(AZURE_EMAIL_URL, method="POST",json=email_message)
        json_resp = json.dumps(email_resp)
        code = email_resp["code"]

        if code not in range(200,300):
            print("Email sending failed with code:", code)
            channel.basic_publish(
                exchange="error_handling_exchange",
                routing_key="email.error",
                body=json_resp,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            return jsonify({"code": code, "message": email_resp["message"]}), code
        
        print("Publishing message to with routing_key: ", "status.info")
        channel.basic_publish(
                exchange="activity_log_exchange",
                routing_key="delivery_status.info",
                body=json_resp,
                properties=pika.BasicProperties(delivery_mode=2)  # make message persistent
            )
    except Exception as e:
        print("Exception in process_delivery_status:", str(e))
        error_payload = json.dumps({
            "error": str(e),
            "routing_key": routing_key,
            "message_dict": message_dict
        })
        channel.basic_publish(
            exchange="error_handling_exchange",
            routing_key="delivery_status.error",
            body=error_payload,
            properties=pika.BasicProperties(delivery_mode=2)
        )


def process_acknowledgment_request(message_dict, routing_key):
    """
    Process an acknowledgement message and send an email notification.

    routing_key: a string indicating the status, e.g.:
      - request.acknowledge
      - completed.acknowledge

    amqp message example:
    {
        "driverId": "driver123",
        "email": "example@gmail.com"
    }
    """
    try:
        subject_prefix = "Acknowledgement Required: "
        status_key = routing_key.split(".")[0]

        # Extract information from the message
        driver_id = message_dict.get("driverId", "Driver")
        driver_email = message_dict.get("email")

        subject_dict = {
            "request": "Delivery Assigned",
            "completed": "Delivery Completed",

        }

        if status_key in subject_dict:
            subject = subject_prefix + subject_dict[status_key]
            plain_text, html_text = request_acknowledgement_email()
            email_message = create_email_message(driver_email, subject, plain_text, html_text)
            print("Sending Email with status: " + routing_key)
            email_resp = invoke_http(AZURE_EMAIL_URL, "POST", json=email_message)
            json_resp = json.dumps(email_resp)
            code = email_resp["code"]

            if code not in range(200,300):
                print("Email sending failed with code:", code)
                channel.basic_publish(
                    exchange="error_handling_exchange",
                    routing_key="email.error",
                    body=json_resp,
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                return jsonify({"code": code, "message": email_resp["message"]}), code
            
            print("Publishing message to with routing_key: ", "acknowledge.info")
            channel.basic_publish(
                    exchange="activity_log_exchange",
                    routing_key="acknowledge.info",
                    body=json_resp,
                    properties=pika.BasicProperties(delivery_mode=2)  # make message persistent
                )
            
        else:
            print("Publishing message to with routing_key: ", routing_key) # publish any unknown keys to the error log
            channel.basic_publish(
                exchange="error_handling_exchange",
                routing_key="email.error",
                body=message_dict,
                properties=pika.BasicProperties(delivery_mode=2)  # make message persistent
            )
    except Exception as e:
        print("Exception in process_acknowledgment_request:", str(e))
        error_payload = json.dumps({
            "error": str(e),
            "routing_key": routing_key,
            "message_dict": message_dict
        })
        channel.basic_publish(
            exchange="error_handling_exchange",
            routing_key="acknowledge.error",
            body=error_payload,
            properties=pika.BasicProperties(delivery_mode=2)
        )


if __name__ == "__main__":
    print(f"This is {os.path.basename(__file__)} - Send Notification service...")
    consumer_thread = threading.Thread(target=run_async_consumer, daemon=True)
    consumer_thread.start()

    # Now run the Flask server in the main thread.
    app.run(host="0.0.0.0", port=5027, debug=True)