# -*- coding: utf-8 -*-

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


class ResourceBase(Resource):
    def options(self, *args, **kwargs):
        return {'result': True}


class User(ResourceBase):
    model = models.User

    def get(self):
        if not user_is_logged():
            return {'result': 'NOT AUHTORIZED'}, 401
        return g.user.to_dict()

    def post(self):
        try:
            g.user = self.model.create_user(request.json)
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
            return self.model.get(g.user.id).get_debt(debt_id).to_dict()
        return self.model.get(g.user.id).debts_resume()

    def post(self):
        if not user_is_logged():
            return {'result': 'NOT AUHTORIZED'}, 401
        try:
            debt = self.model.get(g.user.id).add_debt(request.json)
            return debt.to_dict()
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
