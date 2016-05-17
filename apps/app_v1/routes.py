from apps.app_v1.api import NetworkError
from apps.app_v1.api.cart_service import CartService

from flask import request, g
from config import APP_NAME
from utils.jsonutils.output_formatter import create_error_response
import logging, uuid
from . import app_v1
from apps.app_v1.api import ERROR
from requests.exceptions import ConnectionError
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


# @app_v1.route('/order', methods=['POST'])
# @jsonify
# @logrequest
# def createOrder():
#     logger.info(
#         '%s : Requested url = <%s> , arguments = <%s>' % ('/cart', str(request.url), str(request.args)))
#     g.UUID = uuid.uuid4()
#     try:
#         order_service = OrderService()
#         return order_service.createOrder(request.data)
#     except NetworkError as ne:
#         logger.error("{%s} Netwrork Error occured in order service {%s}" % (g.UUID, str(ne)), exc_info=True)
#         return create_error_response(code=error_code["network_error"], message=error_messages["network_error"])
#     except ConnectionError:
#         return create_error_response(code=error_code["connection_error"], message=error_messages["connection_error"])
#     except Exception as e:
#         logger.error("{%s} Exception occured in order service {%s}" % (g.UUID, str(e)), exc_info=True)
#         return create_error_response(code=error_code["order_error"], message=error_messages["order_error"])
