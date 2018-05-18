from datetime import datetime, date
from decimal import Decimal

from passlib.apps import custom_app_context

from app import models


class Entity(object):
    repository = None

    class AlreadyExist(Exception):
        pass

    class NotExist(Exception):
        pass

    @classmethod
    def list_all(cls):
        return [cls.create_with_instance(instance) for instance in cls.repository.list_all()]

    @classmethod
    def create_new(cls, json_data):
        try:
            return cls(cls.repository.create_from_json(json_data))
        except cls.repository.RepositoryError as ex:
            if 'already exists' in ex.message.lower:
                raise cls.AlreadyExist('Entity with {} already exists in repository'.format(json_data))

    @classmethod
    def create_with_id(cls, entity_id):
        instance = cls.repository.get(entity_id)
        return cls.create_with_instance(instance)

    @classmethod
    def create_with_instance(cls, instance):
        if instance is None:
            raise cls.NotExist('Tryed to create entity with instance None. Check the stack trace to see the origin')
        return cls(instance)

    def __init__(self, instance):
        self.instance = instance
        self.id = instance.id

    def save(self):
        self.instance.save_db()

    @staticmethod
    def remove_unused_json_data_key(key, json_data):
        if key in json_data:
            del json_data[key]

    def update_me(self, json_data):
        self.instance.update_from_json(json_data)

    def as_dict(self, compact=False):
        return {
            'id': self.id,
        }


class ValueObject(object):
    repository = None

    class AlreadyExist(Exception):
        pass

    class NotExist(Exception):
        pass

    @classmethod
    def list_all(cls, parent_instance_list):
        return [cls.create_with_instance(instance) for instance in parent_instance_list]

    @classmethod
    def create_new(cls, json_data):
        try:
            return cls(cls.repository.create_from_json(json_data))
        except cls.repository.RepositoryError as ex:
            if 'already exists' in ex.message.lower:
                raise cls.AlreadyExist('Entity with {} already exists in repository'.format(json_data))

    @classmethod
    def create_with_instance(cls, instance):
        if instance is None:
            raise cls.NotExist('Tryed to create entity with instance None. Check the stack trace to see the origin')
        return cls(instance)

    def __init__(self, instance):
        self.instance = instance
        self.id = instance.id

    def save(self):
        self.instance.save_db()

    @staticmethod
    def remove_unused_json_data_key(key, json_data):
        if key in json_data:
            del json_data[key]

    def update_me(self, json_data):
        self.instance.update_from_json(json_data)

    def as_dict(self, compact=False):
        return {
            'id': self.id,
        }


class UserDebt(ValueObject):
    repository = models.UserDebt

    @property
    def description(self):
        return self.instance.description

    @property
    def value(self):
        return self.instance.value

    @property
    def quantity(self):
        return self.instance.quantity

    @property
    def expiration_day(self):
        return self.instance.expiration_day

    @property
    def is_recurrent(self):
        return self.quantity is None

    @property
    def is_active(self):
        return self.quantity > 0

    def decrease_quantity(self):
        self.update_me({'quantity', self.quantity - 1})

    def as_dict(self, compact=False):
        value_formatted = 'NINFO'
        if self.value is not None:
            value_formatted = float(self.value)

        return {
            'id': self.id,
            'description': self.description,
            'expiration_day': self.expiration_day,
            'value': value_formatted,
            'quantity': self.quantity,
            'is_recurrent': self.is_recurrent
        }


class UserPayment(ValueObject):
    repository = models.UserPayment

    def __init__(self, instance):
        super(UserPayment, self).__init__(instance)
        self.__debt = None

    @property
    def year(self):
        return self.instance.year

    @property
    def month(self):
        return self.instance.month

    @property
    def is_payed(self):
        return self.instance.is_payed

    @property
    def status(self):
        if self.is_payed:
            return 'payed'
        if self.debt.expiration_day < datetime.today().day:
            return 'expired'
        if self.debt.expiration_day == datetime.today().day:
            return 'today'
        if self.debt.expiration_day == (date.today().day + 1):
            return 'tomorrow'
        return 'opened'

    @property
    def debt(self):
        if self.__debt is None:
            self.__debt = UserDebt.create_with_instance(self.instance.user_debt)
        return self.__debt

    def as_dict(self, compact=False):
        return {
            'id': self.id,
            'date': '{}-{}-{}'.format(self.year, self.month, self.debt.expiration_day),
            'status': self.status,
            'debt': self.debt.as_dict()
        }


class User(Entity):
    repository = models.User

    @classmethod
    def create_new(cls, json_data):
        json_data['password'] = custom_app_context.encrypt(json_data['password'])
        super(User, cls).create_new(json_data)

    def __init__(self, instance):
        super(User, self).__init__(instance)
        self.__debts = None
        self.__current_payments = None

    @property
    def name(self):
        return self.instance.name

    @property
    def email(self):
        return self.instance.email

    @property
    def current_payments(self):
        if self.__current_payments is None:
            today = date.today()
            self.__current_payments = UserPayment.list_all(self.instance.filter_payments(today.year, today.month))
        return self.__current_payments

    @property
    def debts(self):
        if self.__debts is None:
            self.__debts = UserDebt.list_all(self.instance.debts)
        return self.__debts

    def create_a_deb(self, debt_data):
        debt_data['user_id'] = self.id
        debt_data['value'] = Decimal(debt_data.get('value', 0.0))
        debt = UserDebt.create_new(debt_data)
        self.__debts = None
        return debt

    def create_month_payments(self, year, month):
        for debt in self.debts:
            if debt.is_active or debt.is_recurrent:
                payment_data = {
                    'user_id': self.id,
                    'user_debt_id': debt.id,
                    'year': year,
                    'month': month
                }
                UserPayment.create_new(payment_data)
                if debt.is_active:
                    debt.decrease_quantity()

    def list_payments_for(self, year, month):
        return UserPayment.list_all(self.instance.filter_payments(year, month))

    def get_jwt_data(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
        }
