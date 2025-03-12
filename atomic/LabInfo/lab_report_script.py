import random
import string
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

key_path = os.path.join(os.getcwd(), 'secrets', 'Lab_Info_Key.json')

if not os.path.isfile(key_path):
    raise FileNotFoundError(f"Could not find the Firebase JSON at {key_path}")

# Initialize Firebase
cred = credentials.Certificate(key_path)
firebase_app = firebase_admin.initialize_app(cred)
db = firestore.client()

print("Firestore initialized successfully for Lab Reports!")

# Function to generate random date within last 'n' days
def generate_random_date(start_date, end_date):
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    random_date = start_date + timedelta(days=random_days)
    return random_date.strftime("%Y-%m-%d")

# Function to generate randomised data for report fields
def generate_random_data():
    tissue_types = ["A1", "B1", "AB", "O"]
    antibody_screens = ["Negative", "Positive"]
    cross_matches = ["Compatible", "Incompatible"]
    
    # Set start and end dates for the randomisation range
    start_date = datetime(2023, 1, 1)  # Start date for the randomisation (you can modify this)
    end_date = datetime.now()  # End date for the randomisation (current date)

    # Generate random date for the report
    random_date = generate_random_date(start_date, end_date)

    report_data = {
        "reportName": "Organ Donor Compatibility Test Report",
        "testType": "Organ Compatibility Test",
        "dateOfReport": random_date,  # Use the randomised date here
        "reportUrl": f"https://beonbrand.getbynder.com/m/b351439ebceb7d39/original/Laboratory-Tests-for-Organ-Transplant-Rejection.pdf",  
        "results": {
            "tissueType": random.choice(tissue_types),
            "antibodyScreen": random.choice(antibody_screens),
            "crossMatch": random.choice(cross_matches),
            "comments": "To be reviewed."
        }
    }
    return report_data

# Function to populate lab reports and save to Firebase and lab_report.json
def populate_lab_reports():
    try:
        donors_file_path = "getAllDonors.json"
        
        # Load getAllDonors.json
        if not os.path.exists(donors_file_path):
            print("getAllDonors.json not found")
            return
        
        with open(donors_file_path, "r") as donors_file:
            donors_data = json.load(donors_file)
        
        # Extract UUIDs (keys)
        uuids = list(donors_data.get("data", {}).keys())
        
        # Prepare list for the reports to be posted to Firebase and written to JSON file
        reports_list = []

        # Generate randomised data for each UUID
        for uuid in uuids:
            donor_data = generate_random_data()
            donor_data["uuid"] = uuid  # Add UUID to the report data
            reports_list.append(donor_data)
        
        # Post the reports to Firebase
        lab_reports_ref = db.collection('lab_reports')
        
        # Use batch writing to send the data to Firestore
        batch = db.batch()
        for report in reports_list:
            lab_report_ref = lab_reports_ref.document(report["uuid"])
            batch.set(lab_report_ref, report)
        
        batch.commit()

        # Write the same reports to lab_report.json
        lab_report_file_path = "lab_report.json"
        with open(lab_report_file_path, "w") as json_file:
            json.dump(reports_list, json_file, indent=4)
        
        print("Lab reports populated in both Firebase and lab_report.json successfully!")
    
    except Exception as e:
        print(f"Error: {str(e)}")

# Directly call the function to populate the lab reports
populate_lab_reports()