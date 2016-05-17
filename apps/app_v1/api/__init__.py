import json
import logging

from config import APP_NAME
from flask import g

__author__ = 'divyagarg'

Logger = logging.getLogger(APP_NAME)


class ERROR_DETAIL(object):
	def __init__(self, code, message):
		self.code = code
		self.message = message


class ERROR(object):
	DISCOUNT_CHANGED = ERROR_DETAIL(code=1001, message="Discount not applicable")
	PRODUCT_OFFER_PRICE_CHANGED = ERROR_DETAIL(code=1002, message="Product price changed")
	PRODUCT_DISPLAY_PRICE_CHANGED = ERROR_DETAIL(code=1003, message="Product display prices changed")
	PRODUCT_AVAILABILITY_CHANGED = ERROR_DETAIL(code=1004, message="Product is not available in the given quantity")
	PAYMENT_MODE_NOT_ALLOWED = ERROR_DETAIL(code=1005, message="Selected Payment mode is not applicable for this order")
	FREEBIE_NOT_ALLOWED = ERROR_DETAIL(code=1006, message="Freebie not allowed for this order")
	COUPON_NOT_APPLIED_FOR_CHANNEL = ERROR_DETAIL(code=1007, message="Coupon is not applicable for this channel")
	COUPON_SERVICE_RETURNING_FAILURE_STATUS = ERROR_DETAIL(code=1008, message="Coupon service returning failure status")
	INTERNAL_ERROR = ERROR_DETAIL(code=1009, message=None)
	ORDER_ERROR = ERROR_DETAIL(code=1010, message="Order Error")
	ORDER_VALIDATION_REQUEST_ERROR = ERROR_DETAIL(code=1011, message="Order Request Validation Failed")
	NETWORK_ERROR = ERROR_DETAIL(code=1012, message="Network Error")
	CONNECTION_ERROR = ERROR_DETAIL(code=1013, message="Connection Error")
	CART_EMPTY = ERROR_DETAIL(code=1014, message="Cart is Empty")
	CART_ITEM_MISSING = ERROR_DETAIL(code=1015, message="Cart items are missing")
	CART_ZERO_QUANTITY_CAN_NOT_BE_ADDED = ERROR_DETAIL(code=1016, message="Zero quantity can not be added")
	DATABASE_ERROR = ERROR_DETAIL(code=1017, message=None)
	SUBSCRIPTION_NOT_FOUND = ERROR_DETAIL(code=1018, message="Item is not found")
	NOT_AVAILABLE_ERROR = ERROR_DETAIL(code=1019, message="Quantity not available")
	KEY_MISSING = ERROR_DETAIL(code=1020, message=None)
	INCORRECT_DATA = ERROR_DETAIL(code=1021, message="Incorrect data is given")



def parse_request_data(body):
	Logger.info('{%s} Received request to create cart for request {%s}' % (g.UUID, body))
	json_data = json.loads(body)
	Logger.info('{%s} Json encoded content {%s}' % (g.UUID, json_data))
	return json_data


class NetworkError(RuntimeError):
	def __init__(self, arg):
		self.args = arg


class RequiredFieldMissing(Exception):
	code = None

	def __init__(self, ERROR_DETAIL):
		self.code = ERROR_DETAIL.code
		super(RequiredFieldMissing, self).__init__(ERROR_DETAIL.message)


class EmptyCartException(Exception):
	code = None

	def __init__(self, ERROR_DETAIL):
		self.code = ERROR_DETAIL.code
		super(EmptyCartException, self).__init__(ERROR_DETAIL.message)


class IncorrectDataException(Exception):
	code = None

	def __init__(self, ERROR_DETAIL):
		self.code = ERROR_DETAIL.code
		super(IncorrectDataException, self).__init__(ERROR_DETAIL.message)


class CouponInvalidException(Exception):
	code = None
	def __init__(self, ERROR_DETAIL):
		self.code = ERROR_DETAIL.code
		super(CouponInvalidException, self).__init__(ERROR_DETAIL.message)


class SubscriptionNotFoundException(Exception):
	code = None
	def __init__(self, ERROR_DETAIL):
		self.code = ERROR_DETAIL.code
		super(SubscriptionNotFoundException, self).__init__(ERROR_DETAIL.message)

class QuantityNotAvailableException(Exception):
	code = None
	def __init__(self, ERROR_DETAIL):
		self.code = ERROR_DETAIL.code
		super(QuantityNotAvailableException, self).__init__(ERROR_DETAIL.message)