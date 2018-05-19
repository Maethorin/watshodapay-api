# -*- coding: utf-8 -*-

import os

from flask import Flask, g, request
from flask_sqlalchemy import SQLAlchemy

from app import config as config_module, api, database, auth, apm

config = config_module.get_config()

web_app = Flask(__name__)
web_app.config.from_object(config)
apm.create_monitor(web_app)

database.AppRepository.db = SQLAlchemy(web_app)

api.create_api(web_app)


@web_app.before_request
def before_request():
    token = request.headers.get('XSRF-TOKEN', None)
    authenticated = None
    user = None
    user_entity = None
    new_token = None
    if token:
        user, new_token, user_entity = auth.check_auth_token(token)
    if user and new_token:
        g.user = user
        g.current_token = new_token
        g.user_entity = user_entity
        authenticated = True
    g.authenticated = authenticated


@web_app.after_request
def add_cache_header(response):
    response.headers['Cache-Control'] = "no-cache, no-store, must-revalidate"
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@web_app.after_request
def add_access_control_header(response):
    """
    Add response headers for CORS
    """
    response.headers['Access-Control-Allow-Origin'] = "http://localhost:3100"
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,Set-Cookie,XSRF-TOKEN'
    response.headers['Access-Control-Expose-Headers'] = 'Content-Type,Authorization,Set-Cookie,XSRF-TOKEN'
    response.headers['Access-Control-Allow-Methods'] = ','.join(['GET', 'PUT', 'POST', 'DELETE', 'OPTIONS'])
    response.headers['Access-Control-Max-Age'] = 21600
    return response


@web_app.after_request
def add_token_header(response):
    user = g.get("user")
    if user is not None:
        token = g.current_token
        response.headers['XSRF-TOKEN'] = token
    return response


def run():
    web_app.run(host='0.0.0.0', port=int(os.environ.get('PORTA', 3666)), debug=True)
