import os

HOME = '/tmp'
HOME = os.environ.get('LOG_HOME') or HOME

LOG_DIR = 'order_service'
LOG_FILE = 'order_service.log'
DEBUG_LOG_FILE = 'order_service_debug.log'
ERROR_LOG_FILE = 'order_service_error.log'

PORT = 9000
APP_NAME = 'order_service'
error_code = {
    "discount_changed": 1001,
    "product_offer_price_changes": 1002,
    "product_display_price_changes": 1003,
    "product_availability_changed": 1004,
    "payment_mode_not_allowed": 1005,
    "freebie_not_allowed": 1006,
    "coupon_not_applid_for_channel": 1007,
    "coupon_service_returning_failure_status": 1008,
    "cart_error":1009,
    "order_error":1010,
    "order_validation_request_error": 1011,
    "network_error":1012,
    "connection_error": 1013
}

error_messages = {
    "discount_changed": "Discount not applicable",
    "product_offer_price_changes": "Product price changed",
    "product_display_price_changes":"Product display prices changed",
    "product_availability_changed": "Product is not available in the given quantity",
    "payment_mode_not_allowed": "Selected Payment mode is not applicable for this order",
    "freebie_not_allowed": "Freebie not allowed for this order",
    "coupon_not_applid_for_channel" : "Coupon is not applicable for this channel",
    "coupon_service_returning_failure_status": "Coupon service returning failure status",
    "cart_error":"Error in updating cart",
    "order_error":"Order Error",
    "order_validation_request_error": "Order Request Validation Failed",
    "network_error": "Network Error",
    "connection_error": "Connection Error"
}


class Config:
    DEBUG = False
    TESTING = False

    def __init__(self):
        pass

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    HOME = '/tmp'
    ENV = 'development'
    DEBUG = True
    DATABASE_NAME = 'grocery_order_service'
    DATABASE_URI = 'mysql+pymysql://root@localhost:3306/'
    SECRET_KEY = 'hard to guess string'
    # KAFKA_HOSTS = ['dc1.staging.askme.com:9092', 'dc2.staging.askme.com:9092']
    # KAFKA_TOPIC = 'fulfillment_staging'
    # KAKFA_GROUP = 'fulfillmentservice_group'
    SQLALCHEMY_DATABASE_URI = DATABASE_URI + DATABASE_NAME
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_TIMEOUT = 20
    PRODUCT_CATALOGUE_URL = "http://pyservice01.staging.askme.com:9056/catalog/v1/calculate_price"
    COUPON_CHECK_URL = "http://pyservice01.staging.askme.com:9933/vouchers/v1/check"
    COUPOUN_APPLY_URL = "http://pyservice01.staging.askme.com:9933/vouchers/"


class TestingConfig(Config):
    HOME = '/tmp'
    ENV = 'testing'
    TESTING = True
    DEBUG = True
    DATABASE_NAME = 'grocery_order_service'
    DATABASE_URI = 'mysql+pymysql://root@localhost:3306/'
    SECRET_KEY = 'hard to guess string'
    # KAFKA_HOSTS = ['dc1.staging.askme.com:9092', 'dc2.staging.askme.com:9092']
    # KAFKA_TOPIC = 'fulfillment_staging'
    # KAKFA_GROUP = 'fulfillmentservice_group'
    SQLALCHEMY_DATABASE_URI = DATABASE_URI + DATABASE_NAME
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_TIMEOUT = 20
    PRODUCT_CATALOGUE_URL = "http://pyservice01.staging.askme.com:9056/catalog/v1/calculate_price"
    COUPON_CHECK_URL = "http://pyservice01.staging.askme.com:9933/vouchers/v1/check"
    COUPOUN_APPLY_URL = "http://pyservice01.staging.askme.com:9933/vouchers/"
    # SERVER_NAME="http://127.0.0.1:9000/"


class StagingConfig(Config):
    HOME = '/tmp'
    ENV = 'development'
    DEBUG = True
    DATABASE_NAME = 'grocery_order_service'
    DATABASE_URI = 'mysql+pymysql://root@localhost:3306/'
    SECRET_KEY = 'hard to guess string'
    # KAFKA_HOSTS = ['dc1.staging.askme.com:9092', 'dc2.staging.askme.com:9092']
    # KAFKA_TOPIC = 'fulfillment_staging'
    # KAKFA_GROUP = 'fulfillmentservice_group'
    SQLALCHEMY_DATABASE_URI = DATABASE_URI + DATABASE_NAME
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_TIMEOUT = 20
    PRODUCT_CATALOGUE_URL = "http://pyservice01.staging.askme.com:9056/catalog/v1/calculate_price"
    COUPON_CHECK_URL = "http://pyservice01.staging.askme.com:9933/vouchers/v1/check"
    COUPOUN_APPLY_URL = "http://pyservice01.staging.askme.com:9933/vouchers/"


class ProductionConfig(Config):
    HOME = '/tmp'
    ENV = 'development'
    DEBUG = True
    DATABASE_NAME = 'grocery_order_service'
    DATABASE_URI = 'mysql+pymysql://root@localhost:3306/'
    SECRET_KEY = 'hard to guess string'
    # KAFKA_HOSTS = ['dc1.staging.askme.com:9092', 'dc2.staging.askme.com:9092']
    # KAFKA_TOPIC = 'fulfillment_staging'
    # KAKFA_GROUP = 'fulfillmentservice_group'
    SQLALCHEMY_DATABASE_URI = DATABASE_URI + DATABASE_NAME
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_TIMEOUT = 20
    PRODUCT_CATALOGUE_URL = "http://pyservice01.staging.askme.com:9056/catalog/v1/calculate_price"
    COUPON_CHECK_URL = "http://pyservice01.staging.askme.com:9933/vouchers/v1/check"
    COUPOUN_APPLY_URL = "http://pyservice01.staging.askme.com:9933/vouchers/"


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

RESPONSE_JSON = {
    'RESPONSE_JSON': {
        'status': ''
    },
    'ERROR_RESPONSE': {
        'code': '',
        'message': ''
    },
}

