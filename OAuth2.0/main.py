import json
from flask import Flask, session, render_template, request, redirect, url_for
import requests
import secrets


app = Flask(__name__)

CLIENT_ID = '793207193577-b0m59mshitdvarg41a6q8e3ofl2sh14m.apps.googleusercontent.com'
CLIENT_SECRET = 'iOr-aGJifs75GOvIQkCVx1aa'
SCOPE = 'profile email openid'
REQUEST_URL = "https://people.googleapis.com/v1/people/me?personFields=names,emailAddresses"
REDIRECT_URI = 'http://localhost:8080/auth'

# post auth code to server to get credentials including access token
def get_credentials(auth_code):
    data = {'code': auth_code,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code'}
    response = requests.post('https://oauth2.googleapis.com/token', data=data)
    return response.json()


@app.route('/')
def index():
        return render_template('welcome.html', error_message=request.args.get('error_message',''))


@app.route('/auth')
def auth():
    if 'code' not in request.args or 'state' not in request.args:
        session['state'] = secrets.token_urlsafe(16)
        print('generated state is: ', session['state'])
        auth_uri = ('https://accounts.google.com/o/oauth2/v2/auth?response_type=code'
                '&client_id={}&redirect_uri={}&scope={}&state={}').format(CLIENT_ID, REDIRECT_URI, SCOPE, session['state'])
        return redirect(auth_uri)
    if request.args.get('state') != session['state']:
        print("returned state is: ", request.args.get('state'))
        return redirect(url_for('index',error_message='State value mismatch, please try again'))
    else:
        auth_code = request.args.get('code')
        credentials = get_credentials(auth_code)
        if 'access_token' not in credentials:
            return redirect(url_for('index', error_message='Authorization failed, please try again'))
        if credentials['expires_in'] <= 0:
            return redirect(url_for('index', error_message='Token expired, please try again'))
        session['credentials'] = credentials
        return redirect(url_for('user_info'))

@app.route('/user_info')
def user_info():
    credentials = session['credentials']
    headers = {'Authorization': 'Bearer {}'.format(credentials['access_token'])}
    data = requests.get(REQUEST_URL, headers=headers)
    names = data.json()['names'][0]
    return render_template('user_info.html',names = names, state=session['state'])


if __name__ == '__main__':
  import uuid
  app.secret_key = str(uuid.uuid4())
  app.run(host='127.0.0.1', port=8080, debug=True)



