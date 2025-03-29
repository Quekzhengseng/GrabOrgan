from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from os import environ
import os
import uuid
app = Flask(__name__)

CORS(app)

# Load the key from an environment variable
key_path = os.getenv("ORDER_DB_KEY")

if not key_path or not os.path.isfile(key_path):
    raise FileNotFoundError(f"Could not find the Firebase JSON at {key_path}")
# Initialize Firestore
cred = credentials.Certificate(key_path)
firebase_app = firebase_admin.initialize_app(cred)

print("Firestore initialized successfully for Donor!")


db = firestore.client()

class Order:
    def __init__(self, orderId, organType, transplantDateTime, startHospital, endHospital, matchId, remarks):
        self.orderId = orderId
        self.organType = organType  # e.g., "heart"
        self.transplantDateTime = transplantDateTime
        self.startHospital = startHospital  # e.g., "CGH"
        self.endHospital = endHospital  # e.g., "SGH"
        self.matchId = matchId
        self.remarks = remarks  # String of additional info

    def to_dict(self):
        """Convert the Order object to a Firestore-compatible dictionary."""
        return {
            "orderId": self.orderId,
            "organType": self.organType,
            "transplantDateTime": self.transplantDateTime,
            "startHospital": self.startHospital,
            "endHospital": self.endHospital,
            "matchId": self.matchId,
            "remarks": self.remarks
        }

    @staticmethod
    def from_dict(order_id, data):
        """Create an Order object from Firestore document data."""
        return Order(
            orderId=order_id,
            organType=data["organType"],
            transplantDateTime=data["transplantDateTime"],
            startHospital=data["startHospital"],
            endHospital=data["endHospital"],
            matchId=data["matchId"],
            remarks=data.get("remarks", "")  # Default to empty string if not present
        )

@app.route("/order", methods=['GET'])
def get_all_orders():
    """
    Retrieve all Order documents from Firestore.
    """
    try:
        orders_ref = db.collection("orders")
        docs = orders_ref.get()
        orders = {}
        for doc in docs:
            order_data = doc.to_dict()
            # Add the document ID as orderId
            order_data["orderId"] = doc.id  
            orders[doc.id] = order_data
        return jsonify({"code": 200, "data": orders}), 200
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500

@app.route("/order/<string:orderId>")
def get_order(orderId):
    """
    Retrieve a specific Order by its orderId.
    """
    try:
        order_ref = db.collection("orders").document(orderId)
        doc = order_ref.get()
        if doc.exists:
            order_obj = Order.from_dict(orderId, doc.to_dict())
            return jsonify({"code": 200, "data": order_obj.to_dict()}), 200
        else:
            return jsonify({"code": 404, "message": "Order does not exist"}), 404
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500

@app.route("/order/<string:orderId>", methods=['PUT'])
def update_order(orderId):
    """
    Update an existing Order document. The request should contain a JSON payload with the fields to update.
    For example, { "status": 200, "data": { ... updated fields ... } }.
    """
    try:
        order_ref = db.collection("orders").document(orderId)
        doc = order_ref.get()
        if not doc.exists:
            return jsonify({
                "code": 404,
                "data": {"orderId": orderId},
                "message": "Order not found."
            }), 404

        new_data = request.get_json()
        # You might include a status code in the payload to indicate if processing is OK.
        if new_data:
            # Merge the provided data into the existing document.
            order_ref.set(new_data["data"], merge=True)
            return jsonify({
                "code": 200,
                "data": new_data,
                "message": "Order updated successfully."
            }), 200
        else:
            return jsonify({
                "code": 400,
                "message": "No data provided for update."
            }), 400
    except Exception as e:
        return jsonify({
            "code": 500,
            "data": {"orderId": orderId},
            "message": "An error occurred while updating the order: " + str(e)
        }), 500

@app.route("/order", methods=['POST'])
def create_order():
    """
    Create a new Order document. The JSON payload should include an "orderId" and the other required fields.
    """
    try:
        order_data = request.get_json()

        # Ensure orderId is provided
        order_id = order_data.get("orderId")
        if not order_id:
            return jsonify({
                "code": 400,
                "data": {},
                "message": "Order ID is required."
            }), 400

        # Reference to the order document in Firestore
        order_ref = db.collection("orders").document(order_id)
        if order_ref.get().exists:
            return jsonify({
                "code": 409,
                "data": {"orderId": order_id},
                "message": "Order already exists."
            }), 409

        # Create a new Order object using the data from the request
        new_order = Order(
            orderId=order_id,
            organType=order_data["organType"],
            transplantDateTime=order_data["transplantDateTime"],
            startHospital=order_data["startHospital"],
            endHospital=order_data["endHospital"],
            matchId=order_data["matchId"],
            remarks=order_data["remarks"]
        )

        # Save the new Order to Firestore
        order_ref.set(new_order.to_dict())

        return jsonify({
            "code": 201,
            "data": new_order.to_dict(),
            "message": "Order created successfully."
        }), 201

    except Exception as e:
        return jsonify({
            "code": 500,
            "data": {},
            "message": "An error occurred while creating the order: " + str(e)
        }), 500

@app.route("/order/<string:orderId>", methods=['DELETE'])
def delete_match(orderId):
    """Delete an order from Firestore."""
    try:
        order_ref = db.collection("orders").document(orderId)
        doc = order_ref.get()

        if not doc.exists:
            return jsonify({"code": 404, "message": "Order not found"}), 404

        # Delete the organ document from Firestore
        order_ref.delete()

        return jsonify({"code": 200, "message": "Order deleted successfully"}), 200

    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5009, debug=True)