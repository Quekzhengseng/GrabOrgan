#!/usr/bin/env python3

"""
A standalone script to create multiple exchanges and queues on RabbitMQ.
"""

import pika

# RabbitMQ connection details
amqp_host = "localhost"
amqp_port = 5672

# Define exchanges and their types
EXCHANGES = {
    "request_organ_exchange": "direct",
    "match_organ_exchange": "direct",
    "test_compatibility_exchange": "direct",
    "test_result_exchange": "direct",
    "activity_log_exchange": "topic",
    "error_handling_exchange": "topic",
}

# Define queues and their respective exchange bindings
QUEUES = [
    {"name": "match_request_queue", "exchange": "request_organ_exchange", "routing_key": "match.request"},
    {"name": "test_compatibility_queue", "exchange": "test_compatibility_exchange", "routing_key": "test.compatibility"},
    {"name": "test_result_queue", "exchange": "test_result_exchange", "routing_key": "test.result"},
    {"name": "activity_log_queue", "exchange": "activity_log_exchange", "routing_key": "#"},  # Topic exchange wildcard
    {"name": "error_queue", "exchange": "error_handling_exchange", "routing_key": "*.error"},  # Topic exchange pattern
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
    setup_amqp()