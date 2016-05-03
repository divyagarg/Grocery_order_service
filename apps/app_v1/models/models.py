from . import db
from sqlalchemy import func, Enum

__author__ = 'divyagarg'

delivery_types = ('Normal', 'Slotted')

""" Making abstract class having common fields"""


class Base(db.Model):
    __abstract__ = True
    created_on = db.Column(db.DateTime, server_default=func.now())
    updated_on = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())


class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    mobile = db.Column(db.String(512), nullable=False)
    street_1 = db.Column(db.String(512), nullable=False)
    street_2 = db.Column(db.String(512))
    city = db.Column(db.String(512), nullable=False)
    pincode = db.Column(db.String(512), nullable=False)
    state = db.Column(db.String(512), nullable=False)
    email = db.Column(db.String(512))
    landmark = db.Column(db.String(512))
    order = db.relationship('Order', backref='Order')

class Cart(Base):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cart_reference_uuid = db.Column(db.String(255), nullable=False, unique=True)
    geo_id = db.Column(db.BigInteger, nullable=False)
    user_id = db.Column(db.String(255), nullable=False)
    promo_codes = db.Column(db.String(255))
    total_offer_price = db.Column(db.Numeric, default=0.0)
    total_discount = db.Column(db.Numeric, default=0.0)
    total_display_price = db.Column(db.Numeric, default=0.0)
    cartItem = db.relationship('Cart_Item', backref='Cart')

class Cart_Item(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cart_item_id = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    promo_codes = db.Column(db.String(255))
    offer_price = db.Column(db.Numeric, default=0.0)
    display_price = db.Column(db.Numeric, default=0.0)
    item_discount = db.Column(db.Numeric, default=0.0)
    order_partial_discount = db.Column(db.Numeric, default=0.0)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'))

class Order(Base):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_reference_id = db.Column(db.String(255), nullable=False)
    geo_id = db.Column(db.BigInteger, nullable=False)
    user_id = db.Column(db.String(255), nullable=False)
    promo_codes = db.Column(db.String(255))
    shipping_address = db.Column(db.Integer, db.ForeignKey('address.id'), nullable=False)
    billing_address = db.Column(db.Integer, db.ForeignKey('address.id'))
    delivery_type = db.Column(Enum('Normal', 'Slotted', name='delivery_types'), nullable=False)
    delivery_due_date = db.Column(db.Date)
    delivery_slot = db.Column(Enum('09:12', '12:15', '15:18', '18:21', name='delivery_time_slots'))
    freebie = db.Column(db.String(255))
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.id'), nullable=False)
    orderItem = db.relationship('Order_Item', backref='Order')

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    amount = db.Column(db.Numeric, default=0.0)
    payment_mode = db.Column(Enum('COD', 'SODEXO', 'PREPAID', 'TICKET', name='payment_mode_type'))
    payment_transaction_id = db.Column(db.String(255))
    order = db.relationship('Order', backref='Payment')


class Order_Item(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    display_price = db.Column(db.Numeric, default=0.0)
    offer_price = db.Column(db.Numeric, default=0.0)
    shipping_charge = db.Column(db.Numeric, default=0.0)
    item_discount = db.Column(db.Numeric, default=0.0)
    order_partial_discount = db.Column(db.Numeric, default=0.0)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))