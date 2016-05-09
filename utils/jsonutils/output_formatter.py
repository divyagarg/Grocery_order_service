__author__ = 'divyagarg'
from config import RESPONSE_JSON
from flask import Response
import json

def create_error_response(code, message):
    settings = RESPONSE_JSON
    response_json = settings['RESPONSE_JSON'].copy()
    error_response = settings['ERROR_RESPONSE'].copy()

    error_response['code'] = int(code)
    error_response['message'] = message

    response_json['status'] = 'failure'
    response_json['error'] = error_response

    return response_json


def create_data_response(data):
    settings = RESPONSE_JSON
    response_json = settings['RESPONSE_JSON'].copy()
    response_json['status'] = 'success'
    response_json['data'] = data
    return response_json