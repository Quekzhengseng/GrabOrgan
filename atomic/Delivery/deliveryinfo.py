from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load Firestore credentials from environment variable
key_path = os.getenv("DELIVERY_DB_KEY")

if not key_path or not os.path.isfile(key_path):
    raise FileNotFoundError(f"Could not find the Firebase JSON at {key_path}")

cred = credentials.Certificate(key_path)
firebase_app = firebase_admin.initialize_app(cred)

print("Firestore initialized successfully for DeliveryInfo!")

db = firestore.client()

# Firestore collection for delivery orders
DELIVERY_COLLECTION = "delivery_orders"

# Function to generate unique orderID
def generate_order_id(pickup_location, pickup_date):
    """Generates a unique Order ID in the format: <pickup_location><pickup_date><4-digit_increment>"""
    pickup_date_str = pickup_date.strftime("%Y%m%d")  # ✅ Correct format YYYYMMDD
    prefix = f"{pickup_location}{pickup_date_str}"
    
    # Reference to the counter document
    counter_ref = db.collection("counters").document(prefix)
    
    # Define transaction operation
    @firestore.transactional
    def update_in_transaction(transaction, counter_ref):
        counter_doc = counter_ref.get(transaction=transaction)
        if counter_doc.exists:
            current_count = counter_doc.to_dict().get('count', 0) + 1
        else:
            current_count = 1
            
        transaction.set(counter_ref, {'count': current_count})
        return current_count
    
    # Execute the transaction
    count = update_in_transaction(db.transaction(), counter_ref)
    
    # Return the formatted ID
    print(f"{prefix}{count:04d}")
    return f"{prefix}{count:04d}"  # 4-digit incremental value

def format_datetime(dt_str):
    """Convert a datetime string to Firestore-compatible format with YYYYMMDD date."""
    try:
        # Try parsing the new YYYYMMDD format first
        dt = datetime.strptime(dt_str, "%Y%m%d %I:%M:%S %p")
        formatted_date = dt.strftime("%Y%m%d")  # Convert to YYYYMMDD
        formatted_time = dt.strftime("%I:%M:%S %p")  # Keep HH:MM:SS AM/PM
        return f"{formatted_date} {formatted_time}", dt
    except ValueError:
        return None, None

def is_valid_status(status, destination_time):
    """Ensure that 'Awaiting pickup' and 'In progress' statuses have no destination_time."""
    if status in ["Awaiting pickup", "In progress"] and destination_time is not None:
        return False
    return True

# DeliveryInfo Class
class DeliveryInfo:
    def __init__(self, order_id, status, pickup, pickup_time, destination, destination_time):
        self.order_id = order_id
        self.status = status
        self.pickup = pickup
        self.pickup_time = pickup_time
        self.destination = destination
        self.destination_time = destination_time

    def to_dict(self):
        """Convert the object to a Firestore-compatible dictionary."""
        return {
            "orderID": self.order_id,
            "status": self.status,
            "pickup": self.pickup,
            "pickup_time": self.pickup_time,
            "destination": self.destination,
            "destination_time": self.destination_time
        }

    @staticmethod
    def from_dict(order_id, data):
        """Create a DeliveryInfo object from Firestore document data."""
        return DeliveryInfo(
            order_id=order_id,
            status=data["status"],
            pickup=data["pickup"],
            pickup_time=data["pickup_time"],
            destination=data["destination"],
            destination_time=data["destination_time"]
        )

# 📌 Route: Get all delivery orders
@app.route("/deliveryinfo", methods=["GET"])
def get_all_deliveries():
    try:
        deliveries_ref = db.collection(DELIVERY_COLLECTION)
        docs = deliveries_ref.get()
        deliveries = {}

        for doc in docs:
            delivery_obj = DeliveryInfo.from_dict(doc.id, doc.to_dict())
            deliveries[doc.id] = delivery_obj.to_dict()  # Convert back to dict
        
        return jsonify({"success": True, "code": 200, "data": deliveries}), 200
    except Exception as e:
        return jsonify({"success": False, "code": 500, "error": str(e)}), 500


# 📌 Route: Get a specific delivery order
@app.route("/deliveryinfo/<string:order_id>", methods=["GET"])
def get_delivery(order_id):
    try:
        delivery_ref = db.collection(DELIVERY_COLLECTION).document(order_id)
        doc = delivery_ref.get()
        
        if doc.exists:
            delivery_obj = DeliveryInfo.from_dict(order_id, doc.to_dict())
            return jsonify({"success": True, "code": 200, "data": delivery_obj.to_dict()}), 200
        else:
            return jsonify({"success": False, "code": 404, "error": "Delivery order not found"}), 404

    except Exception as e:
        return jsonify({"success": False, "code": 500, "error": str(e)}), 500


# 📌 Route: Create a new delivery order (Auto-Generated Order ID)
@app.route("/deliveryinfo", methods=["POST"])
def create_delivery():
    try:
        data = request.get_json()
        required_fields = ["status", "pickup", "pickup_time", "destination", "destination_time"]
        
        if not all(field in data for field in required_fields):
            return jsonify({"success": False, "code": 400, "error": "Missing required fields"}), 400

        # Format and validate pickup_time
        formatted_pickup_time, pickup_dt = format_datetime(data["pickup_time"])
        if not pickup_dt:
            return jsonify({"success": False, "code": 400, "error": "Invalid pickup_time format. Expected 'YYYYMMDD HH:MM:SS AM/PM'"}), 400

        # Format and validate destination_time
        formatted_destination_time, destination_dt = None, None
        if data["destination_time"] is not None:
            formatted_destination_time, destination_dt = format_datetime(data["destination_time"])
            if not destination_dt:
                return jsonify({"success": False, "code": 400, "error": "Invalid destination_time format. Expected 'YYYYMMDD HH:MM:SS AM/PM'"}), 400
            
            if destination_dt <= pickup_dt:
                return jsonify({"success": False, "code": 400, "error": "destination_time must be after pickup_time."}), 400

        # Validate status constraints
        if not is_valid_status(data["status"], formatted_destination_time):
            return jsonify({"success": False, "code": 400, "error": "destination_time should be empty if status is 'Awaiting pickup' or 'In progress'."}), 400

        # Generate Order ID
        order_id = generate_order_id(data["pickup"], pickup_dt)

        # Create Firestore document
        delivery_data = {
            "orderID": order_id,
            "status": data["status"],
            "pickup": data["pickup"],
            "pickup_time": formatted_pickup_time,
            "destination": data["destination"],
            "destination_time": formatted_destination_time,
        }

        db.collection(DELIVERY_COLLECTION).document(order_id).set(delivery_data)

        return jsonify({"success": True, "code": 201, "message": "Delivery order created successfully", "orderID": order_id}), 201
    except Exception as e:
        return jsonify({"success": False, "code": 500, "error": str(e)}), 500


# 📌 Route: Update a delivery order
@app.route("/deliveryinfo/<string:order_id>", methods=["PUT"])
def update_delivery(order_id):
    try:
        delivery_ref = db.collection(DELIVERY_COLLECTION).document(order_id)
        doc = delivery_ref.get()
        
        if not doc.exists:
            return jsonify({"success": False, "code": 404, "error": "Delivery order not found"}), 404

        update_data = request.get_json()

        # Ensure the update follows the expected structure
        valid_fields = ["status", "pickup_time", "destination_time"]
        filtered_data = {key: update_data[key] for key in valid_fields if key in update_data}

        if not filtered_data:
            return jsonify({"success": False, "code": 400, "error": "No valid fields to update"}), 400

        # Retrieve existing data
        existing_data = doc.to_dict()

        # Validate pickup_time (only if it exists)
        pickup_dt = None
        if "pickup_time" in filtered_data and filtered_data["pickup_time"]:
            formatted_pickup_time, pickup_dt = format_datetime(filtered_data["pickup_time"])
            if not pickup_dt:
                return jsonify({"success": False, "code": 400, "error": "Invalid pickup_time format. Expected 'YYYYMMDD HH:MM:SS AM/PM'"}), 400
            filtered_data["pickup_time"] = formatted_pickup_time

        # Validate destination_time (only if it exists)
        destination_dt = None
        if "destination_time" in filtered_data and filtered_data["destination_time"]:
            formatted_destination_time, destination_dt = format_datetime(filtered_data["destination_time"])
            if not destination_dt:
                return jsonify({"success": False, "code": 400, "error": "Invalid destination_time format. Expected 'YYYYMMDD HH:MM:SS AM/PM'"}), 400
            
            # Ensure destination_time is after pickup_time
            if pickup_dt and destination_dt and destination_dt <= pickup_dt:
                return jsonify({"success": False, "code": 400, "error": "destination_time must be after pickup_time."}), 400

            filtered_data["destination_time"] = formatted_destination_time
        
        # Validate status constraints
        if "status" in filtered_data:
            if not is_valid_status(filtered_data["status"], filtered_data.get("destination_time")):
                return jsonify({"success": False, "code": 400, "error": "destination_time should be empty if status is 'Awaiting pickup' or 'In progress'."}), 400

        # Update Firestore document
        db.collection(DELIVERY_COLLECTION).document(order_id).set(filtered_data, merge=True)

        return jsonify({"success": True, "code": 200, "message": "Delivery order updated successfully"}), 200
    except Exception as e:
        print(f"Error updating delivery: {e}")  # Log the error
        return jsonify({"success": False, "code": 500, "error": str(e)}), 500

# 📌 Route: Delete a delivery order
@app.route("/deliveryinfo/<string:order_id>", methods=["DELETE"])
def delete_delivery(order_id):
    try:
        delivery_ref = db.collection(DELIVERY_COLLECTION).document(order_id)
        doc = delivery_ref.get()
        
        if not doc.exists:  # Fixed: removed parentheses
            return jsonify({"success": False, "code": 404, "error": "Delivery order not found"}), 404
        
        delivery_ref.delete()
        return jsonify({"success": True, "code": 200, "message": "Delivery order deleted successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "code": 500, "error": str(e)}), 500

# Run Flask app
if __name__ == '__main__':
    print(f"This is flask for {os.path.basename(__file__)}: managing delivery orders ...")
    app.run(host='0.0.0.0', port=5002, debug=True)
