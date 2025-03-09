import json
import uuid
import random
from datetime import datetime, timedelta
from organ import Organ

# Load donor data from JSON file
with open("getAllDonors.json", "r") as file:
    data = json.load(file)["data"]

organs_list = []

# Start date for organ retrieval (March 2025 onwards)
start_date = datetime(2025, 3, 1)

for donor_id, donor in data.items():
    blood_type = donor.get("bloodType", "Unknown")

    for organ_type in donor.get("organs", []):
        organ_id = str(uuid.uuid4())

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

        organs_list.append(organ.to_dict())

# Save generated organ data to JSON
with open("organs.json", "w") as file:
    json.dump(organs_list, file, indent=4)

print(f"Generated {len(organs_list)} organ records.")
