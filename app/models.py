#  -*- coding: utf-8 -*-

from sqlalchemy import exc
from sqlalchemy.orm import relationship

from app import database

db = database.AppRepository.db


class AbstractModel(object):
    class NotExist(Exception):
        pass

    class RepositoryError(Exception):
        pass

    @classmethod
    def create_from_json(cls, json_data):
        try:
            instance = cls()
            instance.set_values(json_data)
            instance.save_db()
            return instance
        except exc.IntegrityError as ex:
            raise cls.RepositoryError(ex.message)

    @classmethod
    def list_with_filter(cls, **kwargs):
        return cls.query.filter_by(**kwargs).all()

    @classmethod
    def list_all(cls):
        return cls.query.all()

    @classmethod
    def get_with_filter(cls, **kwargs):
        return cls.query.filter_by(**kwargs).one_or_none()

    @classmethod
    def get(cls, item_id):
        item = cls.query.get(item_id)
        if not item:
            raise cls.NotExist
        else:
            return item

    def save_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_db(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except exc.IntegrityError as ex:
            raise self.RepositoryError(ex.message)

    def update_from_json(self, json_data):
        try:
            self.set_values(json_data)
            self.save_db()
            return self
        except exc.IntegrityError as ex:
            raise self.RepositoryError(ex.message)

    def set_values(self, json_data):
        for key, value in json_data.iteritems():
            setattr(self, key, json_data.get(key, getattr(self, key)))


class User(db.Model, AbstractModel):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(), nullable=False)
    debts = relationship('UserDebt', lazy='dynamic', order_by='UserDebt.expiration_day', back_populates='user', passive_deletes=True)
    payments = relationship('UserPayment', lazy='dynamic', order_by='-UserPayment.year,UserPayment.month', back_populates='user', passive_deletes=True)

    @classmethod
    def get_by_email(cls, email):
        return cls.get_with_filter(email=email)

    def filter_payments(self, year, month):
        return self.payments.filter_by(year=year, month=month)

    def payment_exists(self, debt_id, year, month):
        return self.payments.filter_by(user_debt_id=debt_id, year=year, month=month).count() > 0

    def get_debt(self, debt_id):
        return self.debts.filter_by(debt_id).first()

    def get_payment(self, payment_id):
        return self.payments.filter_by(id=payment_id).first()


class UserDebt(db.Model, AbstractModel):
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
    payments = relationship('UserPayment', lazy='dynamic', order_by='UserPayment.year,UserPayment.month', back_populates='user_debt')


class UserPayment(db.Model, AbstractModel):
    __tablename__ = 'users_payments'
    __mapper_args__ = {
        "order_by": '-year,-month'
    }

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer)
    month = db.Column(db.Integer)
    value = db.Column(db.Numeric(scale=2, precision=7))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    user = relationship('User', back_populates='payments')
    user_debt_id = db.Column(db.Integer, db.ForeignKey('users_debts.id'))
    user_debt = relationship('UserDebt', lazy='joined', back_populates='payments')
    is_payed = db.Column(db.Boolean(), nullable=False, default=False, server_default="false")
    payment_info = db.Column(db.String())


class UserAlreadyExist(Exception):
    pass
