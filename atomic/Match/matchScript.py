#simulates matching of HLA markers and organs needed / donated across recipients and donors
import json
import random
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate("/Users/isabelle/Documents/SMU/Y2S2/ESD/grabOrgan/GrabOrgan/secrets/Match_Key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Load donor data
with open("getAllDonors.json", "r") as donor_file:
    donors_data = json.load(donor_file)["data"]

# Load recipient data
with open("recipient.json", "r") as recipient_file:
    recipients_data = json.load(recipient_file)["data"]

matches = []

# HLA keys
hla_keys = ["HLA_A_1", "HLA_A_2", "HLA_B_1", "HLA_B_2", "HLA_DR_1", "HLA_DR_2"]

# Function to randomly generate HLA markers as boolean values
def generate_hla_markers():
    return {key: random.choice([True, False]) for key in hla_keys}

# Iterate through recipients
for recipient in recipients_data:
    recipient_id = recipient["recipient_id"]
    organs_needed = recipient.get("organs_needed", [])
    
    # Randomly generate recipient's HLA markers (True/False)
    recipient_hla = generate_hla_markers()
    
    for donor_id, donor_info in donors_data.items():
        # Randomly generate donor's HLA markers (True/False)
        donor_hla = generate_hla_markers()
        
        # Count how many HLA markers match between recipient and donor
        hla_matches = 0
        for key in hla_keys:
            # Randomly decide if there is a match (not just True/False directly)
            if recipient_hla[key] == donor_hla[key]:
                hla_matches += 1
        
        # Skip if fewer than 4/6 HLA matches
        if hla_matches < 4:
            continue  

        donor_organs = donor_info["organs"]
        donor_organs_cleaned = [organ.split('-')[1] for organ in donor_organs]
        
        # For each organ that matches the recipient's needs, create a match entry
        for donor_organ, full_organ in zip(donor_organs_cleaned, donor_organs):
            if donor_organ in organs_needed:
                match = {
                    "matchId": f"{donor_id}-{donor_organ}-{recipient_id}",
                    "recipientId": recipient_id,
                    "recipient_details": {
                        "first_name": recipient["first_name"],
                        "last_name": recipient["last_name"],
                        "blood_type": recipient["blood_type"],
                        "gender": recipient["gender"]
                    },
                    "donorId": donor_id,
                    "donor_details": {
                        "first_name": donor_info["firstName"],
                        "last_name": donor_info["lastName"],
                        "blood_type": donor_info["bloodType"],
                        "gender": donor_info["gender"]
                    },
                    "OrganId": full_organ,  # Keep full organ ID for tracking
                    "numOfHLA": hla_matches,  # Number of HLA matches
                    "Test_DateTime": datetime.now().isoformat()
                }
                matches.append(match)

# Sort matches: 6/6 first, then 5/6, then 4/6
matches.sort(key=lambda x: x["numOfHLA"], reverse=True)

# Save matches to Firebase
for match in matches:
    db.collection("matches").document(match["matchId"]).set(match)

# Save matches to match.json
with open("match.json", "w") as f:
    json.dump(matches, f, indent=4)

print("✅ Matches saved to Firebase and match.json successfully!")