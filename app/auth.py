import os
from functools import wraps

from flask import request, make_response


def extract_auth_key(headers):
    try:
        authorization = headers["AUTHORIZATION"]
    except KeyError:
        return None
    if not authorization:
        return None
    authorization = authorization.split()
    if len(authorization) != 2:
        return None
    if 'AUTH-KEY' in authorization:
        return authorization[1]


def secured(function):
    @wraps(function)
    def decorated(*args, **kwargs):
        auth_key = extract_auth_key(request.headers)
        if not auth_key or auth_key != os.environ['AUTH_KEY']:
            headers = {'Content-Type': 'text/json; charset=utf-8'}
            return make_response('{"error": "NOT AUTHORIZED"}', 401, headers)
        return function(*args, **kwargs)
    return decorated
