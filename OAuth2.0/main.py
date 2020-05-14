import json
from flask import Flask, session, render_template, request, redirect, url_for
import requests
import secrets
#import uuid
#import logging

CLIENT_ID = '793207193577-b0m59mshitdvarg41a6q8e3ofl2sh14m.apps.googleusercontent.com'
CLIENT_SECRET = 'iOr-aGJifs75GOvIQkCVx1aa'
SCOPE = 'profile email openid'
REQUEST_URL = "https://people.googleapis.com/v1/people/me?personFields=names,emailAddresses"
REDIRECT_URI = 'https://hw6-zouch000.appspot.com/auth'

app = Flask(__name__)
app.secret_key = 'Super Secret Key'

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
    if 'name' in session:
        return render_template('welcome.html', name=session['name'])
    return render_template('welcome.html', message=request.args.get('message',''))


@app.route('/auth')
def auth():
    if 'code' not in request.args or 'state' not in request.args:
        session['state'] = secrets.token_urlsafe(16)
        #app.logger.info('Successful generated state')
        auth_uri = ('https://accounts.google.com/o/oauth2/v2/auth?response_type=code'
                '&client_id={}&redirect_uri={}&scope={}&state={}').format(CLIENT_ID, REDIRECT_URI, SCOPE, session['state'])
        return redirect(auth_uri)
    if request.args.get('state') != session['state']:
        #app.logger.error('State value mismatch')
        return redirect(url_for('index',message='Error: State value mismatch, please try again'))
    else:
        auth_code = request.args.get('code')
        #app.logger.info("Successful return of auth code")
        credentials = get_credentials(auth_code)
        if 'access_token' not in credentials:
            #app.logger.info('Unsuccessful return of credentials')
            return redirect(url_for('index', message='Error: Authorization failed, please try again'))
        if credentials['expires_in'] <= 0:
            return redirect(url_for('index', message='Error: Token expired, please try again'))
        session['credentials'] = credentials
        #app.logger.info('Successful return of credentials')
        return redirect(url_for('user_info'))

@app.route('/user_info')
def user_info():
    credentials = session['credentials']
    headers = {'Authorization': 'Bearer {}'.format(credentials['access_token'])}
    data = requests.get(REQUEST_URL, headers=headers)
    app.logger.info("Successful return of user profile")
    names = data.json()['names'][0]
    session['name'] = names['displayName']
    return render_template('user_info.html',names = names, state=session['state'])

@app.route('/logout')
def logout():
    session.pop('name', None)
    return redirect(url_for('index',message='You are logged out'))

if __name__ == '__main__':
    #logging.basicConfig(level=logging.INFO) #, filename='HW6.log')
    app.run(host='127.0.0.1', port=8080, debug=False)



