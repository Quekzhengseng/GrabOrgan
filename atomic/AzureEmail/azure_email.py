from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from os import environ
import os
from azure.communication.email import EmailClient

app = Flask(__name__)


CORS(app)

CONNECTION_STRING = os.environ.get("AZURE_CONNECTION_STRING") or "null"

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"code": 200, "status": "ok"}), 200


@app.route("/email", methods=["POST"])
def send_email():
    try:
        connection_string = CONNECTION_STRING 
        client = EmailClient.from_connection_string(connection_string)

        message = {
            "senderAddress": "DoNotReply@c4de2af4-af42-4134-8003-492f444c8562.azurecomm.net",
            "recipients": {
                "to": [{"address": "isaidchia@gmail.com"}]
            },
            "content": {
                "subject": "Test Email",
                "plainText": "Hello world via email.",
                "html": """
				<html>
					<body>
						<h1>Hello world via email.</h1>
					</body>
				</html>"""
            },
            
        }

        poller = client.begin_send(message)
        result = poller.result()
        print("Message sent: ", result["id"])
        return jsonify({"code": 200, "message": "Email sent successfully"}), 200
    except Exception as ex:
        print(ex)
        return jsonify({"code": 500 , "message": "Error occured while sending email."}), 500
    


if __name__ == '__main__':
    print("This is flask for " + os.path.basename(__file__) + ": manage azure emails ...")
    app.run(host='0.0.0.0', port=5014, debug=True)