#  -*- coding: utf-8 -*-

from datetime import datetime, date, timedelta
from decimal import Decimal

import jwt
from sqlalchemy import exc, Date, cast
from sqlalchemy.orm import relationship
from passlib.apps import custom_app_context

from app import database, config as config_module

config = config_module.get_config()

db = database.AppRepository.db


class ModelFactory(object):
    @classmethod
    def create(cls, **attrs):
        instance = cls(**attrs)
        return instance

    def save(self):
        db.session.add(self)
        db.session.commit()


class QueryMixin(object):
    @classmethod
    def get_list(cls, *args, **kwargs):
        return cls.query.all()

    @classmethod
    def get(cls, _id):
        return cls.query.get(_id)


class AutenticMixin(object):
    def hash_password(self):
        self.password = custom_app_context.encrypt(self.password)

    def check_password(self, password):
        return custom_app_context.verify(password, self.password)

    def get_jwt_data(self):
        return {}

    def generate_auth_token(self, expiration=600):
        jwt_data = self.get_jwt_data()
        jwt_data['exp'] = datetime.utcnow() + timedelta(seconds=expiration)
        return jwt.encode(jwt_data, config.SECRET_KEY, algorithm='HS256')

    @classmethod
    def check_auth_token(cls, token):
        try:
            data = jwt.decode(token, config.SECRET_KEY)
        except:
            return None
        if not data['id']:
            return None
        user = cls.query.get(data['id'])
        return user

    @classmethod
    def get_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    @property
    def is_admin(self):
        return False


class User(db.Model, ModelFactory, QueryMixin, AutenticMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(), nullable=False)
    debts = relationship('UserDebt', lazy='dynamic', back_populates='user', passive_deletes=True)

    @classmethod
    def create_user(cls, user_data):
        user = None
        try:
            user = cls.create(**user_data)
            user.hash_password()
            user.save()
        except exc.IntegrityError as ex:
            if 'email' in str(ex):
                raise UserAlreadyExist(u'Email já está cadastrado como atleta.')
        return user

    @classmethod
    def update_user(cls, user_id, user_data):
        user = cls.get(user_id)
        try:
            user = cls.create(**user_data)
        except exc.IntegrityError as ex:
            if 'email' in str(ex):
                raise UserAlreadyExist(u'Email já está cadastrado como atleta.')
        return user

    def get_debt(self, debt_id):
        return self.debts.filter(UserDebt.id == debt_id).first()

    @property
    def expiration_day_filter(self):
        return UserDebt.expiration_day

    @property
    def tomorrow(self):
        return date.today().day + 1

    def expired_debts(self):
        return self.debts.filter(UserDebt.is_payed == False, self.expiration_day_filter < date.today().day)

    def opened_debts(self):
        return self.debts.filter(UserDebt.is_payed == False, self.expiration_day_filter > self.tomorrow)

    def payed_debts(self):
        return self.debts.filter(UserDebt.is_payed == True)

    def today_debts(self):
        return self.debts.filter(self.expiration_day_filter == date.today().day)

    def tomorrow_debts(self):
        return self.debts.filter(self.expiration_day_filter == self.tomorrow)

    def debts_resume(self):
        return {
            'all': [debt.to_dict() for debt in self.debts],
            'expired': [debt.to_dict() for debt in self.expired_debts()],
            'opened': [debt.to_dict() for debt in self.opened_debts()],
            'payed': [debt.to_dict() for debt in self.payed_debts()],
            'today': [debt.to_dict() for debt in self.today_debts()],
            'tomorrow': [debt.to_dict() for debt in self.tomorrow_debts()]
        }

    def get_jwt_data(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'has_expired_debts': self.expired_debts().count() > 0,
            'has_expiring_debts': self.today_debts().count() > 0
        }

    def add_debt(self, debt_data):
        value = debt_data.get('value', None)
        if value is not None:
            value = Decimal(value)
            debt_data['value'] = value
        debt = UserDebt.create(**debt_data)
        self.debts.append(debt)
        self.save()
        return debt

    def to_dict(self):
        return self.get_jwt_data()


class UserDebt(db.Model, ModelFactory, QueryMixin):
    __tablename__ = 'users_debts'
    __mapper_args__ = {
        "order_by": 'expiration_day'
    }

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    user = relationship('User', back_populates='debts')
    description = db.Column(db.String(), nullable=False)
    expiration_day = db.Column(db.Integer, nullable=False)
    value = db.Column(db.Numeric(scale=2, precision=7))
    quantity = db.Column(db.Integer)
    payment_info = db.Column(db.String())
    is_payed = db.Column(db.Boolean(), nullable=False, default=False, server_default="false")

    @classmethod
    def clear_all_payed_status(cls):

        db.session.bulk_update_mappings(UserDebt, {"is_payed": False})
        db.session.commit()

    @property
    def status(self):
        if self.is_payed:
            return 'payed'
        if self.expiration_day < datetime.today().day:
            return 'expired'
        if self.expiration_day == datetime.today().day:
            return 'today'
        if self.expiration_day == (date.today().day + 1):
            return 'tomorrow'
        return 'opened'

    def to_dict(self):
        value_formatted = 'NINFO'
        if self.value is not None:
            value_formatted = float(self.value)

        return {
            'id': self.id,
            'description': self.description,
            'expiration_day': self.expiration_day,
            'is_payed': self.is_payed,
            'value': value_formatted,
            'quantity': self.quantity,
            'is_recurrent': self.quantity is None,
            'payment_info': self.payment_info,
            'status': self.status
        }


class UserAlreadyExist(Exception):
    pass
