from apps.app_v1.api.cart_service import CartService
from flask import request, g, Blueprint
import logging, uuid

from lib.decorators import jsonify, logrequest
logger = logging.getLogger()

app_v1 = Blueprint('app_v1', __name__)

@app_v1.route('/test', methods=['GET'])
@jsonify
@logrequest
def test():
  logger.info("Getting call for test function with request data %s", request.data)
  result = {"success": True}
  return result



@app_v1.route('/cart', methods =['POST'])
@jsonify
def createOrUpdateCart():
  logger.info(
        '%s : Requested url = <%s> , arguments = <%s>' % ('/cart', str(request.url), str(request.args)))
  g.UUID = uuid.uuid4()
  cartservice = CartService()
  return cartservice.createOrUpdateCart()