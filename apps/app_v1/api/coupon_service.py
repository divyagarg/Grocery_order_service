import json
import logging

import requests
import config

from apps.app_v1.api import parse_request_data, ERROR
from apps.app_v1.api.api_schema_signature import CHECK_COUPON_SCHEMA
from config import APP_NAME
from flask import current_app, g
from utils.jsonutils.json_schema_validator import validate
from utils.jsonutils.output_formatter import create_error_response

__author__ = 'divyagarg'

Logger = logging.getLogger(APP_NAME)


class CouponService(object):

	def __init__(self):
		pass

	@staticmethod
	def check_coupon_api(body):
		try:
			request_data = parse_request_data(body)
			validate(request_data, CHECK_COUPON_SCHEMA)
			response = CouponService.call_check_coupon_api(request_data)
			return json.loads(response.text)
		except Exception as e:
			Logger.error('[%s] Exception occured while checking coupon [%s]' , g.UUID, str(e), exc_info=True)
			ERROR.INTERNAL_ERROR.message = str(e)
			return create_error_response(ERROR.INTERNAL_ERROR)

	@staticmethod
	def call_check_coupon_api(request_data):
		url = current_app.config['COUPON_CHECK_URL']
		header = {
			'X-API-USER': current_app.config['X_API_USER'],
			'X-API-TOKEN': current_app.config['X_API_TOKEN'],
			'content-type': 'application/json'
		}
		if 'payment_mode' in request_data:
			url = url + config.COUPON_QUERY_PARAM
		Logger.info('[%s] Request for check coupon is [%s]', g.UUID, json.dumps(request_data))
		response = requests.post(url=url, data=json.dumps(request_data), headers=header,timeout= current_app.config['API_TIMEOUT'])
		Logger.info('[%s] Response got is [%s]', g.UUID, json.dumps(response.text))
		return response

	@staticmethod
	def apply_coupon(request_data):
		url = current_app.config['COUPOUN_APPLY_URL']
		header = {
			'X-API-USER': current_app.config['X_API_USER'],
			'X-API-TOKEN': current_app.config['X_API_TOKEN'],
			'Content-type': 'application/json'
		}
		response = requests.post(url=url, data=json.dumps(request_data), headers=header,timeout= current_app.config['API_TIMEOUT'])
		return response
