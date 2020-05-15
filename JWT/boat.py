from google.cloud import datastore
from flask import Blueprint, request, Response, make_response
from requests_oauthlib import OAuth2Session
import json
from google.oauth2 import id_token
from google.auth import crypt
from google.auth import jwt
from google.auth.transport import requests

client = datastore.Client()

bp = Blueprint('boat', __name__, url_prefix='/boats')

#client_id = '1026701465259-a0p8dvblmmvebfvnfj0gu222hb2osrq4.apps.googleusercontent.com'
client_id = '977494860444-rcg8gihn0ltj4gktplao0j2k551ilu4b.apps.googleusercontent.com'
#client_secret = 'cGgwAwQnrj3dGmvwJSyHhG7G'
client_secret = 'whK4cm9sarWhvsyBAR7romAK'

# get all existing boats
def get_all_boats(request):
    query = client.query(kind='Boat')
    q_limit = int(request.args.get('limit', '10'))
    q_offset = int(request.args.get('offset', '0'))
    g_iterator = query.fetch(limit=q_limit, offset=q_offset)
    pages = g_iterator.pages
    results = list(next(pages))
    if g_iterator.next_page_token:
        next_offset = q_offset + q_limit
        next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
    else:
        next_url = None
    for e in results:
        e["id"] = str(e.key.id)
    output = {"boats": results}
    if next_url:
        output["next"] = next_url
    return output

# create a new boat with name, type and length passed as parameters
def add_boat(boat_name, boat_type, boat_length, owner_id):
    new_boat = datastore.Entity(key=client.key('Boat'))
    new_boat.update({
        'name': boat_name,
        'type': boat_type,
        'length': boat_length,
        'owner': owner_id
    })
    client.put(new_boat)
    return new_boat

# delete boat and remove it from loads assigned to it
def delete_boat(boat_id, owner_id):
    boat_key = client.key('Boat', int(boat_id))
    result = client.get(key=boat_key)
    if result is not None:
        if result['owner'] != owner_id:
            error_msg = {"Error": "The boat is owned by someone else and cannot be deleted"}
            return (error_msg, 403)
        client.delete(boat_key)
        return ('', 204)
    else:
        error_msg = {"Error": "No boat with this boat_id exists"}
        return (error_msg, 403)

def get_owner_id(request_headers):
    if 'Authorization' not in request_headers:
        error_msg = {"Error": "Missing JWT"}
        return (error_msg, 401)
    elif request_headers['Authorization'][:6] != 'Bearer':
        error_msg = {"Error": "Invalid JWT"}
        return (error_msg, 401)
    else:
        jwt = request.headers['Authorization'][7:]
    req = requests.Request()
    try:
        id_info = id_token.verify_oauth2_token(
            jwt, req, client_id)
    except ValueError:
        error_msg = {"Error": "Invalid JWT"}
        return (error_msg, 401)
    if id_info['iss'] != 'accounts.google.com':
        raise ValueError('Wrong issuer.')
    print(id_info['sub'])
    return id_info['sub']

# create a new boat via POST or view all boats via GET
@ bp.route('', methods=['POST', 'GET'])
def manage_boats():
    # create new boat
    if request.method == 'POST':
        request_content = json.loads(request.data) or {}
        result = get_owner_id(request.headers)
        if isinstance(result, tuple):
            return result
        owner_id = result
        new_boat = add_boat(request_content["name"], request_content["type"], int(request_content["length"]), owner_id)
        boat_id = str(new_boat.key.id)
        new_boat["id"] = boat_id
        return Response(json.dumps(new_boat), status=201, mimetype='application/json')
    elif request.method == 'GET':
        boat_list = get_all_boats(request)
        return Response(json.dumps(boat_list), status=200, mimetype='application/json')
    else:
        return 'Method not recogonized'


# delete an existing boat, return 404 if boat not exists
@bp.route('/<boat_id>', methods=['DELETE'])
def boat_delete(boat_id):
    # delete the boat
    if request.method == 'DELETE':
        result = get_owner_id(request.headers)
        if isinstance(result, tuple):
            return result
        owner_id = result
        response = delete_boat(boat_id, owner_id)
        return response
    else:
        return 'Method not recogonized'





