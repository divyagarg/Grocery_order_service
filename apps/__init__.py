from flask import Flask
import lib.log as log

def create_app():
  app = Flask(__name__)
  from app_v1.routes import app_v1 as v1_router
  app.register_blueprint(v1_router, url_prefix='/v1')
  log.setup_logging()
  return app
