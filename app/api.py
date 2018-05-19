# -*- coding: utf-8 -*-

from flask_restful import Api


def create_api(app):
    from app import resources
    api = Api(app)
    api.add_resource(resources.LoginResource, '/api/login')
    api.add_resource(resources.MeResource, '/api/me')
    api.add_resource(resources.UserDebtsResource, '/api/me/debts', '/api/me/debts/<int:debt_id>')
    api.add_resource(resources.UserPaymentsResource, '/api/me/payments', '/api/me/payments/<int:payment_id>')
