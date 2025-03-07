import random
import datetime
from donor import Donor, db

def random_date(start_year, end_year):
    """Generate a random date within a given range."""
    start = datetime.date(start_year, 1, 1)
    end = datetime.date(end_year, 12, 31)
    return start + datetime.timedelta(days=random.randint(0, (end - start).days))

def random_datetime_of_death():
    """Generate a random datetime of death in the future."""
    future_date = random_date(2000, 2010)
    return future_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")

def random_blood_type():
    """Random blood type generator."""
    return random.choice(["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])

def random_gender():
    """Random gender assignment."""
    return random.choice(["Male", "Female"])

def random_organs():
    """Generate a list of random organs with statuses."""
    organ_types = ["heart", "liver", "lungs", "kidneys", "pancreas", "intestines", "cornea"]
    conditions = ["Excellent", "Good", "Normal", "Fair"]
    statuses = ["Donated", "Available", "Unavailable"]
    
    return [{"organType": organ, "status": random.choice(statuses), "condition": random.choice(conditions)} for organ in random.sample(organ_types, 3)]

def random_medical_history():
    """Generate a random medical history."""
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
    """Generate a random list of allergies."""
    possible_allergies = ["pollen", "penicillin", "peanuts", "shellfish", "gluten", "lactose"]
    return random.sample(possible_allergies, random.randint(0, 3))

def random_phone():
    """Generate a random 8-digit phone number."""
    return str(random.randint(80000000, 99999999))

# donor_names =[] # add donor names as tuples ("firstName", "lastName")
donor_names = []

donors = []

for i, (first, last) in enumerate(donor_names, start=1):
    new_donor = Donor(
        donor_id=str(i),
        first_name=first,
        last_name=last,
        date_of_birth=str(random_date(1940, 1990)),
        datetime_of_death=random_datetime_of_death(),
        gender=random_gender(),
        blood_type=random_blood_type(),
        organs=random_organs(),
        medical_history=random_medical_history(),
        allergies=random_allergies(),
        nok_contact={
            "firstName": random.choice(["Michael", "Sarah", "David", "Emily"]),
            "lastName": last,
            "relationship": random.choice(["Son", "Daughter", "Spouse", "Sibling"]),
            "phone": random_phone()
        }
    )
    donors.append(new_donor)

# Add Donors
# print(donors[0].name)
for donor in donors:
    db.collection("donors").document(donor.donor_id).set(donor.to_dict())


"""
Example Donor Schema
new_donor = Donor(
    donor_id="1",
    first_name="John",
    last_name="Doe",
    date_of_birth="1980-01-01",
    datetime_of_death="2005-01-01T24:12:34+00:00",
    gender="Male",
    blood_type="O+",
    organs=[
        {"organType": "heart", "status": "Donated", "condition": "Healthy"},
        {"organType": "kidney", "status": "Available", "condition": "Good"}
    ],
    medical_history=[
        {"condition": "Diabetes", "description": "Managed", "dateDiagnosed": "2010-01-01", "treatment": "Insulin"},
    ],
    allergies=["peanuts", "aspirin"],
    nok_contact={"firstName": "Jane", "lastName": "Doe", "relationship": "Spouse", "phone": "12345678"}
)

"""