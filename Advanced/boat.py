from google.cloud import datastore
from flask import Blueprint, request, Response, make_response
from json2html import *
from validation import *
import json

client = datastore.Client()

bp = Blueprint('boat', __name__, url_prefix='/boats')

# create a new boat with name, type and length passed as parameters
def add_boat(boat_name, boat_type, boat_length):
    new_boat = datastore.Entity(key=client.key('Boat'))
    new_boat.update({
        'name': boat_name,
        'type': boat_type,
        'length': boat_length,
    })
    client.put(new_boat)
    return new_boat

# get an existing boat with given boat id
def get_boat(boat_id, base_url):
    boat_key = client.key('Boat', int(boat_id))
    result = client.get(key=boat_key)
    if result is not None:
        result["id"] = boat_id
        result["self"] = base_url
    return result

# modify an existing boat with name, type and length passed as parameters
def edit_boat(content, boat_id):
    boat_key = client.key('Boat', int(boat_id))
    boat = client.get(key=boat_key)
    if boat is not None:
        if 'name' in content:
            boat_name = content["name"]
        else:
            boat_name = boat["name"]
        if 'type' in content:
            boat_type = content["type"]
        else:
            boat_type = boat["type"]
        if 'length' in content:
            boat_length = int(content["length"])
        else:
            boat_length = boat["length"]
        boat.update({
            'name': boat_name,
            'type': boat_type,
            'length': boat_length
        })
        client.put(boat)
    return boat

# delete boat and remove it from loads assigned to it
def delete_boat(boat_id):
    boat_key = client.key('Boat', int(boat_id))
    result = client.get(key=boat_key)
    if result is not None:
        client.delete(boat_key)
        return 204
    else:
        return 404

# create a new boat via POST or view all boats via GET
@ bp.route('', methods=['POST', 'PUT', 'DELETE'])
def manage_boats():
    # create new boat
    if request.method == 'POST':
        if 'application/json' not in request.accept_mimetypes:
            error_msg = {"Error": "Only JSON is supported as returned content type"}
            return (error_msg, 406)
        request_content = json.loads(request.data) or {}
        if 'name' not in request_content or 'type' not in request_content or 'length' not in request_content:
            error_msg = {"Error": "The request object is missing at least one of the required attributes"}
            return (error_msg, 400)
        if not content_validation(request_content):
            error_msg = {"Error": "The request had invalid content"}
            return (error_msg, 400)
        if check_name_exist(request_content["name"]):
            error_msg = {"Error": "The name of boat is not available"}
            return (error_msg, 403)
        new_boat = add_boat(request_content["name"], request_content["type"], int(request_content["length"]))
        boat_id = str(new_boat.key.id)
        new_boat["id"] = boat_id
        new_boat["self"] = request.base_url + '/' + boat_id
        return Response(json.dumps(new_boat), status=201, mimetype='application/json')

    # invalid action - edit all boats
    elif request.method == 'PUT':
        error_msg = {"Error": "Editing all boats is not allowed"}
        return (error_msg, 405)

    # invalid action - delete all boats
    elif request.method == 'DELETE':
        error_msg = {"Error": "Deleting all boats is not allowed"}
        return (error_msg, 405)
    else:
        return 'Method not recogonized'

# view or delete an existing boat, return 404 if boat not exists
@bp.route('/<boat_id>', methods=['GET', 'DELETE'])
def boat_get_delete(boat_id):
    # get the boat
    if request.method == 'GET':
        if 'application/json' not in request.accept_mimetypes and 'text/html' not in request.accept_mimetypes:
            error_msg = {"Error": "Only JSON and HTML are supported as returned content type"}
            return (error_msg, 406)
        boat = get_boat(boat_id, request.base_url)
        if boat is None:
            error_msg = {"Error": "No boat with this boat_id exists"}
            return (error_msg, 404)
        if 'text/html' in request.accept_mimetypes:
            res = make_response(json2html.convert(json=json.dumps(boat)))
            res.headers.set('Content-Type', 'text/html')
            res.status_code = 200
            return res
        else:
            return Response(json.dumps(boat), status=200, mimetype='application/json')
    # delete the boat
    elif request.method == 'DELETE':
        status = delete_boat(boat_id)
        if status == 404:
            error_msg = {"Error":  "No boat with this boat_id exists"}
            return (error_msg, 404)
        elif status == 204:
            return ('', 204)
    else:
        return 'Method not recogonized'


# Fully or Partially update an existing boat, return 404 if boat not exists
@bp.route('/<boat_id>', methods=['PUT', 'PATCH'])
def boat_edit(boat_id):
    request_content = json.loads(request.data) or {}
    if 'application/json'  not in request.accept_mimetypes:
        error_msg = {"Error": "Only JSON is supported as returned content type"}
        return (error_msg, 406)
    if 'id' in request_content:
        error_message = {"Error": "Updating ID is not allowed"}
        return (error_message, 403)
    # Fully edit the boat
    if request.method == 'PUT':
        if 'name' not in request_content or 'type' not in request_content or 'length' not in request_content:
            error_message = {"Error": "The request object is missing at least one of the required attributes"}
            return (error_message, 400)
        if not content_validation(request_content):
            error_msg = {"Error": "The request had invalid content"}
            return (error_msg, 400)
        if name_unavailable(request_content["name"], boat_id):
            error_msg = {"Error": "The name of boat is not available"}
            return (error_msg, 403)
        updated_boat = edit_boat(request_content, boat_id)
        if updated_boat is None:
            error_message = {"Error": "No boat with this boat_id exists"}
            return (error_message, 404)
        updated_url = request.base_url
        response = make_response('')
        response.headers.set('Location', updated_url)
        response.status_code = 303
        return response

    # partially edit the boat:
    elif request.method == 'PATCH':
        request_content = json.loads(request.data) or {}
        if 'name' not in request_content and 'type' not in request_content and 'length' not in request_content:
            error_message = {"Error": "The request object needs at least one of the attributes"}
            return (error_message, 400)
        if not content_validation(request_content):
            error_msg = {"Error": "The request had invalid content"}
            return (error_msg, 400)
        if 'name' in request_content and name_unavailable(request_content["name"], boat_id):
            error_msg = {"Error": "The name of boat is not available"}
            return (error_msg, 403)
        updated_boat = edit_boat(request_content, boat_id)
        if updated_boat is None:
            error_message = {"Error": "No boat with this boat_id exists"}
            return (error_message, 404)
        updated_boat["id"] = boat_id
        updated_boat["self"] = request.base_url
        return Response(json.dumps(updated_boat), status=200, mimetype='application/json')
    else:
        return 'Method not recogonized'

# main function
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)



