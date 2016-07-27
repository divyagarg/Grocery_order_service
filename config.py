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
SHIPPING_COST_THRESHOLD = 250
PUBLISH_TO_KAFKA = True
SEARCH_API_SELECT_CLAUSE = ["deliveryDays", "transferPrice", "maxQuantity"]
COUPON_QUERY_PARAM ="?check_payment_mode=true"

class Config:
	DEBUG = False
	TESTING = False
	API_TIMEOUT = 5
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
	SQLALCHEMY_POOL_RECYCLE = 1750
	PRODUCT_CATALOGUE_URL = "http://pyservice01.staging.askme.com:9070/v1/search"
	COUPON_CHECK_URL = "http://pyservice01.staging.askme.com:8823/vouchers/grocery/v1/check"
	COUPOUN_APPLY_URL = "http://pyservice01.staging.askme.com:8823/vouchers/grocery/v1/apply"
	SHIPMENT_PREVIEW_URL = "http://pyservice01.staging.askme.com:9981/fulfilments/v1/order/getShipmentOptions"
	PAYMENT_SERVICE_URL = "http://pyservice01.staging.askme.com:13000/payment_service/api/paas/v1/paymentstatus"
	X_API_USER = "askmegrocery"
	X_API_TOKEN = "M2JmN2U5NGYtMDJlNi0xMWU2LWFkZGQtMjRhMDc0ZjE1MGYy"
	KAFKA_TOPIC = 'grocery_orderservice_staging'
	KAFKA_HOSTS = ['dc1.staging.askme.com:9092', 'dc2.staging.askme.com:9092']
	#OPS_PANEL_CREATE_ORDER_URL = "http://uat.api.askmegrocery.com/api/generateorder"
	#SMS_SERVICE_URL = "http://notificationservicerest.getit.in/NotificationServiceRest.svc/sendsms?UserId=best_user@&Password=best_user@pwd&Token=987654321&ApplicationId=73&vendorid=groceryapp"

class DevelopmentConfig1(Config):
	HOME = '/tmp'
	ENV = 'development'
	DEBUG = True
	DATABASE_NAME = 'grocery_order_service_v1'
	DATABASE_URI = 'mysql+pymysql://root@localhost:3306/'
	SECRET_KEY = 'hard to guess string'
	# KAFKA_HOSTS = ['dc1.staging.askme.com:9092', 'dc2.staging.askme.com:9092']
	# KAFKA_TOPIC = 'fulfillment_staging'
	# KAKFA_GROUP = 'fulfillmentservice_group'
	SQLALCHEMY_DATABASE_URI = DATABASE_URI + DATABASE_NAME
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	SQLALCHEMY_POOL_SIZE = 100
	SQLALCHEMY_POOL_TIMEOUT = 20
	SQLALCHEMY_POOL_RECYCLE = 1750
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
	SQLALCHEMY_POOL_TIMEOUT = 5
	SQLALCHEMY_POOL_RECYCLE = 1750
	SQLALCHEMY_ECHO = True
	PRODUCT_CATALOGUE_URL = "http://pyservice01.staging.askme.com:9070/v1/search"
	COUPON_CHECK_URL = "http://pyservice01.staging.askme.com:8823/vouchers/grocery/v1/check"
	COUPOUN_APPLY_URL = "http://pyservice01.staging.askme.com:8823/vouchers/grocery/v1/apply"
	SHIPMENT_PREVIEW_URL = "http://pyservice01.staging.askme.com:9981/fulfilments/v1/order/getShipmentOptions"
	X_API_USER = "askmegrocery"
	X_API_TOKEN = "M2JmN2U5NGYtMDJlNi0xMWU2LWFkZGQtMjRhMDc0ZjE1MGYy"

	KAFKA_TOPIC = 'grocery_orderservice_staging'
	#KAFKA_HOSTS = ['dc1.staging.askme.com:9092', 'dc2.staging.askme.com:9092']
	KAFKA_HOSTS= ['kafka01.production.askmebazaar.com:9092', 'kafka02.production.askmebazaar.com:9092','kafka03.production.askmebazaar.com:9092']

	PAYMENT_SERVICE_URL = "http://pyservice01.staging.askme.com:13000/payment_service/api/paas/v1/paymentstatus"
	OPS_PANEL_CREATE_ORDER_URL = "http://uatapi.intern.askmegrocery.com/api/generateorder"
	SMS_SERVICE_URL = "http://notificationservicerest.getit.in/NotificationServiceRest.svc/sendsms?UserId=best_user@&Password=best_user@pwd&Token=987654321&ApplicationId=73&vendorid=groceryapp"
	COD_ORDER_CONFIRMATION_SMS_TEXT_TWO_SHIPMENTS = "Your order has been placed and will be delivered in 2 shipments, Shipment ID 1: %s and Shipment ID 2: %s. Thanks for choosing askmegrocery.com."
	COD_ORDER_CONFIRMATION_SMS_TEXT_ONE_SHIPMENT = "Your order has been placed and the Shipment ID is %s. Thanks for choosing askmegrocery.com."
	PREPAID_ORDER_CONFIRMATION_SMS_TEXT_ONE_SHIPMENT = "Payment successful! Your order number has been confirmed and will be delivered in 2 shipments, Shipment ID 1: %s and Shipment ID 2: %s. Thanks for choosing askmegrocery.com as your shopping destination for grocery."
	PREPAID_ORDER_CONFIRMATION_SMS_TEXT_TWO_SHIPMENTS = "Payment successful! Your order number has been confirmed and will be delivered in 2 shipments, Shipment ID 1: %s and Shipment ID 2: %s. Thanks for choosing askmegrocery.com as your shopping destination for grocery."


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
	SQLALCHEMY_POOL_TIMEOUT = 5
	SQLALCHEMY_POOL_RECYCLE = 1750
	PRODUCT_CATALOGUE_URL = "http://api-internal.askme.com/unified/v1/search"
	COUPON_CHECK_URL = "http://api-internal.askme.com/coupon/vouchers/grocery/v1/check"
	COUPOUN_APPLY_URL = "http://api-internal.askme.com/coupon/vouchers/grocery/v1/apply"
	SHIPMENT_PREVIEW_URL = "http://api-internal.askme.com/fulfilments/v1/order/getShipmentOptions"
	PAYMENT_SERVICE_URL = "https://api.askme.com/payment_service/api/paas/v1/paymentstatus"
	PAYMENT_AUTH_KEY = "553dd18b3199a533a9000001616c2be33cd24735432775949282dc3a"
	X_API_USER = "newaskmegrocery"
	X_API_TOKEN = "ceeb2741064966a6cfe0bb3a722eab772d908b90967eb7585ecf0852960ac279"

	KAFKA_HOSTS= ['kafka01.production.askmebazaar.com:9092', 'kafka02.production.askmebazaar.com:9092','kafka03.production.askmebazaar.com:9092']
	KAFKA_TOPIC = 'grocery_orderservice_prod'

	OPS_PANEL_CREATE_ORDER_URL = "http://api.askmegrocery.com/api/GenerateOrder"
	SMS_SERVICE_URL = "http://notificationservicerest.getit.in/NotificationServiceRest.svc/sendsms?UserId=best_user@&Password=best_user@pwd&Token=987654321&ApplicationId=73&vendorid=groceryapp"
	COD_ORDER_CONFIRMATION_SMS_TEXT_TWO_SHIPMENTS = "Your order has been placed and will be delivered in 2 shipments, Shipment ID 1: %s and Shipment ID 2: %s. Thanks for choosing askmegrocery.com."
	COD_ORDER_CONFIRMATION_SMS_TEXT_ONE_SHIPMENT = "Your order has been placed and the Shipment ID is %s. Thanks for choosing askmegrocery.com."
	PREPAID_ORDER_CONFIRMATION_SMS_TEXT_ONE_SHIPMENT = "Payment successful! Your order number has been confirmed and will be delivered in 2 shipments, Shipment ID 1: %s and Shipment ID 2: %s. Thanks for choosing askmegrocery.com as your shopping destination for grocery."
	PREPAID_ORDER_CONFIRMATION_SMS_TEXT_TWO_SHIPMENTS = "Payment successful! Your order number has been confirmed and will be delivered in 2 shipments, Shipment ID 1: %s and Shipment ID 2: %s. Thanks for choosing askmegrocery.com as your shopping destination for grocery."



config = {
	'development': DevelopmentConfig,
	'development1': DevelopmentConfig1,
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
