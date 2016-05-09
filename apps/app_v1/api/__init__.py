import json
from config import APP_NAME
import logging
from flask import g

__author__ = 'divyagarg'

Logger = logging.getLogger(APP_NAME)


def parse_request_data(body):
    Logger.info('{%s} Received request to create cart for request {%s}' % (g.UUID, body))
    json_data = json.loads(body)
    Logger.info('{%s} Json encoded content {%s}' % (g.UUID, json_data))
    return json_data


class NetworkError(RuntimeError):
    def __init__(self, arg):
        self.args = arg
