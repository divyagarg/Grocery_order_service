import json
from config import APP_NAME
import logging
from flask import g

__author__ = 'divyagarg'

Logger = logging.getLogger(APP_NAME)

error_code = {
	"discount_changed": 1001,
	"product_offer_price_changes": 1002,
	"product_display_price_changes": 1003,
	"product_availability_changed": 1004,
	"payment_mode_not_allowed": 1005,
	"freebie_not_allowed": 1006,
	"coupon_not_applid_for_channel": 1007,
	"coupon_service_returning_failure_status": 1008,
	"cart_error": 1009,
	"order_error": 1010,
	"order_validation_request_error": 1011,
	"network_error": 1012,
	"connection_error": 1013,
	"data_missing": 1014,
	"cart_empty": 1015,
	"coupon_error": 1016
}

error_messages = {
	"discount_changed": "Discount not applicable",
	"product_offer_price_changes": "Product price changed",
	"product_display_price_changes": "Product display prices changed",
	"product_availability_changed": "Product is not available in the given quantity",
	"payment_mode_not_allowed": "Selected Payment mode is not applicable for this order",
	"freebie_not_allowed": "Freebie not allowed for this order",
	"coupon_not_applid_for_channel": "Coupon is not applicable for this channel",
	"coupon_service_returning_failure_status": "Coupon service returning failure status",
	"cart_error": "Error in updating cart",
	"order_error": "Order Error",
	"order_validation_request_error": "Order Request Validation Failed",
	"network_error": "Network Error",
	"connection_error": "Connection Error",
	"cart_empty": "Cart is Empty"
}


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

	def __init__(self, code, message):
		self.code = code
		super(Exception, self).__init__(message)


class EmptyCartException(Exception):
	code = None

	def __init__(self, code, message):
		self.code = code
		super(Exception, self).__init__(message)


class IncorrectDataException(Exception):
	code = None

	def __init__(self, code, message):
		self.code = code
		super(Exception, self).__init__(message)


class CouponInvalidException(Exception):
	error_code = None

	def __init__(self, code, message):
		self.code = code
		super(Exception, self).__init__(message)
