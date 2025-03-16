#!/usr/bin/env python3
import json
import os
from common import amqp_lib
import pika  # or your preferred AMQP library

# Retrieve connection parameters from the environment if available.
rabbit_host = os.getenv("RABBIT_HOST", "rabbitmq")  # Use "rabbitmq" when dockerised
rabbit_port = int(os.getenv("RABBIT_PORT", 5672))
queue_name = "activity_log_queue"
exchange_type = "topic"
exchange_name = "activity_log_exchange"



def callback(channel, method, properties, body):
     # required signature for the callback; no return
    """Handles incoming messages from RabbitMQ."""
    try:
        log_entry = json.loads(body)
        print(f"Received Log Entry: {log_entry}")
    except json.JSONDecodeError:
        print(f"Unable to parse JSON: {body}")
    
    print()
    channel.basic_ack(delivery_tag=method.delivery_tag)  # Ensure message is acknowledged

def start_consuming():
    """Connects to RabbitMQ, declares the exchange and queue, binds them, and starts consuming messages."""
    # Establish connection using pika
    parameters = pika.ConnectionParameters(host=rabbit_host, port=rabbit_port)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # (Re)declare the exchange (idempotent operation)
    channel.exchange_declare(
        exchange=exchange_name,
        exchange_type=exchange_type,
        durable=True  # ensures the exchange survives a RabbitMQ restart
    )

    # (Re)declare the queue (idempotent operation)
    channel.queue_declare(
        queue=queue_name,
        durable=True  # ensures the queue survives a RabbitMQ restart
    )

    # Bind the queue to the exchange.
    channel.queue_bind(
        queue=queue_name,
        exchange=exchange_name
    )

    print(f"Consuming from queue: {queue_name}")
    # Set up the consumer with the callback function.
    channel.basic_consume(queue=queue_name, on_message_callback=callback)

    # Start consuming (this call is blocking)
    channel.start_consuming()

if __name__ == "__main__":
    print(f"This is {os.path.basename(__file__)} - amqp consumer (Activity_Log)...")
    try:
        amqp_lib.start_consuming(
            rabbit_host, rabbit_port, exchange_name, exchange_type ,queue_name, callback
        )
    except Exception as exception:
        print(f"  Unable to connect to RabbitMQ.\n     {exception=}\n")
