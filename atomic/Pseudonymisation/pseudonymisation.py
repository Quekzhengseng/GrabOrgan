from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from os import environ
import os


app = Flask(__name__)

CORS(app)


if __name__ == '__main__':
    print("This is flask for " + os.path.basename(__file__) + ": manage donors ...")
    app.run(host='0.0.0.0', port=5001, debug=True)