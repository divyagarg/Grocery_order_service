__author__ = 'divyagarg'
from config import RESPONSE_JSON

def create_error_response(code=401, message='Internal Error occured'):
    settings = RESPONSE_JSON
    response_json = settings['RESPONSE_JSON'].copy()
    error_response = settings['ERROR_RESPONSE'].copy()

    error_response['code'] = int(code)
    error_response['message'] = message

    response_json['status'] = 'failure'
    response_json['error'] = error_response

    return response_json


def create_data_response(data=None):
    settings = RESPONSE_JSON
    response_json = settings['RESPONSE_JSON'].copy()
    response_json['status'] = 'success'
    return response_json