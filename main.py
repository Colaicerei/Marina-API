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
        result["self"] = base_url
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

def delete_boat(boat_id):
    boat_key = client.key('Boat', int(boat_id))
    result = client.get(key=boat_key)
    if result is not None:
        client.delete(boat_key)
        return 204
    else:
        return 404

def get_all_slips(base_url):
    query = client.query(kind='Slip')
    results = list(query.fetch())
    for e in results:
        e["id"] = e.key.id
        e["self"] = base_url + '/' + str(e.key.id)
    return results

def add_slip(slip_number):
    new_slip = datastore.Entity(key=client.key('Slip'))
    new_slip.update({
        'number': slip_number,
        'current_boat': None
    })
    client.put(new_slip)
    return new_slip

def get_slip(slip_id, base_url):
    slip_key = client.key('Slip', int(slip_id))
    result = client.get(key=slip_key)
    if result is not None:
        result["id"] = slip_id
        result["self"] = base_url
    return result

def delete_slip(slip_id):
    slip_key = client.key('Slip', int(slip_id))
    result = client.get(key=slip_key)
    if result is not None:
        client.delete(slip_key)
        return 204
    else:
        return 404

# check is boat is assigned to a slip
def boat_assigned(boat_id):
    query = client.query(kind='Slip')
    slips = query.fetch()
    for slip in slips:
        if slip["current_boat"] == boat_id:
            return True
    return False

def add_boat_to_slip(slip_id, boat_id):
    slip_key = client.key('Slip', int(slip_id))
    boat_key = client.key('Boat', int(boat_id))
    slip = client.get(key=slip_key)
    boat = client.get(key=boat_key)
    # check if both slip and boat exist and slip is not occupied
    if slip is not None and boat is not None and slip["current_boat"] is None and not boat_assigned(boat_id):
        slip.update({
            "current_boat": boat_id
        })
        client.put(slip)
        return 204
    elif slip["current_boat"] is not None or boat_assigned(boat_id):
        return 403
    else:
        return 404

def remove_boat_from_slip(slip_id, boat_id):
    slip_key = client.key('Slip', int(slip_id))
    boat_key = client.key('Boat', int(boat_id))
    slip = client.get(key=slip_key)
    boat = client.get(key=boat_key)
    # check if both slip and boat exist and slip is occupied by boat
    if slip is not None and boat is not None and slip["current_boat"]==boat_id:
        slip.update({
            "current_boat": None
        })
        client.put(slip)
        return 204
    else:
        return 404

# main page
@app.route('/')
def index():
    return "Please navigate to /boats or /slips to use this API"\

# create a new boat via POST or view all boats via GET
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

# view, modify or delete an existing boat, return 404 if boat not exists
@app.route('/boats/<boat_id>', methods=['GET', 'PATCH', 'DELETE'])
def boat_get_edit(boat_id):
    if request.method == 'GET':
        boat = get_boat(boat_id, request.base_url)
        if boat is None:
            error_message = {"Error": "No boat with this boat_id exists"}
            return (error_message, 404)
        return Response(json.dumps(boat), status=200, mimetype='application/json')
    elif request.method == 'PATCH':
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
        status = delete_boat(boat_id)
        if status == 404:
            error_message = {"Error":  "No boat with this boat_id exists"}
            return (error_message, 404)
        elif status == 204:
            return ('', 204)
    else:
        return 'Method not recogonized'

# create a new slip via POST or view all boats via GET
@ app.route('/slips', methods=['POST', 'GET'])
def slip_list_add():
    if request.method == 'POST':
        content = json.loads(request.data) or {}
        if 'number' not in content:
            error_message = {"Error": "The request object is missing the required number"}
            return (error_message, 400)
        new_slip = add_slip(content["number"])
        slip_id = new_slip.key.id
        new_slip["id"] = slip_id
        new_slip["self"] = request.base_url + '/' + str(slip_id)
        return Response(json.dumps(new_slip), status=201, mimetype='application/json')
    elif request.method == 'GET':
        slip_list = get_all_slips(request.base_url)
        return Response(json.dumps(slip_list), status=200, mimetype='application/json')
    else:
        return 'Method not recogonized'

# view or delete an existing slip, return 404 if slip not exists
@app.route('/slips/<slip_id>', methods=['GET', 'DELETE'])
def slip_get_edit(slip_id):
    if request.method == 'GET':
        slip = get_slip(slip_id, request.base_url)
        if slip is None:
            error_message = {"Error": "No slip with this slip_id exists"}
            return (error_message, 404)
        return Response(json.dumps(slip), status=200, mimetype='application/json')
    elif request.method == 'DELETE':
        status = delete_slip(slip_id)
        if status == 404:
            error_message = {"Error":  "No slip with this slip_id exists"}
            return (error_message, 404)
        elif status == 204:
            return ('', 204)
    else:
        return 'Method not recogonized'

# add (arrival) or delete (departure) a boat to a slip
@app.route('/slips/<slip_id>/<boat_id>', methods=['PUT', 'DELETE'])
def slip_boat_edit(slip_id, boat_id):
    if request.method == 'PUT':
        status = add_boat_to_slip(slip_id, boat_id)
        if status == 403:
            error_message = {"Error": "The slip is not empty or boat is already assigned"}
            return (error_message, 403)
        elif status == 404:
            error_message = {"Error":  "The specified boat and/or slip don’t exist"}
            return (error_message, 404)
        elif status == 204:
            return ('', 204)
    elif request.method == 'DELETE':
        status = remove_boat_from_slip(slip_id, boat_id)
        if status == 404:
            error_message = {"Error":  "No boat with this boat_id is at the slip with this slip_id"}
            return (error_message, 404)
        elif status == 204:
            return ('', 204)
    else:
        return 'Method not recogonized'

# main function
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)