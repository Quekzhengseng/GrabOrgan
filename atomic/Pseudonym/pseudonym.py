from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import random 

app = Flask(__name__)
CORS(app)

def pseudonymise_name(name):
    # Return a random color from a predefined list.
    colors = [
        "red", "blue", "green", "yellow", "orange", "purple", "pink", "brown", "black", "white", "gray", "cyan", "magenta",
        "lime", "maroon", "navy", "olive", "teal", "silver", "gold", "beige", "ivory", "tan", "coral", "salmon", "indigo",
        "violet", "turquoise", "azure", "lavender", "chartreuse", "crimson", "scarlet", "amber", "burgundy", "plum",
        "peach", "apricot", "rose", "ruby", "sapphire", "emerald", "jade", "topaz", "amethyst", "periwinkle", "mint",
        "aqua", "fuchsia", "charcoal", "slate", "gunmetal", "copper", "bronze", "mahogany", "chestnut", "mauve", "cerulean",
        "vermilion", "saffron", "khaki", "sepia", "taupe", "mustard", "sand", "wheat", "denim", "skyblue", "royalblue",
        "midnightblue", "dodgerblue", "steelblue", "cornflowerblue", "cadetblue", "powderblue", "lightblue", "deepskyblue",
        "lightskyblue", "darkblue", "mediumblue", "aquamarine", "springgreen", "mediumseagreen", "seagreen", "darkgreen",
        "forestgreen", "limegreen", "palegreen", "lightgreen", "darkolivegreen", "olivedrab", "lawngreen", "greenyellow",
        "yellowgreen", "darkkhaki", "palegoldenrod", "lightgoldenrodyellow", "lemonchiffon", "lightyellow", "goldenrod",
        "darkgoldenrod", "orangered", "tomato", "darkorange", "chocolate", "saddlebrown", "rosybrown", "firebrick",
        "indianred", "lightcoral", "darkred", "hotpink", "deeppink", "lightpink", "palevioletred", "mediumvioletred",
        "orchid", "darkorchid", "mediumorchid", "thistle", "lightsteelblue", "ghostwhite", "aliceblue", "honeydew",
        "floralwhite", "linen", "oldlace", "antiquewhite", "bisque", "blanchedalmond", "papayawhip", "moccasin",
        "navajowhite", "mistyrose", "seashell", "snow", "whitesmoke", "gainsboro", "lightgray", "darkgray", "dimgray"
    ]
    return random.choice(colors)

def pseudonymise_nok(nok):
    # For a next-of-kin dictionary, pseudonymise the name fields and mask the phone.
    return {
        "firstName": pseudonymise_name(nok.get("firstName", "")),
        "lastName": pseudonymise_name(nok.get("lastName", "")),
        "relationship": nok.get("relationship", ""),
        "phone": masked_phone_number(nok.get("phone", "")) if nok.get("phone") else ""
    }

def masked_phone_number(number):
    if number and isinstance(number, str) and len(number) >= 3:
        return "XXXXX" + number[-3:]
    return number

def masked_email(email):
    # Turns example@gmail.com into exa****@gmail.com
    if "@" in email:
        symbol = "*"
        parts = email.split("@")
        hidden = parts[0][:3] + (symbol * (len(parts[0]) - 3))
        return hidden + "@" + parts[1]
    return email

def pseudo_age(age):
    try:
        age_int = int(age)
        rounded = 5 * round(age_int / 5)
        return str(rounded)
    except Exception:
        return age

def masked_nric(nric):
    symbol = "X"
    if nric and len(nric) > 5:
        return nric[0] + symbol*4 + nric[5:]
    return nric

def masked_birth(dateOfBirth):
    # For a date string "YYYY-MM-DD", mask parts of it, e.g. "1953-01-08" becomes "19XX-X1-X8"
    symbol = "X"
    try:
        parts = dateOfBirth.split("-")
        if len(parts) == 3:
            return parts[0][:2] + symbol*2 + "-" + symbol + parts[1][1] + "-" + symbol + parts[2][1]
        return dateOfBirth
    except Exception:
        return dateOfBirth

def pseudonymise_address(address):
    return "masked-address"

def pseudonymise_value(key, value):
    """
    Personally Identifiable Info Keywords: [
        "email", "nric", "dob",
        "birth", "phone", "mobile",
        "age", "first", "last" 
        "name", "address"
    ]
    """
    lkey = key.lower()
    if isinstance(value, str):
        if "email" in lkey:
            return masked_email(value)
        elif "nric" in lkey:
            return masked_nric(value)
        elif "dob" in lkey or "birth" in lkey:
            return masked_birth(value)
        elif "phone" in lkey or "mobile" in lkey:
            return masked_phone_number(value)
        elif "age" in lkey:
            return pseudo_age(value)
        elif "name" in lkey:
            return pseudonymise_name(value)
        elif "address" in lkey:
            return pseudonymise_address(value)
    return value

def process_pii(data):
    """
    Recursively process a dict or list. If a key contains any PII substring, its value is masked.
    Special handling is provided for nested structures such as nokContact.
    """
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            if isinstance(value, dict):
                if key.lower() == "nokcontact":
                    new_dict[key] = pseudonymise_nok(value)
                else:
                    new_dict[key] = process_pii(value)
            elif isinstance(value, list):
                new_dict[key] = [process_pii(item) if isinstance(item, (dict, list)) else item for item in value]
            else:
                new_dict[key] = pseudonymise_value(key, value)
        return new_dict
    elif isinstance(data, list):
        return [process_pii(item) for item in data]
    else:
        return data

@app.route('/pseudonymise', methods=['POST'])
def pseudonymise_service():
    try:
        data = request.get_json()
        """
        Takes in 
        {
        "donorid-1234": {
                "firstName": "isaiah",
                "lastName": "chia",
                "age": "72",
                "datetimeOfDeath": "2069-01-01T24:12:34+00:00",
                "gender": "Male",
                "bloodType": "O+",
                "organs": ["organId1", "organId2", "organId3"],
                "medicalHistory": [],
                "allergies": ["nuts", "GPD", "aspirin"],
                "nokContact": {
                    "firstName": "First name of the patient.",
                    "lastName": "Last name of the patient.",
                    "relationship": "Spouse",
                    "phone": "54326789"
                },
                "dateOfBirth": "1953-01-08"
        }
        }
        """
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Assume the JSON contains a single record keyed by an ID.
        record_id, record_data = list(data.items())[0]

        # Process the data to pseudonymise/mask PII fields.
        masked_data = process_pii(record_data)
        # Add the required ID field to the masked data.
        masked_data["donorId"] = record_id

        # Build the Personal Data block from the original data.
        personal_data = {
            "personId": record_id,
            "firstName": record_data.get("firstName", ""),
            "lastName": record_data.get("lastName", ""),
            "dateOfBirth": record_data.get("dateOfBirth", ""),
            "nokContact": record_data.get("nokContact", {})
        }

        # Return a JSON with two blocks: one for the masked donor data (keyed under "person")
        # and one for the personal data (keyed under "personalData").
        response = {
            "maskedData": { record_id: masked_data },
            "personalData": personal_data
        }
        return jsonify(response), 200
    except Exception as e:
        record_id, record_data = list(data.items())[0]
        print("Error: {}".format(str(e)))
        return jsonify(
            {
                "code": 500,
                "data": {
                    "personId": record_id
                },
                "message": "An error occurred while updating the donor information. " + str(e)
            }
        ), 500
"""
returns
{
    "maskedData": {
        "donorid-1234": {
            "age": "70",
            "allergies": [
                "nuts",
                "GPD",
                "aspirin"
            ],
            "bloodType": "O+",
            "dateOfBirth": "19XX-X1-X8",
            "datetimeOfDeath": "2069-01-01T24:12:34+00:00",
            "donorId": "donorid-1234",
            "firstName": "wheat",
            "gender": "Male",
            "lastName": "denim",
            "medicalHistory": [],
            "nokContact": {
                "firstName": "darkolivegreen",
                "lastName": "gainsboro",
                "phone": "XXXXX789",
                "relationship": "Spouse"
            },
            "organs": [
                "organId1",
                "organId2",
                "organId3"
            ]
        }
    },
    "personalData": {
        "dateOfBirth": "1953-01-08",
        "firstName": "isaiah",
        "lastName": "chia",
        "nokContact": {
            "firstName": "First name of the patient.",
            "lastName": "Last name of the patient.",
            "phone": "54326789",
            "relationship": "Spouse"
        },
        "personId": "donorid-1234"
    }
}
"""
if __name__ == '__main__':
    print("This is flask for " + os.path.basename(__file__) + ": manage pseudonym ...")
    app.run(host='0.0.0.0', port=5006, debug=True)