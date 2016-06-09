import logging

from flask import Flask
import lib.log as log
from apps.app_v1.models import initialize_db
from config import config, APP_NAME
from utils.kafka_utils.kafka_publisher import Publisher

Logger = logging.getLogger(APP_NAME)


def create_app(config_name):
	app = Flask(__name__)
	app.config.from_object(config[config_name])
	config[config_name].init_app(app)
	log.setup_logging(config[config_name])
	initialize_db(app)
	Publisher.init(app)

	from apps.app_v1.routes import app_v1 as v1_router
	app.register_blueprint(v1_router, url_prefix='/grocery_orderapi/v1')
	return app
