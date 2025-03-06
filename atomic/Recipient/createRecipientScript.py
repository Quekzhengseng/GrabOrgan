import os
import random
import datetime
import firebase_admin
from firebase_admin import credentials, firestore
from recipient import Recipient, db

firebase_key_path = os.getenv("RECIPIENT_DB_KEY")

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

def random_date(start_year, end_year):
    """Generate a random date within a given range."""
    start = datetime.date(start_year, 1, 1)
    end = datetime.date(end_year, 12, 31)
    return start + datetime.timedelta(days=random.randint(0, (end - start).days))


def random_blood_type():
    """Random blood type generator."""
    return random.choice(["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])


def random_gender():
    """Random gender assignment."""
    return random.choice(["Male", "Female"])


def random_organs_needed():
    """Generate a list of organs a recipient needs."""
    organ_types = ["heart", "liver", "lungs", "kidneys", "pancreas", "intestines", "cornea"]
    return random.sample(organ_types, random.randint(1, 3))


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


recipient_names = [
    ("Ryan", "Leow"),
    ("Jia Zheng", "Lim"),
    ("Ivan", "Tan"),
    ("Eng Kit", "Lum"),
    ("Lay Foo", "Thiang"),
    ("Swetha", "Gottipati"),
    ("Danish", "Lim"),
    ("Khong Kham", "Nang"),
    ("Angela", "Neo"),
    ("Yi Kai", "Neo"),
    ("Daryl", "Ng"),
    ("Nicholas", "Lam"),
    ("Nicholas", "Lim"),
    ("Zheng Feng", "Ong"),
    ("Phoebe", "Neo"),
    ("Precia", "Lam"),
    ("Zheng Seng", "Quek"),
    ("Ramasamy", "Vighnesh"),
    ("Yu Xuan", "Shiow"),
    ("Eunice", "Sng"),
    ("Barry", "Tan"),
    ("Wei Wen", "Tan"),
    ("Shamel", "TengKu"),
    ("Panhchaknut", "Tou"),
    ("Ze Jia", "Goh"),
    ("Lucas", "Wong"),
    ("Zavier", "Yan"),
    ("Kang Yan", "Yang"),
    ("Ming", "Yuen"),
    ("Jia Jun", "Zhang")
]
recipients = []

for i, (first, last) in enumerate(recipient_names, start=1):
    new_recipient = {
        "recipient_id": str(i),
        "first_name": first,
        "last_name": last,
        "date_of_birth": str(random_date(1940, 2010)),
        "gender": random_gender(),
        "blood_type": random_blood_type(),
        "organs_needed": random_organs_needed(),
        "medical_history": random_medical_history(),
        "allergies": random_allergies(),
        "nok_contact": {
            "firstName": random.choice(["Michael", "Sarah", "David", "Emily"]),
            "lastName": last,
            "relationship": random.choice(["Son", "Daughter", "Spouse", "Sibling"]),
            "phone": random_phone()
        }
    }
    recipients.append(new_recipient)

# Add Recipients to Database
for recipient in recipients:
    try:
        doc_ref = db.collection("recipients").document(recipient["recipient_id"])
        doc_ref.set(recipient)
        print(f"✅ Added recipient {recipient['first_name']} {recipient['last_name']} successfully.")
    except Exception as e:
        print(f"❌ Error adding recipient {recipient['first_name']} {recipient['last_name']}: {e}")
