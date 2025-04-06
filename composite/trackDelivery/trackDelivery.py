from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import pika
import json
import time

app = Flask(__name__)
CORS(app)

# Define service endpoints
SERVICE_URLS = {
    "delivery": "http://delivery_service:5002",
    "driver": "http://driver_service:5003",
    "driver_info": "http://driverInfo_service:5004",
    "geo_algo": "http://geoalgo_service:5006",
    "location": "https://zsq.outsystemscloud.com/Location/rest/Location"
}

HEADERS = {'Content-Type': 'application/json'}

# RabbitMQ connection parameters
rabbit_host = os.environ.get("rabbit_host", "localhost")
rabbit_port = int(os.environ.get("rabbit_port", "5672"))

channel = None

def addressToCoord(address):
    """Convert an address to latitude/longitude coordinates."""
    try:
        response = requests.post(f"{SERVICE_URLS['location']}/PlaceToCoord", headers=HEADERS, json={"long_name": address}, timeout=5)
        response.raise_for_status()
        data = response.json()
        return {"lat": data.get("latitude"), "lng": data.get("longitude")}
    except requests.exceptions.RequestException as e:
        print(f"Error in addressToCoord: {e}")
        return None

def retrievePolyline(coord1, coord2):
    """Retrieve a polyline route between two coordinates."""
    payload = {
        "routingPreference": "TRAFFIC_AWARE",
        "travelMode": "DRIVE",
        "computeAlternativeRoutes": False,
        "destination": {"location": {"latLng": {"latitude": coord2['lat'], "longitude": coord2['lng']}}},
        "origin": {"location": {"latLng": {"latitude": coord1['lat'], "longitude": coord1['lng']}}}
    }
    try:
        response = requests.post(f"{SERVICE_URLS['location']}/route", headers=HEADERS, json=payload, timeout=5)
        response.raise_for_status()
        return response.json().get("Route", [{}])[0].get("Polyline", {}).get("encodedPolyline")
    except requests.exceptions.RequestException as e:
        print(f"Error in retrievePolyline: {e}")
        return None

def getDelivery(deliveryId):
    """Retrieve delivery information by ID."""
    try:
        response = requests.get(f"{SERVICE_URLS['delivery']}/deliveryinfo/{deliveryId}", timeout=5)
        response.raise_for_status()
        return response.json().get("data")
    except requests.exceptions.RequestException as e:
        print(f"Error in getDelivery: {e}")
        return None
    
def updateDeliveryStatus(deliveryId, status):
    """Update delivery information by Status"""
    try:
        # Create payload with the status
        payload = {"status": status}
        
        # Send PUT request with the JSON payload
        response = requests.put(
            f"{SERVICE_URLS['delivery']}/deliveryinfo/{deliveryId}", 
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=5
        )       
        
        response.raise_for_status()
        return response.json().get("data")
    except requests.exceptions.RequestException as e:
        print(f"Error in updateDeliveryStatus: {e}")
        return None

def getDeviation(polyline, driverCoord):
    """Check if the driver has deviated from the route."""
    try:
        response = requests.post(f"{SERVICE_URLS['geo_algo']}/deviate", headers=HEADERS, json={"polyline": polyline, "driverCoord": driverCoord}, timeout=5)
        response.raise_for_status()
        return response.json().get("data", {}).get("deviate")
    except requests.exceptions.RequestException as e:
        print(f"Error in getDeviation: {e}")
        return None

def updateDelivery(encoded_polyline, driverCoord, deliveryId):
    """Update the delivery details."""
    try:
        response = requests.put(f"{SERVICE_URLS['delivery']}/deliveryinfo/{deliveryId}", json={"polyline": encoded_polyline, "driverCoord": driverCoord}, timeout=5)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error in updateDelivery: {e}")
        return False
    
def connect_to_rabbitmq():
    global channel
    for i in range(5):  # Try 5 times
        try:
            print(f"Attempt {i+1} to connect to RabbitMQ at {rabbit_host}:{rabbit_port}")
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbit_host, port=rabbit_port)
            )
            channel = connection.channel()
            print("Connected to RabbitMQ successfully")
            return True
        except Exception as e:
            print(f"Failed to connect to RabbitMQ: {str(e)}")
            if i < 4:  # Don't sleep after the last attempt
                print(f"Retrying in 5 seconds...")
                time.sleep(5)
    channel = None
    return False

def safe_publish(exchange, routing_key, message):
    """Safely publish a message, with connection checks and error handling"""
    global channel
    
    if channel is None:
        print("Channel not available. Attempting to reconnect...")
        if not connect_to_rabbitmq():
            print("Failed to reconnect to RabbitMQ. Message not sent.")
            return False
    
    try:
        message_str = message if isinstance(message, str) else json.dumps(message)
        channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=message_str,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        print(f"Message published to {exchange} with routing key {routing_key}")
        return True
    except Exception as e:
        print(f"Error publishing message: {e}")
        channel = None  # Reset channel so next attempt will reconnect
        pass

def getPercentageProgress(originCoord, destinationCoord, currentCoord):
    """Retrieve a progress given 3 points, start, end, current based on travel duration"""
    # Get total trip duration (origin to destination)
    payload = {
        "routingPreference": "TRAFFIC_AWARE",
        "travelMode": "DRIVE",
        "computeAlternativeRoutes": False,
        "destination": {"location": {"latLng": {"latitude": destinationCoord['lat'], "longitude": destinationCoord['lng']}}},
        "origin": {"location": {"latLng": {"latitude": originCoord['lat'], "longitude": originCoord['lng']}}}
    }
    try:
        response = requests.post(f"{SERVICE_URLS['location']}/route", headers=HEADERS, json=payload, timeout=5)
        response.raise_for_status()
        
        # Extract duration from string like "1472s"
        duration_str = response.json().get("Route", [{}])[0].get("Duration", "0s")
        total_duration = int(duration_str.replace("s", ""))
        
        # If total duration is 0, return a default value
        if total_duration == 0:
            print("Total duration is 0, returning default progress value of 0.0")
            return 0.0
            
    except Exception as e:
        print(f"Error getting total duration: {e}")
        return 0.0  # Return a default instead of None

    # Get duration from origin to current position
    payload2 = {
        "routingPreference": "TRAFFIC_AWARE",
        "travelMode": "DRIVE",
        "computeAlternativeRoutes": False,
        "destination": {"location": {"latLng": {"latitude": currentCoord['lat'], "longitude": currentCoord['lng']}}},
        "origin": {"location": {"latLng": {"latitude": originCoord['lat'], "longitude": originCoord['lng']}}}
    }

    try:
        response2 = requests.post(f"{SERVICE_URLS['location']}/route", headers=HEADERS, json=payload2, timeout=5)
        response2.raise_for_status()
        
        # Extract duration from string like "1472s"
        current_duration_str = response2.json().get("Route", [{}])[0].get("Duration", "0s")
        current_duration = int(current_duration_str.replace("s", ""))
    except Exception as e:
        print(f"Error getting current duration: {e}")
        return 0.0  # Return a default instead of None
    
    # Calculate percentage and ensure it's between 0 and 1
    try:
        percent = current_duration / total_duration if total_duration > 0 else 0.0
        print(f"Current Percentage: {percent}")
        return max(0.0, min(1.0, percent))
    except Exception as e:
        print(f"Error calculating percentage: {e}")
        return 0.0  # Return a default value in case of calculation errors

def send_driver_notification(driver_id, driver_email, status):
    """Send notification about driver assignment via AMQP"""
    try:
        if not channel:
            print("RabbitMQ channel not available. Cannot send notification.")
            return False
            
        message = {
            "driverId": driver_id,
            "email": driver_email
        }
        
        # Choose the appropriate routing key based on status
        routing_key = f"{status}.status"
        
        print(f"Sending notification with routing key: {routing_key}")
        safe_publish("notification_status_exchange", routing_key , message)
        print(f"Notification sent for driver {driver_id}")
        return True
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False

@app.route('/trackDelivery', methods=['POST'])
def updateDeliveryComposite():
    """Update delivery tracking information, handling deviations if necessary."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        deliveryId = data.get("deliveryId")
        driverCoord = data.get("driverCoord")

        if not (deliveryId and driverCoord):
            return jsonify({"error": "Missing required fields"}), 400

        # Retrieve delivery information
        deliveryData = getDelivery(deliveryId)
        if not deliveryData:
            return jsonify({"error": "Failed to retrieve delivery"}), 500

        polyline = deliveryData.get("polyline")
        if not polyline:
            return jsonify({"error": "Missing polyline in delivery data"}), 500

        # Check if the driver has deviated
        deviation = getDeviation(polyline, driverCoord)
        if deviation is None:
            return jsonify({"error": "Failed to check deviation"}), 500
        
        origin = addressToCoord(deliveryData.get("pickup"))
        if not origin:
                return jsonify({"error": "Failed to retrieve origin coordinates"}), 500
        
        destination = addressToCoord(deliveryData.get("destination"))
        if not destination:
                return jsonify({"error": "Failed to retrieve destination coordinates"}), 500
    
        percentage = getPercentageProgress(origin, destination, driverCoord)

        if not percentage:
                return jsonify({"error": "Failed to retrieve percentage"}), 500
        
        status = deliveryData.get("status")

        # When delivery is complete (100%)
        if percentage > 0.95 and status == "close_by":
            # Update status to "Arrived"
            updated_data = updateDeliveryStatus(deliveryId, "arrived")
            send_driver_notification(deliveryData.get("driverId"), deliveryData.get("doctorId"), "arrived")
            message = json.dumps({"Status": "arrived", "deliveryId": deliveryId})
            safe_publish("activity_log_exchange", "track_delivery.info", message)
            if not updated_data:
                return jsonify({"error": "Failed to update delivery status to arrived"}), 500
        # When driver is near destination (>75%)
        elif percentage > 0.75 and status == "halfway":
            # Update status to "close_by"
            updated_data = updateDeliveryStatus(deliveryId, "close_by")
            send_driver_notification(deliveryData.get("driverId"), deliveryData.get("doctorId"), "close_by")
            message = json.dumps({"Status": "close_by", "deliveryId": deliveryId})
            safe_publish("activity_log_exchange", "track_delivery.info", message)
            if not updated_data:
                return jsonify({"error": "Failed to update delivery status to close by"}), 500
        # When driver has covered half the distance (>50%)
        elif percentage > 0.5 and status == "on_the_way":
            # Update status to "halfway"
            updated_data = updateDeliveryStatus(deliveryId, "halfway")
            send_driver_notification(deliveryData.get("driverId"), deliveryData.get("doctorId"), "halfway")
            message = json.dumps({"Status": "halfway", "deliveryId": deliveryId})
            safe_publish("activity_log_exchange", "track_delivery.info", message)
            if not updated_data:
                return jsonify({"error": "Failed to update delivery status to halfway"}), 500
        elif percentage > 0 and status == "Assigned":
            # Update status to "on_the_Way"
            updated_data = updateDeliveryStatus(deliveryId, "on_the_way")
            send_driver_notification(deliveryData.get("driverId"), deliveryData.get("doctorId"), "on_the_way")
            message = json.dumps({"Status": "on_the_way", "deliveryId": deliveryId})
            safe_publish("activity_log_exchange", "track_delivery.info", message)
            if not updated_data:
                return jsonify({"error": "Failed to update delivery status to on the way"}), 500

        if deviation:
            # Retrieve new polyline if deviation occurs
            new_polyline = retrievePolyline(driverCoord, destination)
            if not new_polyline:
                return jsonify({"error": "Failed to retrieve new polyline"}), 500

            success = updateDelivery(new_polyline, driverCoord, deliveryId)
            if not success:
                return jsonify({"error": "Failed to update delivery"}), 500
        else:
            success = updateDelivery(polyline, driverCoord, deliveryId)
            if not success:
                return jsonify({"error": "Failed to update delivery"}), 500
        return jsonify({
            "code": 200,
            "message": "Tracking updated successfully",
            "data": {"polyline": new_polyline if deviation else polyline, "deviation": deviation}
        }), 200

    except Exception as e:
        print("Error in process_match_request:", str(e))
        error_payload = json.dumps({
            "error": str(e),
            "track_delivery": deliveryId
        })
        try:
            safe_publish("error_handling_exchange", "track_delivery.error", error_payload)
        except Exception as publish_exception:
            print("Failed to publish error message:", str(publish_exception))
        return jsonify({"code": 500, "message": "Error processing match request."}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    connect_to_rabbitmq()
    app.run(host='0.0.0.0', port=5025)
