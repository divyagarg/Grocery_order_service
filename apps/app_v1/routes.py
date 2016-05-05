from apps.app_v1.api.cart_service import CartService
from flask import request, g, Blueprint
from config import APP_NAME
from utils.jsonutils.output_formatter import create_error_response
import logging, uuid
from . import app_v1

from lib.decorators import jsonify, logrequest
logger = logging.getLogger(APP_NAME)



@app_v1.route('/test', methods=['GET'])
@jsonify
@logrequest
def test():
  logger.info("Getting call for test function with request data %s", request.data)
  result = {"success": True}
  return result



@app_v1.route('/cart', methods =['POST'])
def createOrUpdateCart():
  logger.info(
        '%s : Requested url = <%s> , arguments = <%s>' % ('/cart', str(request.url), str(request.args)))
  g.UUID = uuid.uuid4()
  try:
    cartservice = CartService()
    return cartservice.createOrUpdateCart(request.data)
  except Exception as e:
    logger.error("Exception occured in cart service {%s}" %g.UUID, exe_info = True)
    return create_error_response(message=str(e))
