import enum
from datetime import datetime

from flask_login import UserMixin
from src import db, app
import jwt
from sqlalchemy.orm import relationship
from sqlalchemy import Enum
from time import time



class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(250), nullable=False, index=True)
    product_description = db.Column(db.String(300), nullable=False)
    category = db.Column(db.String(30), nullable=False, index=True)
    price = db.Column(db.Integer, nullable=False, index=True)
    img_url = db.Column(db.String(500), nullable=False)
    order = db.relationship("Order", back_populates="product_name", cascade="all, delete")
    reviews = db.relationship("Reviews", backref="product")

    def __repr__(self):
        return f"<name:{self.product_name}>"

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Customer(UserMixin, db.Model):
    __tablename__ = "customers"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    street = db.Column(db.String(250), nullable=False)
    city = db.Column(db.String(250), nullable=False)
    zip = db.Column(db.String(250), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    mail = db.Column(db.String(250), nullable=False, unique=True)
    password = db.Column(db.String(500), nullable=False)
    role = db.Column(db.Integer, nullable=False, default=2)
    order = db.relationship("OrderDetails", back_populates="customer_name")
    reviews = db.relationship("Reviews", backref="customer", cascade="all, delete")

    def __repr__(self):
        return f"<mail:{self.mail}>"

    def get_token(self, expires_sec=1200):
        return jwt.encode({'mail': self.mail,
                           'exp': time() + expires_sec},
                          key=app.config['SECRET_KEY'])

    @staticmethod
    def verify_token(token):
        print(token)
        try:
            user = jwt.decode(token, algorithms="HS256",
                              key=app.config["SECRET_KEY"])['mail']
            print(user)
        except Exception as e:
            app.logger.error(e)
            return None
        return Customer.query.filter_by(mail=user).first()

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    product_name = db.relationship("Product", back_populates="order")
    quantity = db.Column(db.Integer, db.CheckConstraint('quantity>0'), nullable=False)

    order_details_id = db.Column(db.Integer, db.ForeignKey("order_details.id"))
    order_name = db.relationship("OrderDetails", back_populates="order")

    def __repr__(self):
        return f"<name:{self.product_id}>"
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class OrderDetails(db.Model):
    __tablename__ = "order_details"
    id = db.Column(db.Integer, primary_key=True)

    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"))
    customer_name = db.relationship("Customer", back_populates="order")

    order = db.relationship("Order", back_populates="order_name")

    to_street = db.Column(db.String(250), nullable=False)
    to_city = db.Column(db.String(250), nullable=False)
    zip = db.Column(db.String(250), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Reviews(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    review = db.Column(db.String(150), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('customer_id', 'product_id'),)

    def __repr__(self):
        return f"<name:{self.customer}>, <product{self.product}>"
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False, unique=True)



    def __repr__(self):
        return f"<id: {self.id}>, <role {self.name}>"
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class BlacklistToken(db.Model):
    """
    Token Model for storing JWT tokens
    """
    __tablename__ = 'blacklist_tokens'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(500), unique=True, nullable=False)
    blacklisted_on = db.Column(db.DateTime, nullable=False)

    def __init__(self, token):
        self.token = token
        self.blacklisted_on = datetime.now()

    def __repr__(self):
        return '<id: token: {}'.format(self.token)

    @staticmethod
    def check_blacklist(auth_token):
        # check whether auth token has been blacklisted
        res = BlacklistToken.query.filter_by(token=str(auth_token)).first()
        if res:
            return True
        else:
            return False


# db.drop_all()
# db.create_all()