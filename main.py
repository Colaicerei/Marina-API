# Assignment 3 - Build a Restful API
# CS493 Cloud Development Spring 2020
# Author: Chen Zou

from google.cloud import datastore
from flask import Flask, request, Response, jsonify, abort
import json

app = Flask(__name__)
client = datastore.Client()

def get_all_boats(base_url):
    query = client.query(kind='Boat')
    results = list(query.fetch())
    for e in results:
        e["id"] = e.key.id
        e["self"] = base_url + '/' + str(e.key.id)
    return results

def add_boat(boat_name, boat_type, boat_length):
    new_boat = datastore.Entity(key=client.key('Boat'))
    new_boat.update({
        'name': boat_name,
        'type': boat_type,
        'length': boat_length
    })
    client.put(new_boat)
    return new_boat

def get_boat(boat_id, base_url):
    boat_key = client.key('Boat', int(boat_id))
    result = client.get(key=boat_key)
    if result is not None:
        result["id"] = boat_id
        result["self"] = base_url + '/' + str(boat_id)
    return result

def edit_boat(boat_name, boat_type, boat_length, boat_id):
    boat_key = client.key('Boat', int(boat_id))
    boat = client.get(key=boat_key)
    if boat is not None:
        boat.update({
            'name': boat_name,
            'type': boat_type,
            'length': boat_length
        })
        client.put(boat)
    return boat

def remove_boat(boat_id):
    boat_key = client.key('Boat', int(boat_id))
    result = client.get(key=boat_key)
    if result is not None:
        client.delete(boat_key)
        return 204
    else:
        return 404


@app.route('/')
def index():
    return "Please navigate to /boats or /slips to use this API"\

@ app.route('/boats', methods=['POST', 'GET'])
def boat_list_add():
    if request.method == 'POST':
        content = json.loads(request.data) or {}
        if 'name' not in content or 'type' not in content or 'length' not in content:
            error_message = {"Error": "The request object is missing at least one of the required attributes"}
            return (error_message, 400)
        new_boat = add_boat(content["name"], content["type"], int(content["length"]))
        boat_id = new_boat.key.id
        new_boat["id"] = boat_id
        new_boat["self"] = request.base_url + '/' + str(boat_id)
        return Response(json.dumps(new_boat), status=201, mimetype='application/json')
    elif request.method == 'GET':
        boat_list = get_all_boats(request.base_url)
        return Response(json.dumps(boat_list), status=200, mimetype='application/json')
    else:
        return 'Method not recogonized'

@app.route('/boats/<boat_id>', methods=['GET', 'PATCH', 'DELETE'])
def boat_get_edit(boat_id):
    if request.method == 'GET':
        boat = get_boat(boat_id, request.base_url)
        if boat is None:
            error_message = {"Error": "No boat with this boat_id exists"}
            return (error_message, 404)
        return Response(json.dumps(boat), status=200, mimetype='application/json')
    if request.method == 'PATCH':
        content = json.loads(request.data) or {}
        if 'name' not in content or 'type' not in content or 'length' not in content:
            error_message = {"Error": "The request object is missing at least one of the required attributes"}
            return (error_message, 400)
        boat = edit_boat(content["name"], content["type"], int(content["length"]), boat_id)
        if boat is None:
            error_message = {"Error": "No boat with this boat_id exists"}
            return (error_message, 404)
        return Response(json.dumps(boat), status=200, mimetype='application/json')

    elif request.method == 'DELETE':
        status = remove_boat(boat_id)
        if status == 404:
            error_message = {"Error":  "No boat with this boat_id exists"}
            return (error_message, 404)
        elif status == 204:
            return ('', 204)
    else:
        return 'Method not recogonized'

# @app.route('/slips/<slip_id>/<boat_id>', methods =['PUT', 'DELETE'])
# def

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)