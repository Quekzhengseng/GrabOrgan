# new_donor = Donor(
#     donor_id="1",
#     first_name="John",
#     last_name="Doe",
#     date_of_birth="1980-01-01",
#     datetime_of_death="2069-01-01T24:12:34+00:00",
#     gender="Male",
#     blood_type="O+",
#     organs=[
#         {"organType": "heart", "status": "Donated", "condition": "Healthy"},
#         {"organType": "kidney", "status": "Available", "condition": "Good"}
#     ],
#     medical_history=[
#         {"condition": "Diabetes", "description": "Managed", "dateDiagnosed": "2010-01-01", "treatment": "Insulin"},
#     ],
#     allergies=["peanuts", "aspirin"],
#     nok_contact={"firstName": "Jane", "lastName": "Doe", "relationship": "Spouse", "phone": "12345678"}
# )
# new_donor = Donor(
#     donor_id="2",
#     first_name="Alice",
#     last_name="Tan",
#     date_of_birth="1975-06-15",
#     datetime_of_death="2070-03-22T18:45:00+00:00",
#     gender="Female",
#     blood_type="A-",
#     organs=[
#         {"organType": "liver", "status": "Donated", "condition": "Excellent"},
#         {"organType": "lungs", "status": "Available", "condition": "Good"},
#         {"organType": "pancreas", "status": "Available", "condition": "Normal"}
#     ],
#     medical_history=[
#         {"condition": "Hypertension", "description": "Controlled with medication", "dateDiagnosed": "2015-08-10", "treatment": "Beta-blockers"},
#         {"condition": "Asthma", "description": "Mild, triggered by dust", "dateDiagnosed": "1995-04-20", "treatment": "Inhalers"}
#     ],
#     allergies=["shellfish", "penicillin"],
#     nok_contact={"firstName": "Michael", "lastName": "Tan", "relationship": "Son", "phone": "98765432"}
# )

# db.collection("donors").document(new_donor.donor_id).set(new_donor.to_dict())

# print("Donor added successfully!")