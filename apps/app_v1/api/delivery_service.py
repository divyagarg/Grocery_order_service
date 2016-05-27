import json
import logging
import time
from apps.app_v1.api.api_schema_signature import GET_DELIVERY_DETAILS
from apps.app_v1.models import db
from apps.app_v1.models.models import Cart, Address, OrderShipmentDetail
from config import APP_NAME
from flask import g, current_app
import requests
from utils.jsonutils.output_formatter import create_data_response, create_error_response
from apps.app_v1.api import ERROR, parse_request_data, NoSuchCartExistException, NoShippingAddressFoundException
from utils.jsonutils.json_schema_validator import validate

__author__ = 'divyagarg'
Logger = logging.getLogger(APP_NAME)


def create_shipment_id():
	return str(int(time.time()))


class DeliveryService:
	def __init__(self):
		self.shipment_preview = None
		self.cart = None
		self.order_shipment_detail_list = None

	def get_delivery_info(self, body):
		try:
			request_data = parse_request_data(body)
			validate(request_data, GET_DELIVERY_DETAILS)
			self.get_shipment_preview(request_data)
			self.parse_response()
			for each_shipment in self.order_shipment_detail_list:
				db.session.add(each_shipment)
				db.session.commit()
			for each_item in self.cart.cartItem:
				db.session.add(each_item)
			db.session.commit()
			return create_data_response(data=self.shipment_preview)
		except Exception as e:
			Logger.error("[%s] Exception occurred in getting delivery Info [%s]" % (g.UUID, str(e)), exc_info=True)
			db.session.rollback()
			for each_shipment in self.order_shipment_detail_list:
				db.session.delete(each_shipment)
				db.session.commit()
			ERROR.INTERNAL_ERROR.message = str(e)
			return create_error_response(ERROR.INTERNAL_ERROR)

	def get_shipment_preview(self, request_data):
		req_data = self.create_shipment_preview_request_data(request_data)
		url = current_app.config['SHIPMENT_PREVIEW_URL']
		Logger.info("request data for shipment preview API is [%s]" %(json.dumps(req_data)))
		response = requests.post(url=url, data=json.dumps(req_data), headers={'Content-type': 'application/json'})
		json_data = json.loads(response.text)
		Logger.info("[%s] Shipment Preview Request: [%s] and Response: [%s]" % (
			g.UUID, json.dumps(req_data), json_data))
		if not json_data['success']:
			ERROR.INTERNAL_ERROR.message = "Shipment preview API returning failure as response"
			raise Exception(ERROR.INTERNAL_ERROR)
		self.shipment_preview = json_data['data']

	def parse_response(self):
		response_json = self.shipment_preview
		shipment_list = response_json.get('fulfilment_estimates')[0].get('shipments')
		item_dict = {}
		for each_item in self.cart.cartItem:
			item_dict[each_item.cart_item_id] = each_item
		self.order_shipment_detail_list = list()
		for i in range(shipment_list.__len__()):
			order_shipment_detail = OrderShipmentDetail()
			order_shipment_detail.shipment_id = create_shipment_id()
			self.order_shipment_detail_list.append(order_shipment_detail)


			shipment_items_list = shipment_list[i].get('shipment_items')
			shipment_list[i]["shipment_id"] = order_shipment_detail.shipment_id
			for each_item in shipment_items_list:
				item = item_dict[each_item.get('subscription_id')]
				item.shipment_id = order_shipment_detail.shipment_id


	def create_shipment_preview_request_data(self, data):
		cart = Cart.query.filter_by(geo_id=int(data['geo_id']), user_id=data['user_id']).first()
		if cart is None:
			raise NoSuchCartExistException(ERROR.NO_SUCH_CART_EXIST)
		if cart.shipping_address_ref is None:
			raise NoShippingAddressFoundException(ERROR.NO_SHIPPING_ADDRESS_FOUND)
		self.cart = cart
		shipping_address = Address.query.filter_by(address_hash=cart.shipping_address_ref).first()
		address = {}
		address["address_line_1"] = shipping_address.address
		address["city"] = shipping_address.city
		address["state"] = shipping_address.state
		address["pincode"] = shipping_address.pincode
		address_detail = {}
		address_detail["address"] = address
		deliver_to = {}
		deliver_to["address_detail"] = address_detail

		fulfilment_request_object = {}
		fulfilment_request_object["direction"] = 0
		fulfilment_request_object["deliver_to"] = deliver_to

		order_items = list()
		for i in range(cart.cartItem.__len__()):
			order_item = {}
			order_item["order_item_id"] = str(i)
			order_item["subscription_id"] = cart.cartItem[i].cart_item_id
			order_item["quantity"] = cart.cartItem[i].quantity
			order_items.append(order_item)

		order_data = {}
		order_data["order_items"] = order_items
		request_data = {}
		request_data["fulfilment_request_object"] = fulfilment_request_object
		request_data["order_data"] = order_data
		Logger.info("[%s] Request data for shipment preview is [%s]" % (g.UUID, json.dumps(request_data)))
		return request_data
