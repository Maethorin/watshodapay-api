import json

from flask import Response

from app.initialize import web_app, run
from app import api

api.create_api(web_app)


@web_app.route('/')
def root():
    return Response(json.dumps({'result': 'OK'}), content_type='application/json')
