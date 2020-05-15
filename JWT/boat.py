from google.cloud import datastore
from flask import Blueprint, request, Response, make_response
from json2html import *
import json

client = datastore.Client()

#bp = Blueprint('boat', __name__, url_prefix='/boats')

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

# get all existing boats
def get_owner_boats(owner):
    query = client.query(kind='Boat')
    query.add_filter('owner', '=', owner)
    #query.order = ['-']
    results = list(query.fetch())
    for e in results:
        e["id"] = str(e.key.id)
    return results







