# -*- coding: utf-8 -*-

from flask_restful import Api
import resources


def create_api(app):
    api = Api(app)
    api.add_resource(resources.Login, '/login')
    api.add_resource(resources.User, '/me')
    api.add_resource(resources.UserDebts, '/me/debts', '/me/debts/<int:debt_id>')
