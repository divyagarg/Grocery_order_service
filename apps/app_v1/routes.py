from flask import request
from flask import Blueprint
import logging

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
