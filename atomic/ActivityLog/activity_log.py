#!/usr/bin/env python3
import json
import os
from common import amqp_lib
import pika  # or your preferred AMQP library

# # # Retrieve the connection URL from the environment, with a fallback if needed.
# # amqp_url = os.environ.get("AMQP_URL", "amqp://rabbitmq:5672/")
# AMQP_URL = os.getenv("AMQP_URL", "amqp://localhost:5672/")
# # # Use amqp_url to establish the connection
# parameters = pika.URLParameters(AMQP_URL)
# connection = pika.BlockingConnection(parameters)
# channel = connection.channel()

# rabbit_host = "localhost" #localhost if not dockerised
rabbit_host = "rabbitmq" # if dockerised
rabbit_port = 5672
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


if __name__ == "__main__":
    print(f"This is {os.path.basename(__file__)} - amqp consumer (Activity_Log)...")
    try:
        amqp_lib.start_consuming(
            rabbit_host, rabbit_port, exchange_name, exchange_type ,queue_name, callback
        )
    except Exception as exception:
        print(f"  Unable to connect to RabbitMQ.\n     {exception=}\n")
