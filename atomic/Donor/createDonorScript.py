import random
import datetime
import uuid
import requests
from donor import Donor  # Assuming you have a Donor class defined in donor.py

# --- Dummy Data Generation Functions ---

def random_date(start_year, end_year):
    """Generate a random date within a given range."""
    start = datetime.date(start_year, 1, 1)
    end = datetime.date(end_year, 12, 31)
    return start + datetime.timedelta(days=random.randint(0, (end - start).days))

def random_datetime_of_death():
    """Generate a random datetime of death in the future."""
    future_date = random_date(2000, 2010)
    # Return in ISO format with fixed time and timezone offset.
    return future_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")

def random_blood_type():
    return random.choice(["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])

def random_gender():
    return random.choice(["Male", "Female"])

def random_organs():
    organ_types = ["heart", "liver", "lungs", "kidneys", "pancreas", "intestines", "cornea"]
    conditions = ["Excellent", "Good", "Normal", "Fair"]
    statuses = ["Donated", "Available", "Unavailable"]
    # Randomly pick 3 unique organs
    return [{"organType": organ, "status": random.choice(statuses), "condition": random.choice(conditions)}
            for organ in random.sample(organ_types, 3)]

def random_medical_history():
    conditions = [
        {"condition": "Hypertension", "description": "Controlled with medication", "treatment": "Beta-blockers"},
        {"condition": "Diabetes", "description": "Type 2, managed with diet", "treatment": "Metformin"},
        {"condition": "Asthma", "description": "Triggered by dust", "treatment": "Inhalers"},
        {"condition": "High Cholesterol", "description": "Mild, controlled with exercise", "treatment": "Statins"},
        {"condition": "Anemia", "description": "Iron deficiency", "treatment": "Iron supplements"}
    ]
    return [
        {**random.choice(conditions), "dateDiagnosed": str(random_date(1990, 2025))}
        for _ in range(random.randint(1, 3))
    ]

def random_allergies():
    possible_allergies = ["pollen", "penicillin", "peanuts", "shellfish", "gluten", "lactose"]
    return random.sample(possible_allergies, random.randint(0, 3))

def random_phone():
    return str(random.randint(80000000, 99999999))

# --- Generate Dummy Donor Data ---
donor_names = []

donors = []

for i, (first, last) in enumerate(donor_names, start=1):
    new_uuid = str(uuid.uuid4())
    random_dob = str(random_date(1940, 1990))
    random_age = 2025 - int(random_dob[:4])
    new_donor = Donor(
        donor_id=new_uuid,
        first_name=first,
        last_name=last,
        date_of_birth=random_dob,
        age=random_age,
        datetime_of_death=random_datetime_of_death(),
        gender=random_gender(),
        blood_type=random_blood_type(),
        organs=random_organs(),
        medical_history=random_medical_history(),
        allergies=random_allergies(),
        nok_contact={
            "firstName": random.choice(["Michael", "Sarah", "David", "Emily"]),
            "lastName": last,  # using donor's last name for simplicity
            "relationship": random.choice(["Son", "Daughter", "Spouse", "Sibling"]),
            "phone": random_phone()
        }
    )
    donors.append(new_donor)

# --- Endpoints (Container URLs) ---
PERSONAL_DATA_URL = "http://localhost:5007/person"    # POST endpoint for personal data
DONOR_URL = "http://localhost:5002/donor"              # POST endpoint for donor data
PSEUDONYM_URL = "http://localhost:5006/pseudonymise"     # POST endpoint for pseudonym service

# --- Process and Split Data for Each Donor ---
for donor in donors:
    # Prepare payload for pseudonym service.
    # The pseudonym service expects a JSON structure with the donor ID as key.
    pseudonym_payload = {
    donor.donor_id: {
        "firstName": donor.first_name,
        "lastName": donor.last_name,
        "dateOfBirth": donor.date_of_birth,
        "age": donor.age,
        "datetimeOfDeath": donor.datetime_of_death,
        "gender": donor.gender,
        "bloodType": donor.blood_type,
        "organs": donor.organs,
        "medicalHistory": donor.medical_history,
        "allergies": donor.allergies,
        "nokContact": donor.nok_contact
        }
    }
    print(f"Sending to pseudonym service for donor {donor.donor_id}: {pseudonym_payload}")
    
    # Call pseudonym service.
    pseudo_resp = requests.post(PSEUDONYM_URL, json=pseudonym_payload)
    if pseudo_resp.status_code != 200:
        print(f"Error in pseudonym service for donor {donor.donor_id}: {pseudo_resp.text}")
        continue

    pseudo_result = pseudo_resp.json()
    # print(pseudo_result)

    # Using keys as returned by the pseudonym service: "person" and "personalData"
    masked_donor_data = pseudo_result.get("person", {}).get(donor.donor_id)
    personal_data = pseudo_result.get("personalData")

    if not masked_donor_data or not personal_data:
        print(f"Incomplete pseudonym response for donor {donor.donor_id}: {pseudo_result}")
        continue

    # Post the masked donor data to the donor endpoint.
    donor_resp = requests.post(DONOR_URL, json=masked_donor_data)
    if donor_resp.status_code != 201:
        # print(masked_donor_data)
        print(f"Error posting masked donor data for donor {donor.donor_id}: {donor_resp.text}")
    else:
        print(f"Masked donor data posted successfully for donor {donor.donor_id}")

    # Post the personal data to the personalData endpoint.
    personal_resp = requests.post(PERSONAL_DATA_URL, json=personal_data)
    if personal_resp.status_code != 201:
        print(f"Error posting personal data for donor {donor.donor_id}: {personal_resp.text}")
    else:
        print(f"Personal data posted successfully for donor {donor.donor_id}")