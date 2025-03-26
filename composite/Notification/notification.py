#!/usr/bin/env python3
from os import environ
import json
import os
from common import amqp_lib
import pika  # or your preferred AMQP library
import ast
import threading
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Retrieve connection parameters from the environment if available.
rabbit_host = environ.get("rabbit_host") or "localhost"
rabbit_port = int(environ.get("rabbit_port")) or 5672
exchange_name = environ.get("exchange_name") or "notification_exchange"
exchange_type = environ.get("exchange_type") or "topic"
queue_name = environ.get("queue_name") or "notification_queue"

SUBSCRIBE_QUEUES = [
    {"name": "delivery_status_queue", "exchange": "notification_exchange", "routing_key": "*.status", "type": "topic"},
    {"name": "acknowledgement_queue", "exchange": "notification_exchange", "routing_key": "acknowledge.*", "type": "topic"},
]
MAX_RETRIES = 3
# Global channel for publishing messages (set when the channel opens)
channel = None

def handle_message(ch, method, properties, body):
    try:
        print("Raw message body:", body)
        message_dict = ast.literal_eval(body.decode())
        print(f"Received message from {method.routing_key}: {message_dict}")
        
        # Simulate processing
        if method.routing_key == "*.status":
            print("Processing status request...")
            process_delivery_status(message_dict, method.routing_key)
        elif method.routing_key == "acknowledge.request":
            print("Processing acknowledge request...")
            # process_match_result(message_dict)
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
     # Extract information from the message
    driver_id = message_dict.get("driverId", "Driver")
    driver_email = message_dict.get("email")
    
    # Define SMTP server configuration (replace with your own)
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = "your_email@gmail.com"
    smtp_password = "your_email_password"  # Consider using environment variables or a secure vault

    # Build email subject and body based on routing_key
    if routing_key == "searching.status":
        subject = "Delivery Status Update: Searching for Driver"
        body = f"Dear {driver_id},\n\nWe are currently searching for a driver to handle your delivery."
    elif routing_key == "assigned.status":
        subject = "Delivery Status Update: Driver Assigned"
        body = f"Dear {driver_id},\n\nA driver has been assigned to your delivery. Please wait for further updates."
    elif routing_key == "on_the_way.status":
        subject = "Delivery Status Update: Driver On The Way"
        body = f"Dear {driver_id},\n\nYour driver has started the delivery and is on the way."
    elif routing_key == "halfway.status":
        subject = "Delivery Status Update: Driver Halfway"
        body = f"Dear {driver_id},\n\nYour driver is halfway to your destination."
    elif routing_key == "close_by.status":
        subject = "Delivery Status Update: Driver Close By"
        body = f"Dear {driver_id},\n\nYour driver is almost there (80% of the way)."
    elif routing_key == "arrived.status":
        subject = "Delivery Status Update: Driver Arrived"
        body = f"Dear {driver_id},\n\nYour driver has arrived at the destination."
    elif routing_key == "completed.status":
        subject = "Delivery Status Update: Delivery Completed"
        body = f"Dear {driver_id},\n\nYour delivery has been completed and acknowledged."
    else:
        subject = "Delivery Status Update"
        body = f"Dear {driver_id},\n\nYour delivery status has been updated."

    # Setup the MIME message
    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = driver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to the SMTP server and send the email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Upgrade the connection to secure
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"Email sent to {driver_email} with subject: {subject}")
    except Exception as e:
        print(f"Failed to send email to {driver_email}: {e}")


if __name__ == "__main__":
    print(f"This is {os.path.basename(__file__)} - amqp consumer (Notification)...")
    try:
        consumer_thread = threading.Thread(target=run_async_consumer, daemon=True)
        consumer_thread.start()
    except Exception as exception:
        print(f"  Unable to connect to RabbitMQ.\n     {exception=}\n")
