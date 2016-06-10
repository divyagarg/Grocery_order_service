import os

HOME = '/tmp'
HOME = os.environ.get('LOG_HOME') or HOME

LOG_DIR = 'grocery_order_service'
LOG_FILE = 'grocery_order_service.log'
DEBUG_LOG_FILE = 'grocery_order_service_debug.log'
ERROR_LOG_FILE = 'grocery_order_service_error.log'
DB_FILE = 'grocery_order_service_db.log'

PORT = 9000
APP_NAME = 'grocery_order_service'

SHIPPING_COST = 30.0
SHIPPING_COST_THRESHOLD = 1000
PUBLISH_TO_KAFKA = True
SEARCH_API_SELECT_CLAUSE = ["deliveryDays", "transferPrice", "maxQuantity"]
COUPON_QUERY_PARAM ="?check_payment_mode=true"

class Config:
	DEBUG = False
	TESTING = False
	API_TIMEOUT = 10
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
	SQLALCHEMY_POOL_SIZE = 100
	SQLALCHEMY_POOL_TIMEOUT = 20
	PRODUCT_CATALOGUE_URL = "http://pyservice01.staging.askme.com:9070/v1/search"
	COUPON_CHECK_URL = "http://pyservice01.staging.askme.com:8823/vouchers/grocery/v1/check"
	COUPOUN_APPLY_URL = "http://pyservice01.staging.askme.com:8823/vouchers/grocery/v1/apply"
	SHIPMENT_PREVIEW_URL = "http://pyservice01.staging.askme.com:9981/fulfilments/v1/order/getShipmentOptions"
	PAYMENT_SERVICE_URL = "http://pyservice01.staging.askme.com:13000/payment_service/api/paas/v1/paymentstatus"
	X_API_USER = "askmegrocery"
	X_API_TOKEN = "M2JmN2U5NGYtMDJlNi0xMWU2LWFkZGQtMjRhMDc0ZjE1MGYy"
	KAFKA_TOPIC = 'grocery_orderservice_staging'
	KAFKA_HOSTS = ['dc1.staging.askme.com:9092', 'dc2.staging.askme.com:9092']



class TestingConfig(Config):
	HOME = '/tmp'
	ENV = 'testing'
	TESTING = True
	DEBUG = True
	DATABASE_NAME = 'test_grocery_order_service'
	DATABASE_URI = 'mysql+pymysql://root@localhost:3306/'
	SECRET_KEY = 'hard to guess string'
	KAFKA_HOSTS = ['dc1.staging.askme.com:9092', 'dc2.staging.askme.com:9092']
	KAFKA_TOPIC = 'grocery_orderservice_staging'
	# KAKFA_GROUP = 'fulfillmentservice_group'
	SQLALCHEMY_DATABASE_URI = DATABASE_URI + DATABASE_NAME
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	SQLALCHEMY_POOL_SIZE = 10
	SQLALCHEMY_POOL_TIMEOUT = 20
	PRODUCT_CATALOGUE_URL = "http://pyservice01.staging.askme.com:9070/v1/search"
	COUPON_CHECK_URL = "http://pyservice01.staging.askme.com:8823/vouchers/grocery/v1/check"
	COUPOUN_APPLY_URL = "http://pyservice01.staging.askme.com:8823/vouchers/grocery/v1/apply"
	SHIPMENT_PREVIEW_URL = "http://pyservice01.staging.askme.com:9981/fulfilments/v1/order/getShipmentOptions"
	X_API_USER = "askmegrocery"
	X_API_TOKEN = "M2JmN2U5NGYtMDJlNi0xMWU2LWFkZGQtMjRhMDc0ZjE1MGYy"
	PAYMENT_SERVICE_URL = "http://pyservice01.staging.askme.com:13000/payment_service/api/paas/v1/paymentstatus"



class StagingConfig(Config):
	HOME = '/var/log/'
	ENV = 'staging'
	DEBUG = True
	DATABASE_NAME = 'grocery_order_service'
	DATABASE_URI = 'mysql+pymysql://orderengine:OrderEng1ne@order-engine.c0wj8qdslqom.ap-southeast-1.rds.amazonaws.com/'
	SECRET_KEY = 'hard to guess string'
	SQLALCHEMY_DATABASE_URI = DATABASE_URI + DATABASE_NAME
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	SQLALCHEMY_POOL_SIZE = 100
	SQLALCHEMY_POOL_TIMEOUT = 20

	PRODUCT_CATALOGUE_URL = "http://pyservice01.staging.askme.com:9070/v1/search"
	COUPON_CHECK_URL = "http://pyservice01.staging.askme.com:8823/vouchers/grocery/v1/check"
	COUPOUN_APPLY_URL = "http://pyservice01.staging.askme.com:8823/vouchers/grocery/v1/apply"
	SHIPMENT_PREVIEW_URL = "http://pyservice01.staging.askme.com:9981/fulfilments/v1/order/getShipmentOptions"
	X_API_USER = "askmegrocery"
	X_API_TOKEN = "M2JmN2U5NGYtMDJlNi0xMWU2LWFkZGQtMjRhMDc0ZjE1MGYy"
	KAFKA_TOPIC = 'grocery_orderservice_staging'
	KAFKA_HOSTS = ['dc1.staging.askme.com:9092', 'dc2.staging.askme.com:9092']
	PAYMENT_SERVICE_URL = "http://pyservice01.staging.askme.com:13000/payment_service/api/paas/v1/paymentstatus"



class ProductionConfig(Config):
	HOME = '/var/log/'
	ENV = 'production'
	DEBUG = True
	DATABASE_NAME = 'grocery_order_service'
	DATABASE_URI = 'mysql+pymysql://OrderEngine:OrderEngine1234@orderengineproduction.c0wj8qdslqom.ap-southeast-1.rds.amazonaws.com/'
	SECRET_KEY = 'hard to guess string'

	SQLALCHEMY_DATABASE_URI = DATABASE_URI + DATABASE_NAME
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	SQLALCHEMY_POOL_SIZE = 100
	SQLALCHEMY_POOL_TIMEOUT = 20
	PRODUCT_CATALOGUE_URL = "http://api-internal.askme.com/unified/v1/search"
	COUPON_CHECK_URL = "http://pyservice01.staging.askme.com:8823/vouchers/grocery/v1/check"
	COUPOUN_APPLY_URL = "http://pyservice01.staging.askme.com:8823/vouchers/grocery/v1/apply"
	SHIPMENT_PREVIEW_URL = "http://api-service04.production.askme.com:9981/fulfilments/v1/order/getShipmentOptions"
	PAYMENT_SERVICE_URL = "https://api.askme.com/payment_service/api/paas/v1/paymentstatus"
	PAYMENT_AUTH_KEY = "553dd18b3199a533a9000001616c2be33cd24735432775949282dc3a"
	X_API_USER = "askmegrocery"
	X_API_TOKEN = "M2JmN2U5NGYtMDJlNi0xMWU2LWFkZGQtMjRhMDc0ZjE1MGYy"

	KAFKA_HOSTS= ['kafka01.production.askmebazaar.com:9092', 'kafka02.production.askmebazaar.com:9092','kafka03.production.askmebazaar.com:9092']
	KAFKA_TOPIC = 'grocery_orderservice_staging'


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
