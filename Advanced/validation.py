from google.cloud import datastore
client = datastore.Client()
import re

max_string_length = 20
min_string_length = 3
max_boat_length = 10000
min_boat_length = 2
allowed_characters = '^[a-zA-Z0-9]+( [a-zA-Z0-9]+)*$' #from stack overflow

# check if the input is a valid integer
def validate_length(input_length):
    try:
        length = int(input_length)
    except ValueError:
        print("not a valid int")
        return False
    if length < min_boat_length or length > max_boat_length:
        print("boat length out of range")
        return False
    return True

# check if the type contains all valid characters and within allowed length
def validate_string(input_string):
    if len(input_string) > max_string_length or len(input_string) < min_string_length:
        print("string length out of range")
        return False
    if not re.match(allowed_characters, input_string):
        print("the name or type can only allow numbers, alphabets and spaces in between")
        return False
    return True

# check if name already exists
def check_name_exist(name):
    query = client.query(kind='Boat')
    results = list(query.fetch())
    for e in results:
        if e["name"] == name:
            return True
    return False

# check if name already used by other boats
def name_unavailable(name, boat_id):
    query = client.query(kind='Boat')
    results = list(query.fetch())
    for e in results:
        print(e.id)
        if e["name"] == name and e.id != int(boat_id):
            return True
    return False

def content_validation(content):
    if 'name' in content:
        if not validate_string(content["name"]):
            return False
    if 'type' in content:
        if not validate_string(content["type"]):
            return False
    if 'length' in content:
        if not validate_length(content["length"]):
            return False
    return True




