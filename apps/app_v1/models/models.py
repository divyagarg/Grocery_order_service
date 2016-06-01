import hashlib

from . import db
from sqlalchemy import func, Index

__author__ = 'divyagarg'

""" Making abstract class having common fields"""


class Base(db.Model):
	__abstract__ = True
	created_on = db.Column(db.DateTime, server_default=func.now())
	updated_on = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())


class Status(db.Model):
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	status_code = db.Column(db.String(255), unique=True, nullable=False)
	status_description = db.Column(db.String(255))


class Address(db.Model):
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	name = db.Column(db.String(255), nullable=False)
	mobile = db.Column(db.String(512), nullable=False)
	address = db.Column(db.String(512), nullable=False)
	city = db.Column(db.String(512), nullable=False)
	pincode = db.Column(db.String(512))
	state = db.Column(db.String(512), nullable=False)
	email = db.Column(db.String(512))
	landmark = db.Column(db.String(512))
	order = db.relationship('Order', backref='Address')
	cart = db.relationship('Cart', backref='Address')
	address_hash = db.Column(db.String(255), nullable=False, unique=True)

	def __hash__(self):
		raw_string = self.name + self.mobile + self.address
		return hashlib.sha1(raw_string).hexdigest()

	@classmethod
	def get_address(cls, name, mobile, address, city, pincode, state, email, landmark):

		address = Address(name=name, mobile=mobile, address=address, city=city,
						  pincode=pincode, state=state, email=email, landmark=landmark)

		existing_address = Address().query.filter_by(address_hash=address.__hash__()).first()
		if existing_address is not None:
			return existing_address
		else:
			address.address_hash = address.__hash__()
			db.session.add(address)
			return address


class Cart(Base):
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	cart_reference_uuid = db.Column(db.String(255), nullable=False, unique=True)
	geo_id = db.Column(db.BigInteger, nullable=False)
	user_id = db.Column(db.String(255), nullable=False)
	order_type = db.Column(db.String(255))
	order_source_reference = db.Column(db.String(255))
	promo_codes = db.Column(db.String(255))
	selected_freebee_items = db.Column(db.String(255))
	total_offer_price = db.Column(db.Float(precision='10,2'), default=0.0)
	total_discount = db.Column(db.Float(precision='10,2'), default=0.0)
	total_display_price = db.Column(db.Float(precision='10,2'), default=0.0)
	total_shipping_charges = db.Column(db.Float(precision='10,2'), default=0.0)
	shipping_address_ref = db.Column(db.String(255), db.ForeignKey('address.address_hash'))
	payment_mode = db.Column(db.String(255))
	Index('cart_geo_user_idx', geo_id, user_id)
	orderShipmentDetail = db.relationship('OrderShipmentDetail', backref='Cart', cascade = 'all, delete-orphan')
	cartItem = db.relationship('CartItem', backref='Cart', cascade = 'all, delete-orphan')


class OrderShipmentDetail(db.Model):
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	shipment_id = db.Column(db.String(255), nullable=False, unique=True)
	cart_id = db.Column(db.String(255), db.ForeignKey('cart.cart_reference_uuid'), nullable=False)
	delivery_slot = db.Column(db.String(255))
	cartItem = db.relationship('CartItem', backref='OrderShipmentDetail', cascade="all,delete")


class CartItem(db.Model):
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	cart_id = db.Column(db.String(255), db.ForeignKey('cart.cart_reference_uuid'), nullable=False)
	cart_item_id = db.Column(db.String(255), nullable=False, index=True)
	quantity = db.Column(db.Integer, nullable=False)
	promo_codes = db.Column(db.String(255))
	offer_price = db.Column(db.Float(precision='10,2'), default=0.0)
	display_price = db.Column(db.Float(precision='10,2'), default=0.0)
	item_discount = db.Column(db.Float(precision='10,2'), default=0.0)
	transfer_price = db.Column(db.Float(precision='10,2'), default=0.0)
	same_day_delivery = db.Column(db.String(255))
	title = db.Column(db.String(255))
	image_url = db.Column(db.String(255))
	shipment_id = db.Column(db.String(255), db.ForeignKey('order_shipment_detail.shipment_id'))


class Order(Base):
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	parent_order_id = db.Column(db.String(255), index=True)
	order_reference_id = db.Column(db.String(255), nullable=False, unique=True)
	geo_id = db.Column(db.BigInteger, nullable=False)
	user_id = db.Column(db.String(255), nullable=False)
	order_type = db.Column(db.String(255))
	order_source_reference = db.Column(db.String(255))
	promo_codes = db.Column(db.String(255))
	shipping_address_ref = db.Column(db.String(255), db.ForeignKey('address.address_hash'), nullable=False)
	billing_address_ref = db.Column(db.String(255))
	delivery_slot = db.Column(db.String(512))
	freebie = db.Column(db.String(255))
	total_offer_price = db.Column(db.Float(precision='10,2'), nullable=False)
	total_display_price = db.Column(db.Float(precision='10,2'))
	total_discount = db.Column(db.Float(precision='10,2'))
	total_shipping = db.Column(db.Float(precision='10,2'), default=0.0)
	total_payble_amount = db.Column(db.Float(precision='10,2'), default=0.0)
	payment = db.relationship('Payment', backref='Order')
	orderItem = db.relationship('OrderItem', backref='Order')
	Index('order_user_idx', user_id)
	status_id = db.Column(db.Integer, db.ForeignKey('status.id'), nullable=False)


class OrderItem(db.Model):
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	item_id = db.Column(db.String(255), nullable=False, index=True)
	quantity = db.Column(db.Integer, nullable=False)
	display_price = db.Column(db.Float(precision='10,2'), default=0.0)
	offer_price = db.Column(db.Float(precision='10,2'), default=0.0)
	shipping_charge = db.Column(db.Float(precision='10,2'), default=0.0)
	item_discount = db.Column(db.Float(precision='10,2'), default=0.0)
	transfer_price = db.Column(db.Float(precision='10,2'), default=0.0)
	title = db.Column(db.String(255))
	image_url = db.Column(db.String(255))
	order_id = db.Column(db.String(255), db.ForeignKey('order.order_reference_id'), nullable=False)


class Payment(db.Model):
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	paid_amount = db.Column(db.Float(precision='10,2'), default=0.0)
	payment_mode = db.Column(db.String(255), nullable=False)
	payment_transaction_id = db.Column(db.String(255))
	order_id = db.Column(db.String(255), db.ForeignKey('order.parent_order_id'), nullable=False)
