import json
from apps.app_v1.api.cart_service import CartService
from apps.app_v1.api.delivery_service import DeliveryService
from apps.app_v1.api.order_service import OrderService
from apps.app_v1.api.payment_service import PaymentInfo
from flask import request, g
from config import APP_NAME
import flask
from utils.jsonutils.output_formatter import create_error_response
import logging
import uuid
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
	logger.info('START CALL [%s] %s :, arguments = <%s>' % (g.UUID, '/cart', json.dumps(request.data)))
	try:
		cartservice = CartService()
		response = cartservice.create_or_update_cart(request.data)
		logger.info("[%s] END OF CALL [%s]" % (g.UUID, json.dumps(response)))
		return response
	except Exception as e:
		logger.error("[%s] Exception occured in cart service [%s]" % (g.UUID, str(e)), exc_info=True)
		ERROR.INTERNAL_ERROR.message = str(e)
		return create_error_response(ERROR.INTERNAL_ERROR)


@app_v1.route('/add_to_cart', methods=['POST'])
@jsonify
@logrequest
def add_item_to_cart_and_get_count_of_items():
	g.UUID = uuid.uuid4()
	logger.info(
		'START CALL [%s] %s : Requested url = <%s> , arguments = <%s>' % (
			g.UUID, '/cart', str(request.url), json.dumps(request.data)))
	try:
		cartservice = CartService()
		response = cartservice.add_item_to_cart(request.data)
		logger.info("[%s] END OF CALL" % g.UUID)
		return response
	except Exception as e:
		logger.error("[%s] Exception occured in getting count of cart items [%s]" % (g.UUID, str(e)), exc_info=True)
		ERROR.INTERNAL_ERROR.message = str(e)
		return create_error_response(ERROR.INTERNAL_ERROR)


@app_v1.route('/user/<user_id>', methods=['GET'])
@jsonify
@logrequest
def get_count_of_orders_of_a_user(user_id):
	g.UUID = uuid.uuid4()
	logger.info('START CALL [%s]  [%s] : Requested url = <%s> , arguments = <%s>, user_id =<%s>' % (
		g.UUID, '/user', str(request.url), json.dumps(request.data), user_id))
	try:
		order_service = OrderService()
		response = order_service.get_count_of_orders_of_user(user_id)
		logger.info("[%s] END OF CALL" % g.UUID)
		return response
	except Exception as e:
		logger.error("[%s] Exception occured in getting count of orders of a user [%s]" % (g.UUID, str(e)),
					 exc_info=True)
		ERROR.INTERNAL_ERROR.message = str(e)
		return create_error_response(ERROR.INTERNAL_ERROR)


@app_v1.route('/order', methods=['POST'])
@jsonify
@logrequest
def order():
	g.UUID = uuid.uuid4()
	logger.info(
		'START CALL [%s] [%s] : Requested url = <%s> , arguments = <%s>' % (
			g.UUID, '/order', str(request.url), json.dumps(request.data)))

	try:
		order_service = OrderService()
		response = order_service.createorder(request.data)
		logger.info("[%s] END OF CALL [%s]" % (g.UUID, json.dumps(response)))
		return response
	except Exception as e:
		logger.error("[%s] Exception occured in order service [%s]" % (g.UUID, str(e)), exc_info=True)
		ERROR.INTERNAL_ERROR.message = str(e)
		return create_error_response(ERROR.INTERNAL_ERROR)


@app_v1.route('/delivery', methods=['POST'])
@jsonify
@logrequest
def delivery_info():
	g.UUID = uuid.uuid4()
	logger.info(
		'START CALL [%s] [%s] : Requested url = <%s> , arguments = <%s>' % (
			g.UUID, '/delivery', str(request.url), json.dumps(request.data)))

	try:
		delivery_service = DeliveryService()
		response = delivery_service.get_delivery_info(request.data)
		logger.info("[%s] END OF CALL [%s]" % (g.UUID, json.dumps(response)))
		return response
	except Exception as e:
		logger.error("[%s] Exception occured in delivery service [%s]" % (g.UUID, str(e)), exc_info=True)
		ERROR.INTERNAL_ERROR.message = str(e)
		return create_error_response(ERROR.INTERNAL_ERROR)


@app_v1.route('/slot', methods=['POST'])
@jsonify
@logrequest
def slot():
	logger.info(
		'START CALL [%s] [%s] : Requested url = <%s> , arguments = <%s>' % (
			g.UUID, '/slot', str(request.url), json.dumps(request.data)))
	g.UUID = uuid.uuid4()
	try:
		delivery_service = DeliveryService()
		response = delivery_service.update_slot(request.data)
		logger.info("[%s] END OF CALL [%s]" % (g.UUID, json.dumps(response)))
		return response
	except Exception as e:
		logger.error("[%s] Exception occured in delivery service [%s]" % (g.UUID, str(e)), exc_info=True)
		ERROR.INTERNAL_ERROR.message = str(e)
		return create_error_response(ERROR.INTERNAL_ERROR)


@app_v1.route('/get_order_prices', methods=['POST'])
def get_order_prices():
	g.UUID = uuid.uuid4()
	logger.info('START CALL [%s] [%s] : Requested url = <%s> , arguments = <%s>' % (
		g.UUID, '/get_order_price', str(request.url), json.dumps(request.data)))
	order_info = PaymentInfo()
	response = order_info.get_order_prices(request)
	logger.info('[%s] END OF CALL [%s]' % (g.UUID, json.dumps(response)))
	return flask.jsonify(response)


@app_v1.route('/update_payment_details', methods=['POST'])
def update_payment_details():
	g.UUID = uuid.uuid4()
	logger.info('START CALL [%s] [%s] : Requested url = <%s> , arguments = <%s>' % (
		g.UUID, '/update_payment_details', str(request.url), json.dumps(request.data)))

	order_info = PaymentInfo()
	response = order_info.update_payment_details(request)
	logger.info('[%s] END OF CALL [%s]' % (g.UUID, json.dumps(response)))
	return flask.jsonify(response)


@app_v1.route('/get_payment_details', methods=['POST'])
def get_payment_details():
	g.UUID = uuid.uuid4()
	logger.info('START CALL [%s] [%s] : Requested url = <%s> , arguments = <%s>' % (
		g.UUID, '/get_payment_details', str(request.url), json.dumps(request.data)))
	order_info = PaymentInfo()
	response = order_info.get_payment_details(request)
	logger.info('[%s] END OF CALL [%s]' % (g.UUID, json.dumps(response)))
	return flask.jsonify(response)


@app_v1.route('/change_user', methods=['POST'])
def change_user():
	g.UUID = uuid.uuid4()
	logger.info('START CALL [%s] [%s] : Requested url = <%s> , arguments = <%s>' % (
		g.UUID, '/change_user', str(request.url), json.dumps(request.data)))
	cart_service = CartService()
	response = cart_service.change_user(request.data)
	logger.info('[%s] END OF CALL [%s]' % (g.UUID, json.dumps(response)))
	return flask.jsonify(response)
