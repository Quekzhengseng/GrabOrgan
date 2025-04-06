from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from os import environ
import os
from azure.communication.email import EmailClient
import re

app = Flask(__name__)
CORS(app)

CONNECTION_STRING = os.environ.get("AZURE_CONNECTION_STRING") or "null"

def get_sender_address():
    """
    Dynamically generate a sender address based on the connection string
    """
    try:
        # Extract the domain from the connection string endpoint
        endpoint = [part for part in CONNECTION_STRING.split(";") if part.startswith("endpoint=")][0]
        domain = re.search(r'//([^.]+)', endpoint)
        if domain:
            return f"DoNotReply@{domain.group(1)}.communication.azure.com"
    except Exception as e:
        print(f"Error generating sender address: {e}")
    
    # Fallback to a default sender address
    return "DoNotReply@azurecomm.net"

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"code": 200, "status": "ok"}), 200

@app.route("/email", methods=["POST"])
def send_email():
    try:
        message = request.get_json()
        print("Received email request:", message)
        
        connection_string = CONNECTION_STRING
        if connection_string == "null" or not connection_string:
            print("ERROR: No valid Azure connection string provided")
            return jsonify({"code": 500, "message": "Azure connection string not configured"}), 500
        
        try:
            client = EmailClient.from_connection_string(connection_string)
            print("Email client created successfully")
        except Exception as client_error:
            print(f"Detailed client creation error: {str(client_error)}")
            print(f"Error type: {type(client_error)}")
            return jsonify({"code": 500, "message": f"Failed to create email client: {str(client_error)}"}), 500
        
        try:
            # Validate message structure
            if not all(key in message for key in ['recipients', 'content']):
                print("Invalid message structure")
                return jsonify({"code": 400, "message": "Invalid email message structure"}), 400
            
            # Use dynamically generated sender address if not provided
            if 'senderAddress' not in message or not message['senderAddress']:
                message['senderAddress'] = get_sender_address()
            
            # Validate recipients
            if not message['recipients'].get('to') or not message['recipients']['to']:
                print("No recipients specified")
                return jsonify({"code": 400, "message": "No recipients specified"}), 400
            
            # Validate content
            if not message['content'].get('subject') or not message['content'].get('plainText'):
                print("Missing subject or plain text content")
                return jsonify({"code": 400, "message": "Missing email subject or body"}), 400

            # Send email
            poller = client.begin_send(message)
            result = poller.result()
            print("Message sent successfully:", result.get("id", "No ID provided"))
            return jsonify({
                "code": 200, 
                "message": "Email sent successfully",
                "details": result
            }), 200
        
        except Exception as send_error:
            print(f"Detailed send error: {str(send_error)}")
            print(f"Error type: {type(send_error)}")
            print(f"Full message sent: {message}")
            return jsonify({
                "code": 500, 
                "message": f"Failed to send email: {str(send_error)}",
                "error_type": str(type(send_error))
            }), 500
    
    except Exception as ex:
        print(f"Unexpected error processing email request: {str(ex)}")
        return jsonify({
            "code": 500, 
            "message": f"Unexpected error: {str(ex)}"
        }), 500

if __name__ == '__main__':
    print("This is flask for " + os.path.basename(__file__) + ": manage azure emails ...")
    app.run(host='0.0.0.0', port=5014, debug=True)