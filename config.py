import os

HOME = '/tmp'
HOME = os.environ.get('LOG_HOME') or HOME
LOG_DIR = 'newapp'
LOG_FILE = 'newapp.log'
DEBUG_LOG_FILE = 'newapp_debug.log'
ERROR_LOG_FILE = 'newapp_error.log'

PORT = 9000

class Config:
    DEBUG = False
    TESTING = False

    def __init__(self):
        pass

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    HOME='/tmp'
    ENV = 'development'
    DEBUG = True
    DATABASE_NAME = 'grocery_order_service'
    DATABASE_URI = 'mysql+pymysql://root@localhost:3306/'
    SECRET_KEY = 'hard to guess string'
    # KAFKA_HOSTS = ['dc1.staging.askme.com:9092', 'dc2.staging.askme.com:9092']
    # KAFKA_TOPIC = 'fulfillment_staging'
    # KAKFA_GROUP = 'fulfillmentservice_group'
    SQLALCHEMY_DATABASE_URI = DATABASE_URI+DATABASE_NAME
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_TIMEOUT= 20

config = {
    'development': DevelopmentConfig,
    # 'testing': TestingConfig,
    # 'staging': StagingConfig,
    # 'production': ProductionConfig,
    'default': DevelopmentConfig
}


