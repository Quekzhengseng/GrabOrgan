#!/usr/bin/env python3

"""
A standalone script to create multiple exchanges and queues on RabbitMQ.
"""

import pika
from os import environ

# RabbitMQ connection details
amqp_host = environ.get("rabbitmq_host") or "localhost"
# amqp_host = "rabbitmq"
amqp_port = environ.get("rabbitmq_port") or 5672

# Define exchanges and their types
EXCHANGES = {
    "request_organ_exchange": "direct",
    "test_compatibility_exchange": "direct",
    "test_result_exchange": "direct",
    "activity_log_exchange": "topic",
    "error_handling_exchange": "topic",
    "confirm_match_exchange": "direct",
    "notification_status_exchange": "topic",
    "notification_acknowledge_exchange": "topic",
    "driver_match_exchange": "direct",
}

# Define queues and their respective exchange bindings
QUEUES = [
    {"name": "match_request_queue", "exchange": "request_organ_exchange", "routing_key": "match.request"},
    {"name": "test_compatibility_queue", "exchange": "test_compatibility_exchange", "routing_key": "test.compatibility"},
    {"name": "match_test_result_queue", "exchange": "test_result_exchange", "routing_key": "test.result"},
    {"name": "confirm_match_queue", "exchange": "confirm_match_exchange", "routing_key": "match.confirm"},
    {"name": "activity_log_queue", "exchange": "activity_log_exchange", "routing_key": "*.info"},  # Topic exchange wildcard
    {"name": "error_queue", "exchange": "error_handling_exchange", "routing_key": "*.error"},  # Topic exchange pattern
     {"name": "noti_delivery_status_queue", "exchange": "notification_status_exchange", "routing_key": "*.status", "type": "topic"},
    {"name": "noti_acknowledgement_queue","exchange":"notification_acknowledge_exchange", "routing_key": "*.acknowledge", "type": "topic"},
    {"name": "driver_match_request_queue", "exchange": "driver_match_exchange", "routing_key": "driver.request", "type": "direct"},
]


def create_exchange(channel, exchange_name, exchange_type):
    """Create an exchange if it does not exist."""
    print(f"Declaring exchange: {exchange_name} ({exchange_type})")
    channel.exchange_declare(exchange=exchange_name, exchange_type=exchange_type, durable=True)


def create_queue(channel, queue_name, exchange_name, routing_key):
    """Create a queue and bind it to an exchange."""
    print(f"Creating queue: {queue_name}")
    channel.queue_declare(queue=queue_name, durable=True)
    print(f"Binding queue: {queue_name} to exchange: {exchange_name} with routing key: {routing_key}")
    channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)


def setup_amqp():
    """Setup AMQP exchanges and queues."""
    print(f"Connecting to AMQP broker at {amqp_host}:{amqp_port}...")
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=amqp_host, port=amqp_port, heartbeat=300, blocked_connection_timeout=300)
    )
    print("Connected")

    print("Open channel")
    channel = connection.channel()

    # Create exchanges
    for exchange_name, exchange_type in EXCHANGES.items():
        create_exchange(channel, exchange_name, exchange_type)

    # Create queues and bind them to exchanges
    for queue in QUEUES:
        create_queue(channel, queue["name"], queue["exchange"], queue["routing_key"])

    print("✅ AMQP Setup Complete!")
    connection.close()


if __name__ == "__main__":
    print("Setting up AMQP...")
    setup_amqp()