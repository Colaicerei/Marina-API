from google.cloud import datastore
from flask import Flask, request, Response, jsonify, session, render_template, redirect, url_for
from requests_oauthlib import OAuth2Session
import json
from google.oauth2 import id_token
from google.auth import crypt
from google.auth import jwt
from google.auth.transport import requests
from boat import *
import secrets

# This disables the requirement to use HTTPS so that you can test locally.
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
#app.register_blueprint(boat.bp)
client = datastore.Client()
app.secret_key = 'super secret 8888'

# These should be copied from an OAuth2 Credential section at
# https://console.cloud.google.com/apis/credentials
client_id = '1026701465259-a0p8dvblmmvebfvnfj0gu222hb2osrq4.apps.googleusercontent.com'
client_secret = 'cGgwAwQnrj3dGmvwJSyHhG7G'
redirect_uri = 'http://127.0.0.1:8080/oauth'
scope = 'openid https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email'
oauth = OAuth2Session(client_id, redirect_uri=redirect_uri,
                          scope=scope)

# This link will redirect users to begin the OAuth flow with Google
@app.route('/')
def index():
    if 'email' in session:
        return render_template('welcome.html', name=session['email'])
    return render_template('welcome.html', message=request.args.get('message', ''))

# This is where users will be redirected back to and where you can collect
# the JWT for use in future requests
@app.route('/oauth')
def oauthroute():
    if 'code' not in request.args:
        #session['state'] = secrets.token_urlsafe(16)
        #print('generated state is: ', session['state'])
        authorization_url, state = oauth.authorization_url(
            'https://accounts.google.com/o/oauth2/v2/auth',
            # access_type and prompt are Google specific extra
            # parameters.
            access_type="offline", prompt="select_account")
        return redirect(authorization_url)
    else:
        token = oauth.fetch_token(
            'https://accounts.google.com/o/oauth2/token',
            authorization_response=request.url,
            client_secret=client_secret)
        #req = requests.Request()

        #id_info = id_token.verify_oauth2_token(
        #token['id_token'], req, client_id)
        if token['expires_in'] <= 0:
            return redirect(url_for('index', message='Error: Token expired, please try again'))
        session['jwt'] = token['id_token']

        req = requests.Request()
        try:
            id_info = id_token.verify_oauth2_token(
                session['jwt'], req, client_id)
        except ValueError:
            error = "Error: invalid JWT"
            return redirect(url_for('index', message=error))
        if id_info['iss'] != 'accounts.google.com':
            raise ValueError('Wrong issuer.')
        else:
            session['email'] = id_info['email']
        return redirect(url_for('user_info'))

@app.route('/user_info')
def user_info():
    return render_template('user_info.html',jwt = session['jwt'], email = session['email'])

@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('index',message='You are logged out'))

# create a new boat via POST or view all boats via GET
@ app.route('/boats', methods=['POST', 'GET'])
def manage_boats():
    # create new boat
    if request.method == 'POST':
        request_content = json.loads(request.data) or {}
        if 'Authorization' not in request.headers:
            error_msg = {"Error": "Missing JWT"}
            return (error_msg, 401)
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
        owner_id = id_info['sub']
        new_boat = add_boat(request_content["name"], request_content["type"], int(request_content["length"]), owner_id)
        boat_id = str(new_boat.key.id)
        new_boat["id"] = boat_id
        return Response(json.dumps(new_boat), status=201, mimetype='application/json')
    elif request.method == 'GET':
        boat_list = get_all_boats(request)
        return Response(json.dumps(boat_list), status=200, mimetype='application/json')
    else:
        return 'Method not recogonized'

# view all boats for given owner
@app.route('/owners/<owner_id>/boats', methods=['GET'])
def get_boats_by_owner(owner_id):
    # delete the boat
    if request.method == 'GET':
        if 'Authorization' not in request.headers:
            error_msg = {"Error": "Missing JWT"}
            return (error_msg, 401)
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
        owner = id_info['sub']
        if owner != owner_id:
            error_msg = {"Error": "JWT doesn't match the owner_id specified in the URL"}
            return (error_msg, 401)

        boats = get_owner_boats(owner)
        return Response(json.dumps(boats), status=200, mimetype='application/json')
    else:
        return 'Method not recogonized'

# delete an existing boat, return 404 if boat not exists
@app.route('/boats/<boat_id>', methods=['DELETE'])
def boat_delete(boat_id):
    # delete the boat
    if request.method == 'DELETE':
        if 'Authorization' not in request.headers:
            error_msg = {"Error": "Missing JWT"}
            return (error_msg, 401)
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
        owner_id = id_info['sub']
        response = delete_boat(boat_id, owner_id)
        return response
    else:
        return 'Method not recogonized'

@app.route('/verify-jwt')
def verify():
    req = requests.Request()

    id_info = id_token.verify_oauth2_token(
    request.args['jwt'], req, client_id)

    return repr(id_info) + "<br><br> the user is: " + id_info['email']


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)



