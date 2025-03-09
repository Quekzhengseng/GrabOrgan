import json
import os
import firebase_admin
from firebase_admin import credentials, firestore
import random
import uuid
from datetime import datetime, timedelta
from organ import Organ

firebase_key_path = os.getenv("ORGAN_DB_KEY")

if not firebase_key_path or not os.path.exists(firebase_key_path):
    raise FileNotFoundError(f"❌ Firebase JSON key not found at {firebase_key_path}")

print(f"✅ Using Firebase key from {firebase_key_path}")

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_key_path)
    firebase_admin.initialize_app(cred)
    print("✅ Firebase initialized successfully!")
else:
    print("⚠ Firebase has already been initialized!")

# Initialize Firestore
db = firestore.client()

# Load donor data from JSON file
with open("getAllDonors.json", "r") as file:
    data = json.load(file)["data"]

# Create a list to hold organ data
organs_list = []

# Start date for organ retrieval (March 2025 onwards)
start_date = datetime(2025, 3, 1)

for donor_id, donor in data.items():
    blood_type = donor.get("bloodType", "Unknown")

    
    if "organs" not in donor:
        continue  

    for organ_type in donor.get("organs", []):
        
        organ_id = f"{donor_id.split('-')[0]}-{organ_type.split('-')[-1]}"  # Use the first part of donor_id, and the organ name

        # Random retrieval date (March 2025 onwards)
        days_offset = random.randint(0, 60)  # Spread out over 2 months
        retrieval_datetime = start_date + timedelta(days=days_offset)
        expiry_datetime = retrieval_datetime + timedelta(hours=48)

        # Create organ object
        organ = Organ(
            organ_id=organ_id,
            donor_id=donor_id,
            organ_type=organ_type.split("-")[-1],  # Extract organ name
            retrieval_datetime=retrieval_datetime.isoformat(),
            expiry_datetime=expiry_datetime.isoformat(),
            status="Available",
            condition="Healthy",
            blood_type=blood_type,
            weight_grams=500,  # Placeholder weight
            hla_typing="A1, B8, DR3",  # Placeholder HLA type
            histopathology="No abnormalities detected",
            storage_temp_celsius=4,  # Typical cold storage temp
            preservation_solution="UW Solution",
            notes="None"
        )

        # Convert organ to dictionary and append to list
        organs_list.append(organ.to_dict())

        # Upload the organ data to Firestore (direct upload)
        organ_ref = db.collection("organs").document(organ_id)  # Use organ_id as document ID
        organ_ref.set(organ.to_dict())

# Optionally save the generated organs to the JSON file if needed
# with open("organs.json", "w") as file:
#     json.dump(organs_list, file, indent=4)

print(f"Generated and uploaded {len(organs_list)} organ records to Firestore.")
