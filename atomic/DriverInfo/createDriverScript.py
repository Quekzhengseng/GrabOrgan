import random
from faker import Faker #pip install faker
import firebase_admin
from firebase_admin import credentials, firestore

fake = Faker()

# Hospital address mapping
hospital_coords_dict = {
    "CGH": "2 Simei St 3, Singapore 529889",
    "SGH": "Outram Rd, Singapore 169608",
    "TTSH": "11 Jln Tan Tock Seng, Singapore 308433",
    "SKGH": "110 Sengkang E Wy, Singapore 544886",
    "NUH": "5 Lower Kent Ridge Rd, Singapore 119074",
    "KTPH": "90 Yishun Central, Singapore 768828",
    "NTFGH": "1 Jurong East Street 21, Singapore 609606"
}

# Create drivers
drivers = []

#keep track of number of drivers in each hospital
hospital_driver_count = {key: 0 for key in hospital_coords_dict.keys()}

while len(drivers) < 15: #i only want 15 drivers for now
    hospital = random.choice(list(hospital_coords_dict.keys()))
    if hospital_driver_count[hospital] >= 3:
        continue  # Skip if hospital already has 3 drivers (because im capping it at 3)

    awaiting_ack = random.choice([True, False])
    is_booked = False if awaiting_ack else random.choice([True, False]) #this line ensures that if awaiting acknowledgement, the driver havent cfm to be booked
    delivery_id = ""

    if is_booked or awaiting_ack:
        delivery_id = f"DELIVERY{random.randint(100,999)}"

    driver = {
        "name": fake.name(),
        "isBooked": is_booked,
        "stationed_hospital": hospital_coords_dict[hospital],
        "currentAssignedDeliveryId": delivery_id,
        "awaitingAcknowledgement": awaiting_ack,
        "email": "alysa.tsjin.2023@scis.smu.edu.sg"
    }
    drivers.append(driver)
    hospital_driver_count[hospital] += 1


#now that drivers array is created, can send to firebase
cred = credentials.Certificate("../../secrets/driverInfo/driver_key.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

def upload_drivers():
    for driver in drivers:
        doc_ref = db.collection('drivers').document()
        doc_ref.set(driver)
        print(f"Uploaded driver: {driver['name']}")

if __name__ == "__main__":
    upload_drivers()
    print("Driver upload complete!")

#the below doesnt contribute to drivers, just for more info for testing
# Find hospitals with no stationed drivers (no staff) and no available drivers (all booked)
no_stationed = [hospital for hospital, count in hospital_driver_count.items() if count == 0]
no_available = []

for hospital, address in hospital_coords_dict.items():
    # A driver is available if isBooked == False and awaitingAcknowledgement == False
    has_available = any(
        d for d in drivers if d["stationed_hospital"] == address and not d["isBooked"] and not d["awaitingAcknowledgement"]
    )
    if not has_available and hospital_driver_count[hospital] > 0:
        no_available.append(hospital)


print(f"There are no stationed drivers that work at the following hospitals: {no_stationed}")
print(f"All drivers are currently booked at the following hospitals: {no_available}")
"""
There are no stationed drivers that work at the following hospitals: []
All drivers are currently booked at the following hospitals: ['TTSH', 'SKGH', 'NUH', 'KTPH', 'NTFGH']
"""