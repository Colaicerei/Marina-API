import json
import flask
import requests


app = flask.Flask(__name__)

CLIENT_ID = '793207193577-b0m59mshitdvarg41a6q8e3ofl2sh14m.apps.googleusercontent.com'
CLIENT_SECRET = 'iOr-aGJifs75GOvIQkCVx1aa'
SCOPE = 'profile email openid'
REQUEST_URL = "https://people.googleapis.com/v1/people/me?personFields=names,emailAddresses"
REDIRECT_URI = 'http://localhost:8080/user_info'


@app.route('/')
def index():
  if 'credentials' not in flask.session:
    return flask.redirect(flask.url_for('user_info'))
  credentials = json.loads(flask.session['credentials'])
  if credentials['expires_in'] <= 0:
    return flask.redirect(flask.url_for('user_info'))
  else:
    headers = {'Authorization': 'Bearer {}'.format(credentials['access_token'])}
    r = requests.get(REQUEST_URL, headers=headers)
    return r.text


@app.route('/user_info')
def user_info():
  if 'code' not in flask.request.args:
    auth_uri = ('https://accounts.google.com/o/oauth2/v2/auth?response_type=code'
                '&client_id={}&redirect_uri={}&scope={}').format(CLIENT_ID, REDIRECT_URI, SCOPE)
    return flask.redirect(auth_uri)
  else:
    auth_code = flask.request.args.get('code')
    data = {'code': auth_code,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code'}
    r = requests.post('https://oauth2.googleapis.com/token', data=data)
    flask.session['credentials'] = r.text
    return flask.redirect(flask.url_for('index'))


if __name__ == '__main__':
  import uuid
  app.secret_key = str(uuid.uuid4())
  app.run(host='127.0.0.1', port=8080, debug=True)



