#!/usr/bin/env python3
import os
import json
from common import amqp_lib
import pika
from os import environ

# Retrieve connection parameters from the environment if available.
rabbit_host = environ.get("rabbit_host") or "localhost"
rabbit_port = environ.get("rabbit_port") or 5672
exchange_name = environ.get("exchange_name") or "error_handling_exchange"
exchange_type = environ.get("exchange_type") or "topic"
queue_name = environ.get("queue_name") or "error_queue"

def callback(channel, method, properties, body):
    # required signature for the callback; no return
    try:
        error = json.loads(body)
        print(f"JSON: {error}")
    except Exception as e:
        print(f"Unable to parse JSON: {e=}")
        print(f"Message: {body}")
    print()
    channel.basic_ack(delivery_tag=method.delivery_tag)  # Ensure message is acknowledged

if __name__ == "__main__":
    print(f"This is {os.path.basename(__file__)} - amqp consumer (Error)...")
    try:
        amqp_lib.start_consuming(
            rabbit_host, rabbit_port, exchange_name, exchange_type ,queue_name, callback
        )
    except Exception as exception:
        print(f"  Unable to connect to RabbitMQ.\n     {exception=}\n")