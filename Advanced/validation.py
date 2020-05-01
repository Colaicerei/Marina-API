from google.cloud import datastore
client = datastore.Client()

# check if the input is a valid integer
def validate_int(input_string):
    try:
        int(input_string)
        return True
    except ValueError:
        return False

# check if the type contains all valid characters and within allowed length
def validate_name(input_string):
    return True

# check if name already exists
def check_name_exist(name):
    query = client.query(kind='Boat')
    results = list(query.fetch())
    for e in results:
        if e["name"] == name:
            return True
    return False

def content_validation(content):
    valid = True
    if 'name' in content:
        valid = validate_name(content["name"])
    if 'type' in content:
        valid = validate_name(content["type"])
    if 'length' in content:
        valid = validate_int(content["length"])
    return valid




