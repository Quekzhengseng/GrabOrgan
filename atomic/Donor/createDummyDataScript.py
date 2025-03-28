import random
import datetime
import uuid
import requests
import string
from donor import Donor  # Assuming you have a Donor class defined in donor.py

# --- Endpoints (Container URLs) ---
PERSONAL_DATA_URL = "http://PersonalData:5007/person"   # POST endpoint for personal data
PERSONAL_DATA_URL = "https://personal-gbst4bsa.outsystemscloud.com/PatientAPI/rest/patientAPI/patients/"
DONOR_URL = "http://donor:5003/donor"              # POST endpoint for donor data
PSEUDONYM_URL = "http://pseudonym:5012/pseudonymise"     # POST endpoint for pseudonym service
ORGAN_URL = "http://organ:5010/organ" 
LAB_INFO_URL="http://labInfo:5007/lab-reports"

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

def generate_hla_profile():
    # Simulate two alleles for each of the 3 key loci
    hla_options = {
    "A": ["A1", "A2", "A3", "A11", "A24", "A26"],
    "B": ["B7", "B8", "B27", "B35", "B44", "B51"],
    "DR": ["DR1", "DR3", "DR4", "DR7", "DR11", "DR15"]
    }
    profile = {}
    for locus, alleles in hla_options.items():
        profile[locus] = random.sample(alleles, 2) 
    return profile # output: {'A': 'A1/A24', 'B': 'B8/B27', 'DR': 'DR3/DR15'}

# def random_organs():
#     organ_types = ["heart", "liver", "lungs", "kidneys", "pancreas"]
#     conditions = ["Excellent", "Good", "Normal", "Fair"]
#     statuses = ["Donated", "Available", "Unavailable"]
#     # Randomly pick 3 unique organs
#     return [{"organType": organ, "status": random.choice(statuses), "condition": random.choice(conditions)}
#             for organ in random.sample(organ_types, 4)]
# def random_organs(new_uuid, bloodType):
#     organ_types = ["heart", "liver", "lungs", "kidneys", "pancreas"]
#     organIdArr = []

#     for organ in random.sample(organ_types, 3):
#         organId = organ + "=" + new_uuid
    
#         organIdArr.append(organId)
#     return organIdArr

def random_organs(new_uuid, bloodType):
    organ_types = ["heart", "liver", "lungs", "kidneys", "pancreas"]
    organIdArr = []
    conditions = ["Excellent", "Good", "Normal", "Fair"]


    for organ in random.sample(organ_types, 4):
        organId = f"{organ}={new_uuid}"
        organ_data = {
            "organId": organId,
            "organType": organ,
            "donorId": new_uuid,
            "bloodType": bloodType,
            "condition": random.choice(conditions)  # or any random string if you want variety
        }

        # Post the organ data to the Organ DB
        organ_resp = requests.post(ORGAN_URL, json=organ_data)
        if organ_resp.status_code != 201:
            print(f"Error posting organ data for donor {new_uuid}: {organ_resp.text}")
        else:
            print(f"Organ data posted successfully for donor {new_uuid}")

        organIdArr.append(organId)

    return organIdArr

# print(random_organs("fcb3258f"))
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

def random_email(first, last):
    return first+last+"@gmail.com"

def random_nric(dob):
    start = ["S"]
    random_letter = random.choice(string.ascii_uppercase)
    random_number = str(random.randint(10000, 99999))
    return "S" + dob[2:4] + random_number + random_letter

def random_address():
    place_names = [ "Victoria", "Orchard", "Tanjong Pagar", "Bukit Timah",
        "Serangoon", "Bras Basah", "Jalan Besar", "Clementi", "Tampines Central", "Holland",
        "Paya Lebar", "Toa Payoh", "Yishun", "Ang Mo Kio", "Sengkang", "Bukit Batok",
        "Jurong East", "Telok Blangah", "Pasir Ris", "Woodlands"
        ]
    street_names = [
    "Street",
    "Road",
    "Avenue",
    "Central",
    ]
    random_place = random.choice(place_names)
    random_number = str(random.randint(1, 99))
    random_street = random.choice(street_names)
    return random_number + random_place + random_street



# --- Generate Dummy Donor Data ---
donor_names = []


donors = []

for i, (first, last) in enumerate(donor_names, start=1):
    new_uuid = str(uuid.uuid4())
    random_dob = str(random_date(1940, 1990))
    random_age = 2025 - int(random_dob[:4])
    random_address = random_address()
    random_bloodType = random_blood_type()
    new_donor = Donor(
        donor_id=new_uuid,
        first_name=first,
        last_name=last,
        date_of_birth=random_dob,
        nric=random_nric(random_dob),
        email=random_email(first, last),
        address=random_address,
        age=random_age,
        datetime_of_death=random_datetime_of_death(),
        gender=random_gender(),
        blood_type=random_blood_type,
        organs=random_organs(new_uuid, random_bloodType),
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
        "nric": donor.nric,
        "email": donor.email,
        "address": donor.address,
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

    # Using keys as returned by the pseudonym service: "maskedData" and "personalData"
    masked_donor_data = pseudo_result.get("maskedData", {}).get(donor.donor_id)
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

        # Post the masked donor data to the donor endpoint.
    organ_resp = requests.post(ORGAN_URL, json=organ)
    if organ_resp.status_code != 201:
        # print(masked_donor_data)
        print(f"Error posting masked donor data for donor {organ["donorId"]}: {organ_resp.text}")
    else:
        print(f"Organ data posted successfully for donor {organ["donorId"]}")