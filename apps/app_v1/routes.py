import json
import uuid
import logging
from apps.app_v1.api.payment_service import get_order_prices, \
	update_payment_details, get_payment_details
import flask
from flask import request, g
from config import APP_NAME
from apps.app_v1.api.cart_service import CartService
from utils.jsonutils.output_formatter import create_error_response
from apps.app_v1.api.coupon_service import CouponService
from apps.app_v1.api.delivery_service import DeliveryService, update_slot
from apps.app_v1.api.order_service import OrderService, \
	get_count_of_orders_of_user, check_if_cod_possible_for_order, \
	convert_order_to_cod, get_order_count_for_today
from . import app_v1
from apps.app_v1.api import ERROR
from lib.decorators import jsonify, logrequest

logger = logging.getLogger(APP_NAME)


@app_v1.route('/test', methods=['GET'])
@jsonify
@logrequest
def test():
	logger.info("Getting call for test function with request data %s", request.data)
	result = {"success": True}
	return result


@app_v1.route('/cart', methods=['POST'])
@jsonify
@logrequest
def createOrUpdateCart():
	g.UUID = uuid.uuid4()
	logger.info('START_CALL [%s] Request_url = [%s], arguments = [%s]', g.UUID, str(request.url), json.dumps(request.data))
	try:
		cartservice = CartService()
		response = cartservice.create_or_update_cart(request.data)
		logger.info("[%s] END_OF_CALL [%s]", g.UUID, json.dumps(response))
		return response
	except Exception as exception:
		logger.error("[%s] Exception occured in cart service [%s]", g.UUID, str(exception), exc_info=True)
		ERROR.INTERNAL_ERROR.message = str(exception)
		return create_error_response(ERROR.INTERNAL_ERROR)


@app_v1.route('/add_to_cart', methods=['POST'])
@jsonify
@logrequest
def add_item_to_cart_and_get_count_of_items():
	g.UUID = uuid.uuid4()
	logger.info('START_CALL [%s] Request_url = [%s], arguments = [%s]', g.UUID, str(request.url), json.dumps(request.data))
	try:
		cartservice = CartService()
		response = cartservice.add_item_to_cart(request.data)
		logger.info("[%s] END_OF_CALL", g.UUID)
		return response
	except Exception as exception:
		logger.error("[%s] Exception occured in getting count of cart items [%s]", g.UUID, str(exception), exc_info=True)
		ERROR.INTERNAL_ERROR.message = str(exception)
		return create_error_response(ERROR.INTERNAL_ERROR)


@app_v1.route('/user', methods=['GET'])
@jsonify
@logrequest
def get_count_of_orders_of_a_user():
	g.UUID = uuid.uuid4()
	logger.info('START_CALL [%s] Request_url = [%s], arguments = [%s]', g.UUID, str(request.url), json.dumps(request.args))
	try:
		if request.args.__len__() == 0 :
			response = create_error_response(ERROR.VALIDATION_ERROR)
		else:
			response = get_count_of_orders_of_user(request.args['user_id'])
		logger.info("[%s] END_OF_CALL [%s]", g.UUID, json.dumps(response))
		return response
	except Exception as exception:
		logger.error("[%s] Exception occured in getting count of orders of a user [%s]", g.UUID, str(exception),
					 exc_info=True)
		ERROR.INTERNAL_ERROR.message = str(exception)
		return create_error_response(ERROR.INTERNAL_ERROR)


@app_v1.route('/order', methods=['POST'])
@jsonify
@logrequest
def order():
	g.UUID = uuid.uuid4()
	logger.info('START_CALL [%s] Request_url = [%s], arguments = [%s]', g.UUID, str(request.url), json.dumps(request.data))

	try:
		order_service = OrderService()
		response = order_service.createorder(request.data)
		logger.info("[%s] END_OF_CALL [%s]", g.UUID, json.dumps(response))
		return response
	except Exception as exception:
		logger.error("[%s] Exception occured in order service [%s]", g.UUID, str(exception), exc_info=True)
		ERROR.INTERNAL_ERROR.message = str(exception)
		return create_error_response(ERROR.INTERNAL_ERROR)


@app_v1.route('/delivery', methods=['POST'])
@jsonify
@logrequest
def delivery_info():
	g.UUID = uuid.uuid4()
	logger.info('START_CALL [%s] Request_url = [%s], arguments = [%s]', g.UUID, str(request.url), json.dumps(request.data))

	try:
		delivery_service = DeliveryService()
		response = delivery_service.get_delivery_info(request.data)
		logger.info("[%s] END_OF_CALL [%s]", g.UUID, json.dumps(response))
		return response
	except Exception as exception:
		logger.error("[%s] Exception occured in delivery service [%s]", g.UUID, str(exception), exc_info=True)
		ERROR.INTERNAL_ERROR.message = str(exception)
		return create_error_response(ERROR.INTERNAL_ERROR)


@app_v1.route('/slot', methods=['POST'])
@jsonify
@logrequest
def slot():
	g.UUID = uuid.uuid4()
	logger.info('START_CALL [%s] Request_url = [%s], arguments = [%s]', g.UUID, str(request.url), json.dumps(request.data))
	try:
		response = update_slot(request.data)
		logger.info("[%s] END_OF_CALL [%s]", g.UUID, json.dumps(response))
		return response
	except Exception as exception:
		logger.error("[%s] Exception occured in delivery service [%s]", g.UUID, str(exception), exc_info=True)
		ERROR.INTERNAL_ERROR.message = str(exception)
		return create_error_response(ERROR.INTERNAL_ERROR)


@app_v1.route('/get_order_prices', methods=['POST'])
def get_order_prices_api():
	g.UUID = uuid.uuid4()
	logger.info('START_CALL [%s] Request_url = [%s], arguments = [%s]', g.UUID, str(request.url), json.dumps(request.data))
	response = get_order_prices(request)
	logger.info('[%s] END_OF_CALL [%s]', g.UUID, json.dumps(response))
	return flask.jsonify(response)


@app_v1.route('/update_payment_details', methods=['POST'])
def update_payment_details_api():
	g.UUID = uuid.uuid4()
	logger.info('START_CALL [%s] Request_url = [%s], arguments = [%s]', g.UUID, str(request.url), json.dumps(request.data))
	response = update_payment_details(request)
	logger.info('[%s] END_OF_CALL [%s]', g.UUID, json.dumps(response))
	return flask.jsonify(response)


@app_v1.route('/get_payment_details', methods=['POST'])
def get_payment_details_api():
	g.UUID = uuid.uuid4()
	logger.info('START_CALL [%s] Request_url = [%s], arguments = [%s]', g.UUID, str(request.url), json.dumps(request.data))
	response = get_payment_details(request)
	logger.info('[%s] END_OF_CALL [%s]', g.UUID, json.dumps(response))
	return flask.jsonify(response)


@app_v1.route('/change_user', methods=['POST'])
def change_user():
	g.UUID = uuid.uuid4()
	logger.info('START_CALL [%s] Request_url = [%s], arguments = [%s]', g.UUID, str(request.url), json.dumps(request.data))
	cart_service = CartService()
	response = cart_service.change_user(request.data)
	logger.info('[%s] END_OF_CALL [%s]', g.UUID, json.dumps(response))
	return flask.jsonify(response)


@app_v1.route('/check_coupon', methods=['POST'])
def check_coupon():
	g.UUID = uuid.uuid4()
	logger.info('START_CALL [%s] Request_url = [%s], arguments = [%s]', g.UUID, str(request.url), json.dumps(request.data))
	response = CouponService.check_coupon_api(request.data)
	logger.info('[%s] END_OF_CALL [%s]', g.UUID, json.dumps(response))
	return flask.jsonify(response)


@app_v1.route('/check_cod', methods = ['GET'])
def check_cod():
	g.UUID = uuid.uuid4()
	logger.info('START_CALL [%s] Request_url = [%s], arguments = [%s]', g.UUID, str(request.url), json.dumps(request.args))
	if request.args.__len__() == 0:
		response = create_error_response(ERROR.VALIDATION_ERROR)
	else:
		response = check_if_cod_possible_for_order(request.args['order_id'])
	logger.info('[%s] END_OF_CALL [%s]', g.UUID, json.dumps(response))
	return flask.jsonify(response)


@app_v1.route('/convert_cod', methods = ['POST'])
def convert_cod():
	g.UUID = uuid.uuid4()
	logger.info('START_CALL [%s] Request_url = [%s], arguments = [%s]', g.UUID, str(request.url), json.dumps(request.data))
	response = convert_order_to_cod(request.data)
	logger.info('[%s] END_OF_CALL [%s]', g.UUID, json.dumps(response))
	return flask.jsonify(response)


@app_v1.route('/add_item_to_cart', methods = ['POST'])
def add_to_cart():
	g.UUID = uuid.uuid4()
	logger.info('START_CALL [%s] Request_url = [%s], arguments = [%s]', g.UUID, str(request.url), json.dumps(request.data))
	response = CartService().add_to_cart(request.data)
	logger.info('[%s] END_OF_CALL [%s]', g.UUID, json.dumps(response))
	return flask.jsonify(response)


@app_v1.route('/remove_from_cart', methods = ['POST'])
def remove_from_cart():
	g.UUID = uuid.uuid4()
	logger.info('START_CALL [%s] Request_url = [%s], arguments = [%s]', g.UUID, str(request.url), json.dumps(request.data))
	response = CartService().remove_from_cart(request.data)
	logger.info('[%s] END_OF_CALL [%s]', g.UUID, json.dumps(response))
	return flask.jsonify(response)

@app_v1.route('/order_count', methods=['GET'])
def get_order_count():
	g.UUID = uuid.uuid4()
	logger.info('START_CALL [%s] Request_url = [%s], arguments = [%s]', g.UUID, str(request.url), json.dumps(request.args))
	if request.args.__len__() == 0:
		response = create_error_response(ERROR.VALIDATION_ERROR)
	else:
		response = get_order_count_for_today(request.args)
	logger.info('[%s] END_OF_CALL [%s]', g.UUID, json.dumps(response))
	return flask.jsonify(response)
