import lib.log as log
from apps.app_v1.models import initialize_db
from config import config, APP_NAME
import json, logging
from flask import Flask, Response

Logger = logging.getLogger(APP_NAME)

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    log.setup_logging(config[config_name])
    initialize_db(app)

    from app_v1.routes import app_v1 as v1_router
    app.register_blueprint(v1_router, url_prefix='/orderapi/v1')

    @app.errorhandler(Exception)

    def internal_error(error):
        response_json = {
            'status': 'failure',
            'error': {
                'code': '500',
                'message': 'Internal error occurred'
            }
        }

        data = json.dumps(response_json)
        res = Response(data, mimetype='application/json')
        return res

    @app.errorhandler(500)
    def internal_exception(error):
        response_json = {
            'status': 'failure',
            'error': {
                'code': '500',
                'message': 'Internal error occurred'
            }
        }
        data = json.dumps(response_json)
        res = Response(data, mimetype='application/json')
        return res

    @app.errorhandler(404)
    def internal_exception(error):
        response_json = {
            'status': 'failure',
            'error': {
                'code': '404',
                'message': 'Invalid URL'
            }
        }
        data = json.dumps(response_json)
        res = Response(data, mimetype='application/json')
        return res

    @app.errorhandler(422)
    def internal_exception(error):
        response_json = {
            'status': 'failure',
            'error': {
                'code': '422',
                'message': 'Input request parameters are not valid'
            }
        }
        data = json.dumps(response_json)
        res = Response(data, mimetype='application/json')
        return res


    return app
