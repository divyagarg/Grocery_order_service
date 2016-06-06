import json
import logging
import random
import time
from apps.app_v1.models.models import Address, Payment
from config import APP_NAME
import config
from flask import g

__author__ = 'divyagarg'

Logger = logging.getLogger(APP_NAME)


class ERROR_DETAIL(object):
	def __init__(self, code, message):
		self.code = code
		self.message = message


class ERROR(object):
	# General Error
	VALIDATION_ERROR = ERROR_DETAIL(code=1001, message="Input data is incorrect")
	DATABASE_ERROR = ERROR_DETAIL(code=1002, message=None)
	KEY_MISSING = ERROR_DETAIL(code=1003, message=None)
	INCORRECT_DATA = ERROR_DETAIL(code=1004, message="Zero quantity can not be added")
	INVALID_STATUS = ERROR_DETAIL(code=1005, message="No Such status Exist")
	PAYMENT_CAN_NOT_NULL = ERROR_DETAIL(code= 1006, message= "Payment can not be null for an order")
	NO_ORDER_FOUND_ERROR = ERROR_DETAIL(code= 1007, message= "Order does not Exist")
	INTERNAL_ERROR = ERROR_DETAIL(code=1008, message=None)

	# Coupon specific Error
	DISCOUNT_CHANGED = ERROR_DETAIL(code=2001, message="Discount not applicable")
	PAYMENT_MODE_NOT_ALLOWED = ERROR_DETAIL(code=2002, message="Selected Payment mode is not applicable for this order")
	FREEBIE_NOT_ALLOWED = ERROR_DETAIL(code=2003, message="Freebie is not correct")
	COUPON_NOT_APPLIED_FOR_CHANNEL = ERROR_DETAIL(code=2004, message="Coupon is not applicable for this channel")
	COUPON_SERVICE_RETURNING_FAILURE_STATUS = ERROR_DETAIL(code=2005, message="Coupon service returning failure status")
	COUPON_APPLY_FAILED = ERROR_DETAIL(code=2006, message="Coupon application Failed")

	# Product specific Error
	PRODUCT_OFFER_PRICE_CHANGED = ERROR_DETAIL(code=3001, message="Product price changed")
	PRODUCT_DISPLAY_PRICE_CHANGED = ERROR_DETAIL(code=3002, message="Product display prices changed")
	PRODUCT_AVAILABILITY_CHANGED = ERROR_DETAIL(code=3003, message="Product is not available in the given quantity")
	SUBSCRIPTION_NOT_FOUND = ERROR_DETAIL(code=3004, message="Subscription id is not correct")
	NOT_AVAILABLE_ERROR = ERROR_DETAIL(code=3005, message="Quantity not available")

	# Cart specific Error
	CART_EMPTY = ERROR_DETAIL(code=4001, message="Cart is Empty")
	CART_ITEM_MISSING = ERROR_DETAIL(code=4002, message="Cart items are missing")
	CART_ZERO_QUANTITY_CAN_NOT_BE_ADDED = ERROR_DETAIL(code=4003, message="Zero quantity can not be added")
	NO_SUCH_CART_EXIST = ERROR_DETAIL(code=4004, message="No such cart exist")
	NOT_EXISTING_ITEM_CAN_NOT_BE_DELETED = ERROR_DETAIL(code= 4005, message="Non existing item can not be deleted")

	# Delivery Specific Error
	NO_DELIVERY_SLOT_ERROR = ERROR_DETAIL(code= 5001, message="Delivery slot not found")
	OLDER_DELIVERY_SLOT_ERROR = ERROR_DETAIL(code= 5002, message="Older Delivery slot found")
	SHIPMENT_PREVIEW_FAILED = ERROR_DETAIL(code=5003, message="Shipment Preview Failed")
	NO_SHIPPING_ADDRESS_FOUND = ERROR_DETAIL(code=5004, message="Shipping address is mandatory for Order placement")
	SHIPPING_CHARGES_CHANGED = ERROR_DETAIL(code=5005, message="Shipping charges changed")




def parse_request_data(body):
	json_data = json.loads(body)
	Logger.info('{%s} Json encoded content {%s}' % (g.UUID, json_data))
	return json_data


class NetworkError(RuntimeError):
	def __init__(self, arg):
		self.args = arg


class RequiredFieldMissing(Exception):
	code = None

	def __init__(self, error_detail):
		self.code = error_detail.code
		super(RequiredFieldMissing, self).__init__(error_detail.message)


class EmptyCartException(Exception):
	code = None

	def __init__(self, error_detail):
		self.code = error_detail.code
		super(EmptyCartException, self).__init__(error_detail.message)


class IncorrectDataException(Exception):
	code = None

	def __init__(self, error_detail):
		self.code = error_detail.code
		super(IncorrectDataException, self).__init__(error_detail.message)


class CouponInvalidException(Exception):
	code = None

	def __init__(self, error_detail):
		self.code = error_detail.code
		super(CouponInvalidException, self).__init__(error_detail.message)


class SubscriptionNotFoundException(Exception):
	code = None

	def __init__(self, error_detail):
		self.code = error_detail.code
		super(SubscriptionNotFoundException, self).__init__(error_detail.message)


class QuantityNotAvailableException(Exception):
	code = None

	def __init__(self, error_detail):
		self.code = error_detail.code
		super(QuantityNotAvailableException, self).__init__(error_detail.message)


class NoSuchCartExistException(Exception):
	code = None

	def __init__(self, error_detail):
		self.code = error_detail.code
		super(NoSuchCartExistException, self).__init__(error_detail.message)

class PriceChangedException(Exception):
	code = None

	def __init__(self, error_detail):
		self.code = error_detail.code
		super(PriceChangedException, self).__init__(error_detail.message)

class DiscountHasChangedException(Exception):
	code = None

	def __init__(self, error_detail):
		self.code = error_detail.code
		super(DiscountHasChangedException, self).__init__(error_detail.message)

class FreebieNotApplicableException(Exception):
	code = None

	def __init__(self, error_detail):
		self.code = error_detail.code
		super(FreebieNotApplicableException, self).__init__(error_detail.message)
class NoShippingAddressFoundException(Exception):
	code = None

	def __init__(self, error_detail):
		self.code = error_detail.code
		super(NoShippingAddressFoundException, self).__init__(error_detail.message)

class NoSuchStatusException(Exception):
	code = None

	def __init__(self, error_detail):
		self.code = error_detail.code
		super(NoSuchStatusException, self).__init__(error_detail.message)

class PaymentCanNotBeNullException(Exception):
	code = None

	def __init__(self, error_detail):
		self.code = error_detail.code
		super(PaymentCanNotBeNullException, self).__init__(error_detail.message)

class NoDeliverySlotException(Exception):
	code = None

	def __init__(self, error_detail):
		self.code = error_detail.code
		super(NoDeliverySlotException, self).__init__(error_detail.message)

class OlderDeliverySlotException(Exception):
	code = None
	def __init__(self, error_detail):
		self.code = error_detail.code
		super(OlderDeliverySlotException, self).__init__(error_detail.message)

class ShipmentPreviewException(Exception):
	code = None
	def __init__(self, error_detail):
		self.code = error_detail.code
		super(ShipmentPreviewException, self).__init__(error_detail.message)

class OrderNotFoundException(Exception):
	code = None
	def __init__(self, error_detail):
		self.code = error_detail.code
		super(OrderNotFoundException, self).__init__(error_detail.message)

def get_shipping_charges(total_price, total_discount):
		total_shipping_charges =0.0
		if (total_price - total_discount) <= config.SHIPPING_COST_THRESHOLD and (
					total_price - total_discount) > 0:
			total_shipping_charges = float(config.SHIPPING_COST)
		return total_shipping_charges

def generate_reference_order_id():
	longtime = str(int(time.time()))
	longtime = 'GRC'+ longtime[5:] + longtime[:5]
	reference_orderid = longtime + str(random.randint(1000,10000))
	return reference_orderid


def get_address(address_hash):
	address = Address.query.filter_by(address_hash = address_hash).first()
	if address is None:
		Logger.info("[%s] No address is found for address hash [%s]" %(g.UUID, address_hash))
		return None
	return address

def get_payment(order_id):
	payment = Payment.query.filter_by(order_id = order_id).first()
	return payment