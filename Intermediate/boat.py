from google.cloud import datastore
from flask import Blueprint, request, Response, jsonify, abort
import json

client = datastore.Client()

bp = Blueprint('boat', __name__, url_prefix='/boats')

# get all existing boats
def get_all_boats(request):
    query = client.query(kind='Boat')
    q_limit = int(request.args.get('limit', '3'))
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
        e["self"] = request.base_url + '/' + str(e.key.id)
        if e['loads']:
            for l in e["loads"]:
                load_key = client.key("Load", int(l["id"]))
                load = client.get(key=load_key)
                if load is not None:
                    l["self"] = request.url_root + '/loads/' + str(load.id)
    output = {"boats": results}
    if next_url:
        output["next"] = next_url
    return output

# create a new boat with name, type and length passed as parameters
def add_boat(boat_name, boat_type, boat_length):
    new_boat = datastore.Entity(key=client.key('Boat'))
    new_boat.update({
        'name': boat_name,
        'type': boat_type,
        'length': boat_length,
        'loads': []
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
        loads = result["loads"]
        if loads:
            for l in loads:
                load_key = client.key("Load", int(l["id"]))
                load = client.get(key=load_key)
                if load is not None:
                    l["self"] = request.url_root + '/loads/' + str(load.id)
    return result

# delete boat and remove it from loads assigned to it
def delete_boat(boat_id):
    boat_key = client.key('Boat', int(boat_id))
    result = client.get(key=boat_key)
    if result is not None:
        for l in result['loads']:
            load_key = client.key('Load', int(l['id']))
            load = client.get(key=load_key)
            if load is not None:
                load.update({
                    "carrier": None
                })
                client.put(load)
        client.delete(boat_key)
        return 204
    else:
        return 404

# assign an existing load to an existing boat
def add_load_to_boat(host, load_id, boat_id):
    load_key = client.key('Load', int(load_id))
    boat_key = client.key('Boat', int(boat_id))
    load = client.get(key=load_key)
    boat = client.get(key=boat_key)
    # check if both load and boat exist and load is not occupied
    if load is None or boat is None:
        return 404
    # check if load has been assigned to another boat
    elif load['carrier'] is not None:
        return 403
    # update list of loads in boat
    load_brief = {'id':str(load.id)}
    boat['loads'].append(load_brief)
    client.put(boat)
    # update carrier information in load
    boat_brief = {'id': str(boat.id), 'name': boat['name']}
    # boat_brief.update({'self': host + '/boats/' + str(boat.id)})
    load.update({
        "carrier": boat_brief
    })
    client.put(load)
    return 204

# remove an existing load from the boat it is assigned to one
def remove_load_from_boat(load_id, boat_id):
    load_key = client.key('Load', int(load_id))
    boat_key = client.key('Boat', int(boat_id))
    load = client.get(key=load_key)
    boat = client.get(key=boat_key)
    # check if both load and boat exist and load is assigned to the boat
    if load is None or boat is None or load["carrier"] is None or str(load["carrier"]["id"])!=boat_id:
        return 404
    load.update({
        "carrier": None
    })
    client.put(load)
    for load in boat['loads']:
        print(load["id"])
        if load["id"] == load_id:
            boat['loads'].remove(load)
    client.put(boat)
    return 204


# create a new boat via POST or view all boats via GET
@ bp.route('', methods=['POST', 'GET'])
def boat_list_add():
    if request.method == 'POST':
        content = json.loads(request.data) or {}
        if 'name' not in content or 'type' not in content or 'length' not in content:
            error_message = {"Error": "The request object is missing at least one of the required attributes"}
            return (error_message, 400)
        new_boat = add_boat(content["name"], content["type"], int(content["length"]))
        boat_id = str(new_boat.key.id)
        new_boat["id"] = boat_id
        new_boat["self"] = request.base_url + '/' + boat_id
        return Response(json.dumps(new_boat), status=201, mimetype='application/json')
    elif request.method == 'GET':
        boat_list = get_all_boats(request)
        return Response(json.dumps(boat_list), status=200, mimetype='application/json')
    else:
        return 'Method not recogonized'

# view, modify or delete an existing boat, return 404 if boat not exists
@bp.route('/<boat_id>', methods=['GET', 'DELETE'])
def boat_get_edit(boat_id):
    if request.method == 'GET':
        boat = get_boat(boat_id, request.base_url)
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

# assign or un-assign a load to boat
@bp.route('/<boat_id>/<load_id>', methods=['PUT', 'DELETE'])
def manage_boat_load(load_id, boat_id):
    if request.method == 'PUT':
        status = add_load_to_boat(request.url_root, load_id, boat_id)
        if status == 403:
            error_message = {"Error": "The load has already been assigned to another boat"}
            return (error_message, 403)
        elif status == 404:
            error_message = {"Error":  "The specified boat and/or load don\u2019t exist"}
            return (error_message, 404)
        elif status == 204:
            return ('', 204)
    elif request.method == 'DELETE':
        status = remove_load_from_boat(load_id, boat_id)
        if status == 404:
            error_message = {"Error":  "No load with this load_id is at the boat with this boat_id"}
            return (error_message, 404)
        elif status == 204:
            return ('', 204)
    else:
        return 'Method not recogonized'

@bp.route('/<boat_id>/loads', methods=['GET'])
def get_loads_at_boat(boat_id):
    boat_key = client.key('Boat', int(boat_id))
    boat = client.get(key=boat_key)
    if boat is None:
        error_message = {"Error": "No boat with this boat_id exists"}
        return (error_message, 404)
    load_list  = []
    if 'loads' in boat.keys():
        #for l in boat['loads']:
        #    load_key = client.key('Load', int(l["id"]))
        #    load_list.append(load_key)
        #return json.dumps(client.get_multi(load_list))
        for l in boat['loads']:
            load_key = client.key('Load', int(l["id"]))
            load = client.get(key=load_key)
            load_list.append({
                'id': str(load.id),
                'weight': load['weight'],
                'content': load['content'],
                'delivery_date': load['delivery_date'],
                'self': request.url_root + '/loads/' + str(load.id)
            })
        return json.dumps(load_list)
    else:
        return json.dumps([])


# main function
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)



