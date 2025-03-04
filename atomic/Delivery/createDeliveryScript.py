import firebase_admin
from firebase_admin import credentials, firestore
import random
from datetime import datetime, timedelta
import os

key_path = os.getenv("DELIVERY_DB_KEY")
print(key_path)

# Initialize Firestore
cred = credentials.Certificate(key_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

# Firestore collection
DELIVERY_COLLECTION = "delivery_orders"

# Possible values for pickup and destination
HOSPITALS = ["SGH", "NUH", "TTSH", "KTPH", "CGH"]
STATUSES = ["Awaiting pickup", "In progress", "Delivered"]

# 🚀 Helper function: Format timestamp (YYYYMMDD + 12-hour time)
def format_timestamp(dt):
    """Converts a datetime object into 'YYYYMMDD HH:MM:SS AM/PM' format."""
    return dt.strftime("%Y%m%d %I:%M:%S %p")

# 🚀 Function: Generate unique order ID
def generate_order_id(pickup_location, pickup_time):
    """Generates an Order ID in the format: <pickup_location><YYYYMMDD><4-digit_increment>"""
    pickup_date_str = pickup_time.strftime("%Y%m%d")  # Ensure YYYYMMDD format
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
    
    return f"{prefix}{count:04d}"  # 4-digit incremental value

# 🚀 Function: Generate random timestamps
def generate_random_timestamps(status):
    """
    Generates timestamps based on status:
    - For 'Delivered': Both pickup and destination times with destination after pickup
    - For 'Awaiting pickup' or 'In progress': Only pickup time
    """
    if status == "Delivered":
        # Ensure destination is always after pickup
        pickup_time = datetime.now() + timedelta(days=random.randint(0, 7), hours=random.randint(0, 12))
        destination_time = pickup_time + timedelta(hours=random.randint(1, 5))
        return pickup_time, destination_time
    else:
        # For 'Awaiting pickup' or 'In progress', only generate pickup time
        pickup_time = datetime.now() + timedelta(days=random.randint(0, 7), hours=random.randint(0, 12))
        return pickup_time, None

# 🚀 Function: Create a new delivery document
def create_delivery_document():
    """Generates and inserts a new delivery order into Firestore."""
    pickup_location = random.choice(HOSPITALS)
    destination_location = random.choice([h for h in HOSPITALS if h != pickup_location])  # Ensure different destination
    
    # Randomly select status
    status = random.choice(STATUSES)
    
    # Generate timestamps based on status
    pickup_time, destination_time = generate_random_timestamps(status)

    # Format timestamps
    formatted_pickup_time = format_timestamp(pickup_time)
    formatted_destination_time = format_timestamp(destination_time) if destination_time else None

    # Generate order ID
    order_id = generate_order_id(pickup_location, pickup_time)

    # Create document data
    delivery_data = {
        "orderID": order_id,
        "status": status,
        "pickup": pickup_location,
        "pickup_time": formatted_pickup_time,
        "destination": destination_location,
        "destination_time": formatted_destination_time,  # May be None based on status
    }

    # Insert into Firestore
    db.collection(DELIVERY_COLLECTION).document(order_id).set(delivery_data)

    print(f"Created Delivery Order: {order_id} | Status: {status} | Pickup: {formatted_pickup_time} | Destination: {formatted_destination_time}")

# Generate multiple documents (e.g., 10 orders)
for _ in range(10):
    create_delivery_document()