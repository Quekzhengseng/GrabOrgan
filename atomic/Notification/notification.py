#!/usr/bin/env python3
from os import environ
import json
import os
from common import amqp_lib
import pika  # or your preferred AMQP library
import ast
import threading
import time

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
            # process_match_request(message_dict)
        elif method.routing_key == "acknowledge.request":
            print("Processing acknowledge request...")
            # process_match_result(message_dict)
        else:
            print("Unknown routing key.")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error while handling message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag)

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


if __name__ == "__main__":
    print(f"This is {os.path.basename(__file__)} - amqp consumer (Notification)...")
    try:
        consumer_thread = threading.Thread(target=run_async_consumer, daemon=True)
        consumer_thread.start()
    except Exception as exception:
        print(f"  Unable to connect to RabbitMQ.\n     {exception=}\n")
