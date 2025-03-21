import firebase_admin
from firebase_admin import credentials, firestore
import os

# Load Firestore credentials from environment variable
key_path = os.getenv("DELIVERY_DB_KEY")

if not key_path or not os.path.isfile(key_path):
    raise FileNotFoundError(f"Could not find the Firebase JSON at {key_path}")

# Initialize Firebase app
cred = credentials.Certificate(key_path)
firebase_app = firebase_admin.initialize_app(cred)

print("Firestore initialized successfully for createDeliveryScript!")

# Firestore client
db = firestore.client()

# Firestore collection for delivery orders
DELIVERY_COLLECTION = "delivery_orders"

# Example delivery documents to populate Firestore
delivery_documents = [
    {
        "status": "Awaiting pickup",
        "pickup": "31 Third Hospital Ave, Singapore 168753",
        "pickup_time": "20250306 09:15:00 AM",
        "destination": "11 Jln Tan Tock Seng, Singapore 308433",
        "destination_time": None,
        "polyline": "test",
        "driverCoord": {"Lat": "123.40", "Lng": "123.49"},
        "driverID": "146789",
        "doctorID": "123690"
    },
    {
        "status": "In progress",
        "pickup": "5 Lower Kent Ridge Rd, Singapore 119074",
        "pickup_time": "20250306 10:30:00 AM",
        "destination": "90 Yishun Central, Singapore 768828",
        "destination_time": None,
        "polyline": "test2",
        "driverCoord": {"Lat": "124.50", "Lng": "124.59"},
        "driverID": "146790",
        "doctorID": "123691"
    },
    {
        "status": "Awaiting pickup",
        "pickup": "110 Sengkang E Wy, Singapore 544886",
        "pickup_time": "20250306 11:00:00 AM",
        "destination": "90 Yishun Central, Singapore 768828",
        "destination_time": None,
        "polyline": "test3",
        "driverCoord": {"Lat": "125.60", "Lng": "125.69"},
        "driverID": "146791",
        "doctorID": "123692"
    },
    {
        "status": "Completed",
        "pickup": "2 Simei St 3, Singapore 529889",
        "pickup_time": "20250305 08:00:00 AM",
        "destination": "31 Third Hospital Ave, Singapore 168753",
        "destination_time": "20250305 09:00:00 AM",
        "polyline": "test4",
        "driverCoord": {"Lat": "126.70", "Lng": "126.79"},
        "driverID": "146792",
        "doctorID": "123693"
    },
    {
        "status": "In progress",
        "pickup": "90 Yishun Central, Singapore 768828",
        "pickup_time": "20250306 01:30:00 PM",
        "destination": "110 Sengkang E Wy, Singapore 544886",
        "destination_time": None,
        "polyline": "test5",
        "driverCoord": {"Lat": "127.80", "Lng": "127.89"},
        "driverID": "146793",
        "doctorID": "123694"
    }
]

# Populate Firestore with delivery documents
for delivery in delivery_documents:
    try:
        db.collection(DELIVERY_COLLECTION).add(delivery)
        print(f"Added delivery document: {delivery}")
    except Exception as e:
        print(f"Failed to add delivery document: {delivery}. Error: {e}")

print("Firestore population completed.")
