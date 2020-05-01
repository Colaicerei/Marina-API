from google.cloud import datastore
from flask import Flask, request, Response, jsonify, abort
import json
import boat

app = Flask(__name__)
app.register_blueprint(boat.bp)
client = datastore.Client()

# main page
@app.route('/')
def index():
    return "Please navigate to /boats to use this API"\

# main function
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)



