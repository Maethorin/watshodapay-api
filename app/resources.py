# -*- coding: utf-8 -*-

import re

from flask import request, g
from flask_restful import Resource, fields, marshal_with

import models


def user_is_logged(is_admin=False):
    user = getattr(g, 'user', None)
    if user is None:
        return False
    if is_admin:
        return user.is_admin
    return True


def camel_to_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def snake_to_camel(name):
    result = []
    for index, part in enumerate(name.split('_')):
        if index == 0:
            result.append(part.lower())
        else:
            result.append(part.capitalize())
    return ''.join(result)


class ResourceBase(Resource):
    def options(self, *args, **kwargs):
        return {'result': True}

    @property
    def payload(self):
        if request.json:
            return {camel_to_snake(key): value for key, value in request.json.iteritems()}
        if request.form:
            return {camel_to_snake(key): value for key, value in request.form.iteritems()}
        return {}

    def response(self, data_dict):
        return {snake_to_camel(key): value for key, value in data_dict.iteritems()}


class User(ResourceBase):
    model = models.User

    def get(self):
        if not user_is_logged():
            return {'result': 'NOT AUHTORIZED'}, 401
        return self.response(g.user.to_dict())

    def post(self):
        try:
            g.user = self.model.create_user(self.payload)
            return {'token': g.user.generate_auth_token(), 'userId': g.user.id}
        except KeyError as ex:
            return {'mensagemErro': u'Dados faltando: {}'.format(ex)}, 400
        except models.UserAlreadyExist as ex:
            return {'mensagemErro': u'{}'.format(ex)}, 400
        except Exception as ex:
            return {'mensagemErro': u'Ocorreu um erro e não pudemos gravar seus dados. Por favor, tente mais tarde.', 'ex': str(ex)}, 500


class UserDebts(ResourceBase):
    model = models.User

    def get(self, debt_id=None):
        if not user_is_logged():
            return {'result': 'NOT AUHTORIZED'}, 401
        if debt_id:
            return self.response(self.model.get(g.user.id).get_debt(debt_id).to_dict())
        return self.model.get(g.user.id).debts_resume()

    def post(self):
        if not user_is_logged():
            return {'result': 'NOT AUHTORIZED'}, 401
        try:
            debt = self.model.get(g.user.id).add_debt(self.payload)
            return self.response(debt.to_dict())
        except KeyError as ex:
            return {'mensagemErro': u'Dados faltando: {}'.format(ex)}, 400
        except Exception as ex:
            return {'mensagemErro': u'Ocorreu um erro e não pudemos criar o débito. Por favor, tente mais tarde.', 'ex': str(ex)}, 500


class Login(ResourceBase):
    model = models.User

    def delete(self):
        g.user = None

    def post(self):
        try:
            g.user = self.model.get_by_email(request.json['email'])
            if g.user.check_password(request.json['password']):
                return {'token': g.user.generate_auth_token()}
        except Exception:
            pass
        return {'resultado': 'NOT AUTHORIZED'}, 401
