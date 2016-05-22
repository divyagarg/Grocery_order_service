
from apps.app_v1.api.cart_service import CartService
from apps.app_v1.api.order_service import OrderService
from flask import request, g
from config import APP_NAME
from utils.jsonutils.output_formatter import create_error_response
import logging, uuid
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
    logger.info(
        '%s : Requested url = <%s> , arguments = <%s>' % ('/cart', str(request.url), str(request.args)))
    g.UUID = uuid.uuid4()
    try:
        cartservice = CartService()
        return cartservice.create_or_update_cart(request.data)
    except Exception as e:
        logger.error("{%s} Exception occured in cart service {%s}" % (g.UUID, str(e)), exc_info=True)
        ERROR.INTERNAL_ERROR.message = str(e)
        return create_error_response(ERROR.INTERNAL_ERROR)


@app_v1.route('/add_to_cart', methods =['POST'])
@jsonify
@logrequest
def add_item_to_cart_and_get_count_of_items():
    logger.info(
        '%s : Requested url = <%s> , arguments = <%s>' % ('/cart', str(request.url), str(request.args)))
    g.UUID = uuid.uuid4()
    try:
        cartservice = CartService()
        return cartservice.add_item_to_cart(request.data)
    except Exception as e:
        logger.error("{%s} Exception occured in getting count of cart items {%s}" % (g.UUID, str(e)), exc_info=True)
        ERROR.INTERNAL_ERROR.message = str(e)
        return create_error_response(ERROR.INTERNAL_ERROR)



@app_v1.route('/user/<user_id>', methods = ['GET'])
@jsonify
@logrequest

def get_count_of_orders_of_a_user(user_id):
    logger.info('[%s] : Requested url = <%s> , arguments = <%s>, user_id =<%s>' % ('/user', str(request.url), str(request.args), user_id))
    g.UUID = uuid.uuid4()
    try:
        order_service = OrderService()
        return order_service.get_count_of_orders_of_user(user_id)
    except Exception as e:
        logger.error("{%s} Exception occured in getting count of orders of a user {%s}" % (g.UUID, str(e)), exc_info=True)
        ERROR.INTERNAL_ERROR.message = str(e)
        return create_error_response(ERROR.INTERNAL_ERROR)


@app_v1.route('/order', methods=['POST'])
@jsonify
@logrequest
def createOrder():
    logger.info(

        '[%s] : Requested url = <%s> , arguments = <%s>' % ('/cart', str(request.url), str(request.args)))
    g.UUID = uuid.uuid4()
    try:
        order_service = OrderService()
        return order_service.createorder(request.data)
    except Exception as e:
        logger.error("{%s} Exception occured in order service {%s}" % (g.UUID, str(e)), exc_info=True)
        ERROR.INTERNAL_ERROR.message = str(e)
        return create_error_response(ERROR.INTERNAL_ERROR)