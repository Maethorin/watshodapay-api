# -*- coding: utf-8 -*-

from functools import wraps
import re

from flask import request, g, Response
from flask_restful import Resource

from app import domain, apm


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        authenticated = getattr(g, 'authenticated', False)
        if not authenticated:
            return Response('{"result": "Not Authorized"}', 401, content_type='application/json')
        return f(*args, **kwargs)
    return decorated_function


def not_allowed(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return Response('{"result": "Method not allowed"}', 405, content_type='application/json')
    return decorated_function


class ResourceBase(Resource):
    http_methods_allowed = []
    entity = None

    def __init__(self):
        self.me = getattr(g, 'user_entity', None)
        if self.me is None and self.logged_user is not None:
            self.me = domain.User.create_with_logged(self.logged_user)

    @staticmethod
    def camel_to_snake(name):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    @staticmethod
    def snake_to_camel(name):
        result = []
        for index, part in enumerate(name.split('_')):
            if index == 0:
                result.append(part.lower())
            else:
                result.append(part.capitalize())
        return ''.join(result)

    def transform_key(self, data, method):
        if isinstance(data, dict):
            return {method(key): self.transform_key(value, method) for key, value in data.items()}
        if isinstance(data, list):
            for index, item in enumerate(data):
                if isinstance(item, dict):
                    data[index] = {method(key): self.transform_key(value, method) for key, value in item.items()}
        return data

    @property
    def payload(self):
        payload = {}
        if request.json:
            payload = self.transform_key(request.json, self.camel_to_snake)
        if request.form:
            payload = self.transform_key(request.form, self.camel_to_snake)
        if request.args:
            payload = self.transform_key(request.args, self.camel_to_snake)
        return payload

    @property
    def cookies(self):
        username = request.cookies.get('watshodapayUserName', None)
        token = request.cookies.get('watshodapayUserToken', 'null')
        return {'watshodapayUserName': username, 'watshodapayUserToken': token}

    @property
    def headers(self):
        return request.headers

    @property
    def logged_user(self):
        return getattr(g, 'user', None)

    def return_not_found(self, entity):
        return self.response({'result': 'Resource not found', 'entity': entity}), 404

    def return_not_allowed(self):
        return self.response({'result': 'Method not allowed'}), 405

    def return_bad_request(self, ex):
        return self.response({'result': 'Bad request', 'exception': ex.message}), 400

    def return_unexpected_error(self, ex):
        return self.response({'result': 'error', 'exception': ex.message}), 500

    def response(self, data_dict):
        return self.transform_key(data_dict, self.snake_to_camel)

    @login_required
    def get(self, **kwargs):
        if 'GET' not in self.http_methods_allowed:
            return self.return_not_allowed()

    @login_required
    def post(self, **kwargs):
        if 'POST' not in self.http_methods_allowed:
            return self.return_not_allowed()

    @login_required
    def put(self, **kwargs):
        if 'PUT' not in self.http_methods_allowed:
            return self.return_not_allowed()

    @login_required
    def delete(self, item_id):
        if 'DELETE' not in self.http_methods_allowed:
            return self.return_not_allowed()


class LoginResource(ResourceBase):
    http_methods_allowed = ['POST']
    entity = domain.User

    def post(self):
        try:
            user = self.entity.create_for_login(self.payload)
            if user.is_correct:
                g.user = user.as_dict()
                g.user_entity = user
                g.current_token = user.generate_auth_token()
                return {'logged': True}, 200
        except Exception:
            apm.monitor.capture_exception(exc_info=True)
            return {'result': 'Not Authorized'}, 401
        return {'result': 'Not Authorized'}, 401


class MeResource(ResourceBase):
    http_methods_allowed = ['GET', 'PUT', 'POST']
    entity = domain.User

    @login_required
    def get(self):
        try:
            if self.me is None:
                return self.return_not_found('Me')
            return self.response(self.me.as_dict())
        except Exception as ex:
            apm.monitor.capture_exception(exc_info=True)
            return self.return_unexpected_error(ex)

    @login_required
    def put(self):
        try:
            if self.me is None:
                return self.return_not_found('Me')
            self.me.update_me(self.payload)
            return self.response(self.me.as_dict())
        except Exception as ex:
            apm.monitor.capture_exception(exc_info=True)
            return self.return_unexpected_error(ex)

    def post(self):
        try:
            g.user = self.entity.create_new(self.payload)
            return self.response({'token': g.user.generate_auth_token(), 'user': self.me.as_dict()})
        except KeyError as ex:
            apm.monitor.capture_exception(exc_info=True)
            return self.return_bad_request(ex)
        except domain.AlreadyExist as ex:
            apm.monitor.capture_exception(exc_info=True)
            return self.return_bad_request(ex)
        except Exception as ex:
            apm.monitor.capture_exception(exc_info=True)
            return self.return_unexpected_error(ex)


class UserDebts(ResourceBase):
    @login_required
    def get(self, debt_id=None):
        super(UserDebts, self).get()
        if debt_id is None:
            return [self.response(debt.as_dict()) for debt in self.me.debts]
        try:
            debt = self.me.get_debt(debt_id)
            return self.response(debt.as_dict())
        except domain.NotExist:
            apm.monitor.capture_exception(exc_info=True)
            return self.return_not_found('UserDebt')

    @login_required
    def put(self, debt_id):
        super(UserDebts, self).put()
        try:
            return self.response(self.me.update_debt(debt_id, self.payload).as_dict())
        except domain.NotExist:
            apm.monitor.capture_exception(exc_info=True)
            return self.return_not_found('UserDebt')
        except KeyError as ex:
            apm.monitor.capture_exception(exc_info=True)
            return self.return_bad_request(ex)
        except Exception as ex:
            apm.monitor.capture_exception(exc_info=True)
            return self.return_unexpected_error(ex)

    @login_required
    def post(self):
        super(UserDebts, self).post()
        try:
            debt = self.me.create_a_deb(self.payload)
            return self.response(debt.to_dict())
        except KeyError as ex:
            apm.monitor.capture_exception(exc_info=True)
            return self.return_bad_request(ex)
        except Exception as ex:
            apm.monitor.capture_exception(exc_info=True)
            return self.return_unexpected_error(ex)


class UserPayments(ResourceBase):
    @login_required
    def get(self, payment_id=None):
        super(UserPayments, self).get()
        if payment_id is None:
            return [self.response(payment.as_dict()) for payment in self.me.payment]
        try:
            payment = self.me.get_payment(payment_id)
            return self.response(payment.as_dict())
        except domain.NotExist:
            apm.monitor.capture_exception(exc_info=True)
            return self.return_not_found('UserPayment')

    @login_required
    def put(self, payment_id):
        super(UserPayments, self).put()
        try:
            return self.response(self.me.update_payment(payment_id, self.payload).as_dict())
        except domain.NotExist:
            apm.monitor.capture_exception(exc_info=True)
            return self.return_not_found('UserPayment')
        except KeyError as ex:
            apm.monitor.capture_exception(exc_info=True)
            return self.return_bad_request(ex)
        except Exception as ex:
            apm.monitor.capture_exception(exc_info=True)
            return self.return_unexpected_error(ex)

    @login_required
    def post(self):
        super(UserPayments, self).post()
        try:
            payment = self.me.create_payment(self.payload)
            return self.response(payment.to_dict())
        except KeyError as ex:
            apm.monitor.capture_exception(exc_info=True)
            return self.return_bad_request(ex)
        except Exception as ex:
            apm.monitor.capture_exception(exc_info=True)
            return self.return_unexpected_error(ex)
