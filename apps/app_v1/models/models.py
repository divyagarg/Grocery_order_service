from . import db
import hashlib
from sqlalchemy import func, Enum

__author__ = 'divyagarg'

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
    # email = db.Column(db.String(512))
    # landmark = db.Column(db.String(512))
    order = db.relationship('Order', backref='Address')
    address_hash = db.Column(db.String(255), nullable=False, unique=True)

    def __hash__(self):
        raw_string = self.name + self.mobile + self.street_1 + self.street_2 + self.city + self.pincode + self.state
        return hashlib.sha512(raw_string).hexdigest()



    @classmethod
    def get_address(cls, name, mobile, street_1, street_2, city, pincode, state):

        address = Address(name=name, mobile=mobile, street_1=street_1, street_2=street_2, city=city,
                            pincode=pincode, state=state)

        existing_address = Address().query.filter_by(address_hash = address.__hash__())
        if existing_address is not None:
            return existing_address[0]
        else:
            address.data_hash = address.__hash__()
            return address


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
    cart_id = db.Column(db.String(255), db.ForeignKey('cart.cart_reference_uuid'), nullable=False)
    cart_item_id = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    promo_codes = db.Column(db.String(255))
    offer_price = db.Column(db.Numeric, default=0.0)
    display_price = db.Column(db.Numeric, default=0.0)
    item_discount = db.Column(db.Numeric, default=0.0)
    order_partial_discount = db.Column(db.Numeric, default=0.0)


class Order(Base):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_reference_id = db.Column(db.String(255), nullable=False, unique=True)
    geo_id = db.Column(db.BigInteger, nullable=False)
    user_id = db.Column(db.String(255), nullable=False)
    order_type = db.Column(db.String(255))
    order_source_reference = db.Column(db.String(255))
    promo_codes = db.Column(db.String(255))
    shipping_address_ref = db.Column(db.String(255), db.ForeignKey('address.address_hash'), nullable=False)
    billing_address_ref = db.Column(db.String(255))
    delivery_type = db.Column(Enum('NORMAL', 'SLOTTED'), nullable=False)
    delivery_due_date = db.Column(db.Date)
    delivery_slot = db.Column(Enum('09:12', '12:15', '15:18', '18:21'))
    freebie = db.Column(db.String(255))
    payment = db.relationship('Payment', backref='Order')
    orderItem = db.relationship('Order_Item', backref='Order')


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    total_offer_price = db.Column(db.Numeric, nullable = False)
    total_display_price = db.Column(db.Numeric)
    total_discount = db.Column(db.Numeric)
    amount = db.Column(db.Numeric, default=0.0)
    payment_mode = db.Column(Enum('COD', 'SODEXO', 'PREPAID', 'TICKET'), nullable=False)
    payment_transaction_id = db.Column(db.String(255))
    order_id = db.Column(db.String(255), db.ForeignKey('order.order_reference_id'), nullable=False)


class Order_Item(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    display_price = db.Column(db.Numeric, default=0.0)
    offer_price = db.Column(db.Numeric, default=0.0)
    shipping_charge = db.Column(db.Numeric, default=0.0)
    item_discount = db.Column(db.Numeric, default=0.0)
    order_partial_discount = db.Column(db.Numeric, default=0.0)
    order_id = db.Column(db.String(255), db.ForeignKey('order.order_reference_id'), nullable=False)
