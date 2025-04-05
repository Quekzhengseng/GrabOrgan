from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from common.invokes import invoke_http

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

DRIVER_INFO_ENDPOINT = "http://driverInfo_service:5004/drivers"
DELIVERY_ENDPOINT = "http://delivery_service:5002/deliveryinfo"

MAX_RETRIES = 3  # Maximum number of retries for message processing
HEADERS = {'Content-Type': 'application/json'}
TIMEOUT = 10  # API timeout for requests

def make_request(url, method="POST", payload=None):
    """ Helper function to send HTTP requests with error handling. """
    try:
        print(f"Making {method} request to {url}")
        if method == "POST":
            response = requests.post(url, headers=HEADERS, json=payload, timeout=TIMEOUT)
        elif method == "PUT":
            response = requests.put(url, headers=HEADERS, json=payload, timeout=TIMEOUT)
        elif method == "PATCH":
            response = requests.patch(url, headers=HEADERS, json=payload, timeout=TIMEOUT)
        else:  # GET request
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)

         # Print the raw response for debugging
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")

        response.raise_for_status()
         # Try to parse JSON but handle cases where response might not be JSON
        try:
            return response.json()
        except ValueError:
            # If response is not valid JSON, return a dict with the text
            return {"code": response.status_code, "message": response.text}
        
    except requests.exceptions.RequestException as e:
        print(f"HTTP Request failed: {e}")
        return None

# Method to update driver records with assigned delivery
def update_driver(driver_id):
    """ Update driver record"""
    payload = {
        "awaitingAcknowledgement": bool(False),
        "currentAssignedDeliveryId": "",
        "isBooked": bool(False),
        }
    response = make_request(f"{DRIVER_INFO_ENDPOINT}/{driver_id}", method="PATCH", payload=payload)

    if response:
        return response.get("message")
    return None

# Method to update delivery records with assigned driver
def update_delivery(delivery_id):
    """ Update delivery record"""
    payload = {
        "status": "Completed",
        }
    response = make_request(f"{DELIVERY_ENDPOINT}/{delivery_id}", method="PUT", payload=payload)

    if response:
        return response.get("message")
    return None

#Migrate to send to doctor instead to end delivery
# def send_driver_notification(driver_id, driver_email, status):
#     """Send notification about driver assignment via AMQP"""
#     try:
#         if not channel:
#             print("RabbitMQ channel not available. Cannot send notification.")
#             return False
            
#         message = {
#             "driverId": driver_id,
#             "email": driver_email
#         }
        
#         # Choose the appropriate routing key based on status
#         routing_key = f"{status}.status"
        
#         print(f"Sending notification with routing key: {routing_key}")
#         channel.basic_publish(
#             exchange="notification_status_exchange",
#             routing_key=routing_key,
#             body=json.dumps(message),
#             properties=pika.BasicProperties(
#                 delivery_mode=2,  # Make message persistent
#                 content_type='application/json'
#             )
#         )
#         print(f"Notification sent for driver {driver_id}")
#         return True
#     except Exception as e:
#         print(f"Error sending notification: {e}")
#         return False

@app.route('/endDelivery', methods=['POST'])
def endDelivery():
    """Ends Delivery with updates to delivery and driver"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        deliveryId = data.get("deliveryId")
        driverId = data.get("driverId")

        if not (deliveryId and driverId):
            return jsonify({"error": "Missing required fields"}), 400

        delivery_response = update_delivery(deliveryId)
        if (delivery_response == None):
            return jsonify({"error": "Failed delivery update"}), 400

        driver_response = update_driver(driverId)

        if (driver_response == None):
            return jsonify({"error": "Failed driver update"}), 400

        return jsonify({
            "code": 200,
            "message": "Delivery ended successfully",
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5028)