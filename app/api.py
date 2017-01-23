# -*- coding: utf-8 -*-

from flask_restful import Api
import resources


def create_api(app):
    api = Api(app)
    api.add_resource(resources.Login, '/api/login')
    api.add_resource(resources.User, '/api/me')
    api.add_resource(resources.UserDebts, '/api/me/debts', '/api/me/debts/<int:debt_id>')
