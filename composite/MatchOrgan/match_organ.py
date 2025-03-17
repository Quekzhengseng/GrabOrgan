from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import pika
import sys, os
import ast
from os import environ

from common import amqp_lib
from common.invokes import invoke_http

app = Flask(__name__)

CORS(app)

# export PYTHONPATH=$PYTHONPATH:/path/to/GrabOrgan (do this in local env for "common" package)
RECIPIENT_URL = environ.get("RECIPIENT_URL") or "http://localhost:5013/recipient"
DONOR_URL = environ.get("DONOR_URL") or "http://localhost:5003/donor"
ORGAN_URL = environ.get("ORGAN_URL") or "http://localhost:5010/organ"
MATCH_URL = environ.get("MATCH_URL") or "http://localhost:5008/matches"
"""
for testing:
routing_key = match.request
amqp message:
{
"recipientId" : "5RWWwCxq2M2eoXX91Z5BBsONTLs="
}

routing_key = test.result
amqp message:
{
"listOfMatchId" : ["015051e7-0c87-4c13-9bb0-dd5e7584aabc-heart-12", "015051e7-0c87-4c13-9bb0-dd5e7584aabc-heart-29", "015051e7-0c87-4c13-9bb0-dd5e7584aabc-heart-5"]
}
"""

# RabbitMQ
# rabbit_host = "rabbitmq" # if dockerised
rabbit_host = os.environ.get("rabbit_host", "localhost")
rabbit_port = int(os.environ.get("rabbit_port", "5672"))



EXCHANGES = {
    "request_organ_exchange": "direct",  # Listen for incoming organ requests
    "test_compatibility_exchange": "direct",  # Publish test requests
    "match_test_result_exchange": "direct",  # Listen for test results
    "match_result_exchange": "direct",  # Publish final match results
}

SUBSCRIBE_QUEUES = [
    {"name": "match_request_queue", "exchange": "request_organ_exchange", "routing_key": "match.request", "type": "direct" },
    {"name": "match_test_result_queue", "exchange": "test_result_exchange", "routing_key": "test.result", "type": "direct" },
]



connection = None 
channel = None

def connectAMQP():
    """Establish a connection to RabbitMQ and start consuming messages."""
    global connection, channel

    print("Connecting to AMQP broker...")
    try:
        # Establish a single connection and channel
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbit_host, port=rabbit_port, heartbeat=300, blocked_connection_timeout=300)
        )
        channel = connection.channel()

        # Subscribe to queues (declaration already done in setup script)
        for queue in SUBSCRIBE_QUEUES:
            print(f"Subscribing to queue: {queue['name']}")
            # amqp_lib.start_consuming(rabbit_host,rabbit_port, exchange_name=queue["exchange"], queue_name=queue["name"], exchange_type=queue["type"] ,callback=handle_message)
            channel.basic_consume(queue=queue["name"], on_message_callback=handle_message, auto_ack=False)
        print("AMQP Connection Established!")
        print("Waiting for messages...")
        channel.start_consuming()

    except Exception as e:
        print(f"Unable to connect to RabbitMQ: {e}")
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
    print(f"Received message from {method.routing_key}: {body.decode()}") # debugging print statement
    decoded_msg_to_dict = ast.literal_eval(body.decode())
    # print(type(ast.literal_eval(decoded_msg)))
    if method.routing_key == "match.request":
        match_request = process_match_request(decoded_msg_to_dict)
        ch.basic_ack(delivery_tag=method.delivery_tag)  # <-- Manually acknowledge
        # publish_message("test_compatibility_exchange", "test.compatibility", match_request)
    if method.routing_key == "test.result":
        match_test_result = process_match_result(decoded_msg_to_dict)
        ch.basic_ack(delivery_tag=method.delivery_tag)  # <-- Manually acknowledge


def start_consuming():
    """Start consuming messages from subscribed queues."""
    if channel:
        print("Waiting for messages...")
        channel.start_consuming()
    else:
        print("Error: AMQP channel not available.")

def is_compatible(recipient_bloodType, donor_bloodType):
    # Blood transfusion compatibility rules
    blood_transfusion_rules = {
        "O-": {"O-"},
        "O+": {"O-", "O+"},
        "A-": {"O-", "A-"},
        "A+": {"O-", "O+", "A-", "A+"},
        "B-": {"O-", "B-"},
        "B+": {"O-", "O+", "B-", "B+"},
        "AB-": {"O-", "A-", "B-", "AB-"},
        "AB+": {"O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"}
    }
    """Checks if a donor's blood type is compatible with the recipient."""
    return donor_bloodType in blood_transfusion_rules[recipient_bloodType]

def process_match_request(match_request_dict):
    if connection is None or not amqp_lib.is_connection_open(connection):
        connectAMQP()
    
    # 2. Get specific recipient from DB
    recipient_id = match_request_dict["recipientId"]
    recipient_URL = RECIPIENT_URL +"/"+ recipient_id
    # Invoke the Recipient atomic service
    print("Invoking recipient atomic service...")
    recipient_result = invoke_http(recipient_URL, method="GET", json=match_request_dict) # need to see what match_request decodes to

    message = json.dumps(recipient_result)
    # Check the recipient result; if a failure, send it to the error microservice.
    code = recipient_result["code"]
    # publish_message("test_compatibility_exchange","test.compatibility",message, code)

    if code not in range(200, 300):
        # Inform the error microservice
        print("Publish message with routing_key=match_request.error\n")
        channel.basic_publish(
                exchange="error_handling_exchange",
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
    # print("Publish message with routing_key=\n")

    # print(f"recipient_result: {recipient_result}\n")
    recipient_data = recipient_result["data"]
    recipient_bloodType = recipient_data["bloodType"] # A-, O+ ...
    recipient_organsNeeded = recipient_data["organsNeeded"] # ["cornea", "lungs", "liver"]
    print(recipient_bloodType)
    print(recipient_organsNeeded)

    # 3. Get All Organs 
    # Invoke the Organ atomic service
    print("Invoking organ atomic service...")
    organ_result = invoke_http(ORGAN_URL, method="GET", json=match_request_dict) # need to see what match_request decodes to

    message = json.dumps(organ_result)
    # Check the recipient result; if a failure, send it to the error microservice.
    code = organ_result["code"]
    # publish_message("test_compatibility_exchange","test.compatibility",message, code)

    if code not in range(200, 300):
        # Inform the error microservice
        print("Publish message with routing_key=match_request.error\n")
        channel.basic_publish(
                exchange="error_handling_exchange",
                routing_key="match_request.error",
                body=message,
                properties=pika.BasicProperties(delivery_mode=2),
        )
        # make message persistent within the matching queues until it is received by some receiver
        # (the matching queues have to exist and be durable and bound to the exchange)

        # 7. Return error
        return {
            "code": 500,
            "data": {"organ_result": organ_result},
            "message": "Failed to Get Recipients sent for error handling.",
        }

    # print(f"organ_result: {organ_result}\n")
    organ_data = organ_result["data"]
    organList = []


    for organ in organ_data:
        if is_compatible(recipient_bloodType, organ["bloodType"]) and organ["organType"] in recipient_organsNeeded:
            organList.append(organ["organId"])

    print(f"Compatible Donor Organes: {organList}")

    message=json.dumps({
        "recipientId": recipient_id,
        "listOfOrganId" : organList
        
        })
    # if there are no compatible donors
    if len(organList) == 0:
        print("Publish message with routing_key=match_request.info\n")
        channel.basic_publish(
                exchange="activity_log_exchange",
                routing_key="match_request.info",
                body="No matches available",
                properties=pika.BasicProperties(delivery_mode=2),
        )
        # 7. Return error
        return {
            "code": 204,
            "message": "No compatible matches found.",
        }

    print("Publish message with routing_key=match_request.info\n")
    channel.basic_publish(
            exchange="activity_log_exchange",
            routing_key="match_request.info",
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),
    )
    print("Publish message with routing_key=test.compatibility\n")
    channel.basic_publish(
            exchange="test_compatibility_exchange",
            routing_key="test.compatibility",
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),
    )

def process_match_result(match_test_result_dict):
    if connection is None or not amqp_lib.is_connection_open(connection):
        connectAMQP()
    
    # Invoke the Recipient atomic service
    print("Invoking match atomic service...")
    match_result = invoke_http(MATCH_URL, method="GET", json=match_test_result_dict) # need to see what match_request decodes to

    message = json.dumps(match_result)
    # Check the recipient result; if a failure, send it to the error microservice.
    code = match_result["code"]
    # publish_message("test_compatibility_exchange","test.compatibility",message, code)

    if code not in range(200, 300):
        # Inform the error microservice
        print("Publish message with routing_key=match_test_result.error\n")
        channel.basic_publish(
                exchange="error_handling_exchange",
                routing_key="match_test_result.error.error",
                body=message,
                properties=pika.BasicProperties(delivery_mode=2),
        )
        # make message persistent within the matching queues until it is received by some receiver
        # (the matching queues have to exist and be durable and bound to the exchange)

        # 7. Return error
        return {
            "code": 500,
            "data": {"matches_result": match_result},
            "message": "Faild to Get All Matches sent for error handling.",
        }
    # print(f"match_results: {match_result["data"]}")

    match_data = match_result["data"]

    match_test_result = []

    for match in match_data:
        if match["matchId"] in match_test_result_dict["listOfMatchId"]:
            match_test_result.append(match)

    print(f"match_details: {match_test_result}")


# Execute this program if it is run as a main script (not by 'import')
if __name__ == "__main__":
    print("This is flask " + os.path.basename(__file__) + " for matching an organ...")
    connectAMQP()
    app.run(host="0.0.0.0", port=5020, debug=True)