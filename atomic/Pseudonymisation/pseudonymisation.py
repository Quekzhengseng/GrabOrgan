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
        return "T" + symbol*4 + nric[5:]
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

# List of substrings indicating PII fields.
pii_keywords = ["name", "age", "phone", "mobile", "dob", "birth", "address", "email", "nric", "number"]

def pseudonymise_value(key, value):
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
        elif "first" in lkey and "name" in lkey:
            return pseudonymise_name(value)
        elif "last" in lkey and "name" in lkey:
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
                # Special-case for known nested PII blocks like 'nokContact'
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
    data = request.get_json()
    # print("Received data:", data)
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # For simplicity, assume the JSON contains a single donor record keyed by an ID.
    donor_id, donor_data = list(data.items())[0]

    # Process the donor data to pseudonymise/mask PII fields.
    processed_data = process_pii(donor_data)

    # Return the data in the desired format.
    response = {
        donor_id: processed_data
    }
    return jsonify(response), 200

if __name__ == '__main__':
    print("This is flask for " + os.path.basename(__file__) + ": pseudonymise ...")
    app.run(host='0.0.0.0', port=5001, debug=True)