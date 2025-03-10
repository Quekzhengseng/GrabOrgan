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
recipient_URL = "http://localhost:5001/recipient" #localhost if not dockerised
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
    """Establish a connection to RabbitMQ and start consuming messages."""
    global connection, channel

    print("  Connecting to AMQP broker...")
    try:
        # Establish a single connection and channel
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbit_host, port=rabbit_port, heartbeat=300, blocked_connection_timeout=300)
        )
        channel = connection.channel()

        # Subscribe to queues (declaration already done in setup script)
        for queue in SUBSCRIBE_QUEUES:
            print(f"  Subscribing to queue: {queue['name']}")
            channel.basic_consume(queue=queue["name"], on_message_callback=handle_message, auto_ack=True)

        print("✅ AMQP Connection Established & Listening for Messages!")

    except Exception as e:
        print(f"❌ Unable to connect to RabbitMQ: {e}")
        exit(1)  # Terminate on failure

# def publish_message(exchange_name, routing_key, message_body, status_code, result):
     
#      if status_code not in range(200, 300):
#         # Inform the error microservice
#         print("Publish message with routing_key={routing_key}\n")
#         channel.basic_publish(
#                 exchange=exchange_name,
#                 # routing_key="order.error",
#                 routing_key=routing_key,
#                 body=message_body,
#                 properties=pika.BasicProperties(delivery_mode=2),
#         )
#         # 7. Return error
#         return {
#             "code": 500,
#             "data": {"result": result},
#             "message": "Faild to Get Recipients sent for error handling.",
#         }
def handle_message(ch, method, properties, body):
    """Callback function to process incoming messages."""
    print(f"📩 Received message from {method.routing_key}: {body.decode()}")

    if method.routing_key == "match.request":
        match_request = process_match_request(body.decode())
        publish_message("test_compatibility_exchange", "test.compatibility", match_request)

    # Example: If this is a test result, send a final match result
    # if method.routing_key == "test.result":
    #     match_result = process_test_result(body.decode())  # Custom logic
    #     publish_message("match_result_exchange", "match.result", match_result)

def start_consuming():
    """Start consuming messages from subscribed queues."""
    if channel:
        print("📡 Waiting for messages...")
        channel.start_consuming()
    else:
        print("❌ Error: AMQP channel not available.")


def process_match_request(match_request):
    if connection is None or not amqp_lib.is_connection_open(connection):
        connectAMQP()
    
    # 2. Get specific recipient from DB
    # Invoke the order microservice
    print("Invoking recipient microservice...")
    recipient_result = invoke_http(recipient_URL, method="GET", json=match_request) # need to see what match_request decodes to
    print(f"  recipient_result: { recipient_result}\n")

    message = json.dumps(recipient_result)

    # Check the order result; if a failure, send it to the error microservice.
    code = recipient_result["code"]
    # publish_message("test_compatibility_exchange","test.compatibility",message, code)

    if code not in range(200, 300):
        # Inform the error microservice
        print("  Publish message with routing_key=match_request.error\n")
        channel.basic_publish(
                exchange="match.request",
                routing_key="match_request.error",
                body=message,
                properties=pika.BasicProperties(delivery_mode=2),
        )
        # make message persistent within the matching queues until it is received by some receiver
        # (the matching queues have to exist and be durable and bound to the exchange)

        # 7. Return error
        return {
            "code": 500,
            "data": {"recipient_result": recipient_result},
            "message": "Faild to Get Recipients sent for error handling.",
        }



# Execute this program if it is run as a main script (not by 'import')
if __name__ == "__main__":
    print("This is flask " + os.path.basename(__file__) + " for matching an organ...")
    connectAMQP()
    app.run(host="0.0.0.0", port=5011, debug=True)