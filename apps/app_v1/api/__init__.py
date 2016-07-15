import json
import logging
import random
import time

from apps.app_v1.models.models import Address, Payment, Order
from config import APP_NAME
import config
from flask import g, current_app
import requests

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
	PAYMENT_SERVICE_IS_DOWN = ERROR_DETAIL(code=1009, message="Payment service is temporary unavailable")
	PAYMENT_API_TIMEOUT = ERROR_DETAIL(code=1010, message="Payment API timeout")

	COUPON_SERVICE_DOWN = ERROR_DETAIL(code=1012, message="Coupon service is temporary unavailable")
	COUPON_API_TIMEOUT = ERROR_DETAIL(code=1013, message="Coupon API Request timeout")
	PRODUCT_CATALOG_SERVICE_DOWN = ERROR_DETAIL(code=1014, message="Product catalog service is temporary unavailable")
	PRODUCT_API_TIMEOUT = ERROR_DETAIL(code=1015, message="Product API Request timeout")
	SHIPMENT_PREVIEW_FAILED = ERROR_DETAIL(code=1016, message="Shipment Preview Failed")
	FULFILLMENT_SERVICE_DOWN = ERROR_DETAIL(code=1017, message="Fulfillment Service is temporary unavailable")
	FULFILLMENT_API_TIMEOUT = ERROR_DETAIL(code=1018, message="Fulfilment API Request timeout")
	#OPS-Panel Specific Error
	OPS_PANEL_DOWN = ERROR_DETAIL(code=1019, message="OPS Panel Service is temporary unavailable")

	# Coupon specific Error
	DISCOUNT_CHANGED = ERROR_DETAIL(code=2001, message="Discount not applicable")
	PAYMENT_MODE_NOT_ALLOWED = ERROR_DETAIL(code=2002, message="Coupon code is not valid for given paymentMode")
	FREEBIE_NOT_ALLOWED = ERROR_DETAIL(code=2003, message="Freebie is not correct")
	COUPON_NOT_APPLIED_FOR_CHANNEL = ERROR_DETAIL(code=2004, message="Coupon is not applicable for this channel")
	COUPON_APPLY_FAILED = ERROR_DETAIL(code=2005, message="Coupon can not applied")
	FREEBIE_NOT_APPLICABLE = ERROR_DETAIL(code=2006, message="Freebie is not applicable on the current cart items")
	COUPON_SERVICE_RETURNING_FAILURE_STATUS = ERROR_DETAIL(code=2007, message="Coupon service returning failure status")
	REMOVE_COUPON_BEFORE_DELETING_LAST_ITEM = ERROR_DETAIL(code= 2008, message="Please remove coupon first")
	# Product specific Error
	PRODUCT_OFFER_PRICE_CHANGED = ERROR_DETAIL(code=3001, message="Product price changed")
	PRODUCT_DISPLAY_PRICE_CHANGED = ERROR_DETAIL(code=3002, message="Product display price changed")
	PRODUCT_AVAILABILITY_CHANGED = ERROR_DETAIL(code=3003, message="Requested quantoty of the product is not available")
	SUBSCRIPTION_NOT_FOUND = ERROR_DETAIL(code=3004, message="Subscription id is not correct")


	# Cart specific Error
	CART_EMPTY = ERROR_DETAIL(code=4001, message="Cart is Empty")
	CART_ITEM_MISSING = ERROR_DETAIL(code=4002, message="Cart items are missing")
	CART_ZERO_QUANTITY_CAN_NOT_BE_ADDED = ERROR_DETAIL(code=4003, message="Zero quantity can not be added")
	NO_SUCH_CART_EXIST = ERROR_DETAIL(code=4004, message="No such cart exist")
	NOT_EXISTING_ITEM_CAN_NOT_BE_DELETED = ERROR_DETAIL(code= 4005, message="Item is already deleted from Cart")
	CHANGE_USER_NOT_POSSIBLE = ERROR_DETAIL(code= 4006, message="Change User is not possible as cart does not Exist")

	# Delivery Specific Error
	NO_DELIVERY_SLOT_ERROR = ERROR_DETAIL(code=5001, message="Delivery slot not found")
	OLDER_DELIVERY_SLOT_ERROR = ERROR_DETAIL(code=5002, message="Older Delivery slot can not be updated")
	NO_SHIPPING_ADDRESS_FOUND = ERROR_DETAIL(code=5003, message="Shipping address is mandatory for Order placement")
	SHIPPING_CHARGES_CHANGED = ERROR_DETAIL(code=5004, message="Shipping charges changed")





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


class RemoveCouponBeforeDeletingLastItem(Exception):
	code = None

	def __init__(self, error_detail):
		self.code = error_detail.code
		super(RemoveCouponBeforeDeletingLastItem, self).__init__(error_detail.message)


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

class ServiceUnAvailableException(Exception):
	code = None
	def __init__(self, error_detail):
		self.code = error_detail.code
		super(ServiceUnAvailableException, self).__init__(error_detail.message)

class RequestTimeoutException(Exception):
	code = None
	def __init__(self, error_detail):
		self.code = error_detail.code
		super(RequestTimeoutException, self).__init__(error_detail.message)


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

def get_order(order_id):
	order = Order.query.filter_by(order_reference_id = order_id).first()
	return order

def send_sms(phoneno, sms_body):
	sms_url = current_app.config['SMS_SERVICE_URL']
	full_sms_url = sms_url + '&phoneNo='+phoneno+'&smsBody='+sms_body
	response = requests.get(url= full_sms_url)
	return response