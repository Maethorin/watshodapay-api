import os
from datetime import timedelta

from flask import Flask, request, g
from flask.ext.sqlalchemy import SQLAlchemy

from app import database

web_app = Flask(__name__)
web_app.config.from_object(os.environ['APP_SETTINGS'])
database.AppRepository.db = SQLAlchemy(web_app)


@web_app.after_request
def add_header(req):
    req.headers['Cache-Control'] = "no-cache, no-store, must-revalidate"
    req.headers['Pragma'] = 'no-cache'
    req.headers['Expires'] = '0'
    req.headers['Access-Control-Allow-Origin'] = 'http://localhost:3100'
    req.headers['Access-Control-Allow-Credentials'] = 'true'
    req.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,Set-Cookie,XSRF-TOKEN'
    req.headers['Access-Control-Expose-Headers'] = 'Content-Type,Authorization,Set-Cookie,XSRF-TOKEN'
    req.headers['Access-Control-Allow-Methods'] = ','.join(['GET', 'PUT', 'POST', 'DELETE', 'OPTIONS'])
    req.headers['Access-Control-Max-Age'] = 21600
    return req


@web_app.before_request
def before_request():
    from app import models
    token = request.headers.get('XSRF-TOKEN', None)
    user = None
    if token:
        user = models.User.check_auth_token(token)
    g.user = user


@web_app.after_request
def after_request(resp):
    user = g.get('user', None)
    if user is not None:
        token = user.generate_auth_token()
        resp.headers['XSRF-TOKEN'] = token.decode('ascii')
    return resp


def run():
    web_app.run(host='0.0.0.0', port=5000, debug=True)
