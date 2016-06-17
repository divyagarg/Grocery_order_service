import json
import logging
import datetime

from requests.exceptions import ConnectTimeout
from flask import g, current_app
import requests
from utils.jsonutils.json_utility import json_serial

from utils.jsonutils.output_formatter import create_error_response, create_data_response
from apps.app_v1.models.models import MasterOrder, Address, Payment, db
from config import APP_NAME
from apps.app_v1.api import ERROR, ServiceUnAvailableException
from utils.kafka_utils.kafka_publisher import Publisher

__author__ = 'amit.bansal'

Logger = logging.getLogger(APP_NAME)

PAYMENT_METHOD = {
	   "CC"  : 0,
	   "DC"  : 1,
	   "NB"  : 2,
	   "PPI" : 3,
	   "COD" : 4
	}

def get_order_prices(request):
	try:
		raw_data = request.data
		Logger.info('{%s} Data from request {%s}', g.UUID, raw_data)
		pure_json = json.loads(raw_data)

		if 'order_id' not in pure_json:
			ERROR.KEY_MISSING.message = 'key missing is order_id'
			return create_error_response(ERROR.KEY_MISSING)

		order_data = MasterOrder.get_order(pure_json['order_id'])
		if order_data is None:
			return create_error_response(ERROR.NO_ORDER_FOUND_ERROR)

		billing_address = Address.find(order_data.billing_address_ref)

		response = {}
		response['order_id'] = order_data.order_id
		response['total_offer_price'] = order_data.total_offer_price
		response['total_shipping_charges'] = order_data.total_shipping
		response['total_discount'] = order_data.total_discount
		response['total_payable_amount'] = order_data.total_payble_amount
		response['user_id'] = order_data.user_id
		response['address'] = billing_address.convert_to_json()
		Logger.info("[%s] Response for Get Order Price is: [%s]", g.UUID,
					json.dumps(response))
		return create_data_response(data=response)

	except Exception as exception:
		Logger.error('{%s} Exception occured ', g.UUID, exc_info=True)
		ERROR.INTERNAL_ERROR.message = str(exception)
		return create_error_response(ERROR.INTERNAL_ERROR)


def save_payment_details(pure_json, order_id):
	payment_objs = list()
	if "childTxns" in pure_json:
		for childTxn in pure_json["childTxns"]:
			payment_data = Payment()
			payment_data.order_id = order_id
			payment_data.payment_gateway = childTxn.get('bankGateway', None)
			payment_data.payment_method = childTxn.get('paymentMode', None)
			payment_data.pg_txn_id = childTxn.get('pgTxnId', None)
			payment_data.txn_date = childTxn.get('txnDate', None)
			payment_data.txn_amt = childTxn.get('txnAmount', 0.0)
			payment_data.bank_txn_id = childTxn.get('bankTxnId', None)
			payment_data.status = childTxn.get('status', 'pending')
			payment_objs.append(payment_data)
	else:
		payment_data = Payment()
		payment_data.order_id = order_id
		payment_data.payment_gateway = pure_json.get('bankGateway', None)
		payment_data.payment_method = pure_json.get('paymentMode', None)
		payment_data.pg_txn_id = pure_json.get('pgTxnId', None)
		payment_data.txn_date = pure_json.get('txnDate', None)
		payment_data.txn_amt = pure_json.get('txnAmount', 0.0)
		payment_data.bank_txn_id = pure_json.get('bankTxnId', None)
		payment_data.status = pure_json.get('status', 'pending')
		payment_objs.append(payment_data)

	# save in DB
	for payment in payment_objs:
		db.session.add(payment)

	return payment_objs


def get_payment_details(request):
	try:
		raw_data = request.data
		Logger.info('{%s} Data from request {%s}', g.UUID, raw_data)
		pure_json = json.loads(raw_data)

		if 'order_id' not in pure_json:
			ERROR.KEY_MISSING.message = 'key missing is order_id'
			return create_error_response(ERROR.KEY_MISSING)

		order_data = MasterOrder.get_order(pure_json['order_id'])

		if order_data is None:
			return create_error_response(ERROR.NO_ORDER_FOUND_ERROR)

		payments = Payment.get_payment_details(pure_json['order_id'])

		if len(payments) == 0:
			# call to payment service api
			url = current_app.config['PAYMENT_SERVICE_URL']
			data = {}
			data['order_id'] = pure_json['order_id']
			data['update_order_service'] = False
			headers = {"Content-type": "application/json"}
			if current_app.config.get("PAYMENT_AUTH_KEY"):
				headers['Authorization'] = current_app.config.get(
					"PAYMENT_AUTH_KEY")

			request = requests.post(url=url, data=json.dumps(data),
									headers=headers,
									timeout=current_app.config[
										'API_TIMEOUT'])
			if request.status_code == 200:
				response = json.loads(request.text)
				if response['status'] == "success":
					# update payment_status in order table
					order_data.payment_status = response['data']['status']
					db.session.add(order_data)
					payments = save_payment_details(response['data'],
													pure_json['order_id'])
					db.session.commit()
				else:
					raise Exception(response['error']["message"])
			else:
				if request.status_code == 404:
					Logger.error("[%s] Payment service is down", g.UUID)
					raise ServiceUnAvailableException(
						ERROR.PAYMENT_SERVICE_IS_DOWN)
				else:
					Logger.error(
						"[%s] Exception occurred in Payment service",
						g.UUID)
					raise Exception("could not get payment details")

		response = {}
		payment_details = list()
		for payment in payments:
			payment_data = {}
			payment_data['payment_gateway'] = payment.payment_gateway
			payment_data['payment_method'] = payment.payment_method
			payment_data['pg_txn_id'] = payment.pg_txn_id
			payment_data['txn_date'] = str(payment.txn_date)
			payment_data['txn_amt'] = payment.txn_amt
			payment_data['bank_txn_id'] = payment.bank_txn_id
			payment_data['status'] = payment.status
			payment_details.append(payment_data)

		response['payment_details'] = payment_details
		response['payment_status'] = order_data.payment_status
		return create_data_response(data=response)

	except ConnectTimeout:
		Logger.error("[%s] Timeout exception for payment api", g.UUID)
		return create_error_response(ERROR.PAYMENT_API_TIMEOUT)
	except ServiceUnAvailableException:
		Logger.error("[%s] Payment service is down", g.UUID)
		return create_error_response(ERROR.PAYMENT_SERVICE_IS_DOWN)
	except Exception as exception:
		Logger.error('{%s} Exception occurred ', g.UUID, exc_info=True)
		ERROR.INTERNAL_ERROR.message = str(exception)
		return create_error_response(ERROR.INTERNAL_ERROR)


def update_payment_details(request):
	required_fields = ["order_id", "status"]
	required_fields_in_child_txn = ["paymentMode"]
	try:
		raw_data = request.data
		Logger.info('{%s} Data from request {%s}', g.UUID, raw_data)
		pure_json = json.loads(raw_data)

		for field in required_fields:
			if field not in pure_json:
				ERROR.KEY_MISSING.message = 'key missing is %s' % field
				return create_error_response(ERROR.KEY_MISSING)

		order_data = MasterOrder.get_order(pure_json['order_id'])
		if order_data is None:
			return create_error_response(ERROR.NO_ORDER_FOUND_ERROR)

		if order_data.payment_status != "pending":
			return create_data_response(
				data={"message": "payment is already updated"})

		# update payment_status in order table
		order_data.payment_status = pure_json['status']
		db.session.add(order_data)

		if "childTxns" in pure_json:
			for child in pure_json["childTxns"]:
				for field in required_fields_in_child_txn:
					if field not in child:
						ERROR.KEY_MISSING.message = 'key missing in childTxns is %s' % field
						return create_error_response(ERROR.KEY_MISSING)

		payment_objs = save_payment_details(pure_json,
											pure_json['order_id'])

		# update payment and send order to OPS-Panel
		response = None
		"""
		ops_panel_request = PushToOpsPanel(order_id=pure_json['order_id'], payments=payment_objs)
		Logger.info('{%s} updating payment status for order : {%s} '%(g.UUID, pure_json['order_id']))
		ops_panel_request.update_payment(pure_json)

		response_text = ops_panel_request.get_response().text
		Logger.info('{%s} response text for update order {%s}'%(g.UUID, response_text))
		response = json.loads(response_text)
		if str(response['status']).lower() == 'success':
		response_obj = response
		else:
		Logger.error('{%s} Order updation failed for order {%s} '%(g.UUID, pure_json['order_id']), exc_info=True)
		raise Exception(str(response['message']))

		response = response_obj
		"""

		publish_update_payment(pure_json, pure_json['order_id'])


		# create response data here
		db.session.commit()
		Logger.info("[%s] Response for Update Payment Detail API is: [%s]",
					g.UUID, json.dumps(response))
		return create_data_response(data=response)

	except Exception as exception:
		db.session.rollback()
		Logger.error('{%s} Exception occurred ', g.UUID, exc_info=True)
		ERROR.INTERNAL_ERROR.message = exception.message
		return create_error_response(ERROR.INTERNAL_ERROR)


def publish_update_payment(pure_json, order_id):
	message = {}
	message["msg_type"] = "update_payment"
	message['timestamp'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	data = {}
	data["master_order_id"] = order_id
	data["payment_status"] = 0 if pure_json['status'] == "success" else 1
	data["txn_date"] = pure_json.get('txnDate', None)
	data["txn_type"] = 0
	data["pg_txn_Id"] = pure_json.get('pgTxnId', None)
	data["paid_amount"] = pure_json.get('txnAmount', 0.0)
	data["payment_details"] = list()

	if "childTxns" in pure_json:
		for childTxn in pure_json["childTxns"]:
			payment_detail = {}
			payment_detail["mode"] =  PAYMENT_METHOD.get(childTxn.get('paymentMode'))
			payment_detail["gateway"] = childTxn.get('bankGateway', None)
			payment_detail["status"] = 0 if childTxn.get('status')  == "success" else 1
			payment_detail["pg_txn_id"] = childTxn.get('pgTxnId', None)
			payment_detail["amount"] = childTxn.get('txnAmount', 0.0)
			data["payment_details"].append(payment_detail)
	else:
		payment_detail = {}
		payment_detail["mode"] = PAYMENT_METHOD.get(pure_json.get('paymentMode'))
		payment_detail["gateway"] = pure_json.get('bankGateway', None)
		payment_detail["status"] = 0 if pure_json['status'] == "success" else 1
		payment_detail["pg_txn_id"] = pure_json.get('pgTxnId', None)
		payment_detail["amount"] = pure_json.get('txnAmount', 0.0)
		data["payment_details"].append(payment_detail)

	message["data"] = data

	Publisher.publish_message(order_id, json.dumps(message, default=json_serial))
