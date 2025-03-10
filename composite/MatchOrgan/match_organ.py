from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import pika
import sys, os

import amqp_lib
from invokes import invoke_http

app = Flask(__name__)

CORS(app)

# order_URL = "http://order:5001/order" # if dockerised
order_URL = "http://localhost:5001/order" #localhost if not dockerised
# shipping_record_URL = "http://shipping_record:5002/shipping_record" # if dockerised
shipping_record_URL = "http://localhost:5002/shipping_record" # if localhost

# RabbitMQ
rabbit_host = "rabbitmq" #localhost if not dockerised
rabbit_port = 5672


EXCHANGES = {
    "request_organ_exchange": "direct",  # Listen for incoming organ requests
    "test_compatibility_exchange": "direct",  # Publish test requests
    "match_test_result_exchange": "direct",  # Listen for test results
    "match_result_exchange": "direct",  # Publish final match results
}

SUBSCRIBE_QUEUES = [
    {"name": "match_request_queue", "exchange": "request_organ_exchange", "routing_key": "match.request" },
    {"name": "test_result_queue", "exchange": "test_result_exchange", "routing_key": "test.result" },
]



connection = None 
channel = None

def connectAMQP():
    # Use global variables to reduce number of reconnection to RabbitMQ
    # There are better ways but this suffices for our lab
    global connection
    global channel

    print("  Connecting to AMQP broker...")
    try:
        for exchange_name, exchange_type in EXCHANGES.items():
            connection, channel = amqp_lib.connect(
                    hostname=rabbit_host,
                    port=rabbit_port,
                    exchange_name=exchange_name,
                    exchange_type=exchange_type,
            )
    except Exception as exception:
        print(f"  Unable to connect to RabbitMQ.\n     {exception=}\n")
        exit(1) # terminate

def publishMessage(exchange_name, routing_key, message_body, status_code):
     
     if status_code not in range(200, 300):
        # Inform the error microservice
        print("  Publish message with routing_key={routing_key}\n")
        channel.basic_publish(
                exchange=exchange_name,
                # routing_key="order.error",
                routing_key=routing_key,
                body=message_body,
                properties=pika.BasicProperties(delivery_mode=2),
        )


# Execute this program if it is run as a main script (not by 'import')
if __name__ == "__main__":
    print("This is flask " + os.path.basename(__file__) + " for matching an organ...")
    connectAMQP()
    app.run(host="0.0.0.0", port=5011, debug=True)