import json
import logging
import random
import time
from apps.app_v1.api.api_schema_signature import GET_DELIVERY_DETAILS, UPDATE_DELIVERY_SLOT
from apps.app_v1.models import db
from apps.app_v1.models.models import Cart, Address, OrderShipmentDetail, CartItem
from config import APP_NAME
from flask import g, current_app
import requests
from sqlalchemy import func, distinct
from utils.jsonutils.output_formatter import create_data_response, create_error_response
from apps.app_v1.api import ERROR, parse_request_data, NoSuchCartExistException, NoShippingAddressFoundException, \
	NoDeliverySlotException, ShipmentPreviewException
from utils.jsonutils.json_schema_validator import validate

__author__ = 'divyagarg'
Logger = logging.getLogger(APP_NAME)


def create_shipment_id():
	longtime = str(int(time.time()))
	longtime = 'SH' + longtime[7:] + longtime[:3]
	shipment_id = longtime + str(random.randint(1000, 10000))
	return shipment_id


class DeliveryService:
	def __init__(self):

		self.cart = None

	def get_delivery_info(self, body):
		Logger.info("[%s]************************* Get Delivery Slots Start **************************" % g.UUID)
		try:
			request_data = parse_request_data(body)
			validate(request_data, GET_DELIVERY_DETAILS)
			cart = Cart.query.filter_by(geo_id=int(request_data['geo_id']), user_id=request_data['user_id']).first()
			if cart is None:
				raise NoSuchCartExistException(ERROR.NO_SUCH_CART_EXIST)
			else:
				Logger.info("Cart is not none in get delivery info [%s]" % cart.cart_reference_uuid)
				count = db.session.query(func.count(distinct(OrderShipmentDetail.shipment_id))).filter(
					OrderShipmentDetail.cart_id == cart.cart_reference_uuid).group_by(
					OrderShipmentDetail.cart_id).count()
				if count > 0:
					Logger.info("Count is not zero in get delivery info [%s]" % count)
					cart_items_list = CartItem.query.filter_by(cart_id=cart.cart_reference_uuid).all()
					for each_cart_item in cart_items_list:
						each_cart_item.shipment_id = None
						db.session.add(each_cart_item)

					order_shipment_detail_list = OrderShipmentDetail.query.filter_by(
						cart_id=cart.cart_reference_uuid).all()
					for each_shipment in order_shipment_detail_list:
						db.session.delete(each_shipment)

				shipment_preview_response = self.get_shipment_preview(request_data)
				self.parse_response_and_update_db(shipment_preview_response, cart)

			db.session.commit()
			Logger.info("[%s] Response for shipment preview is: [%s]" %(g.UUID, json.dumps(shipment_preview_response)))
			Logger.info("[%s]************************* Get Delivery Slots Stop **************************" % g.UUID)
			return create_data_response(data=shipment_preview_response)
		except NoSuchCartExistException as nsce:
			Logger.error("[%s] No such cart Exist [%s]" % (g.UUID, str(nsce)))
			db.session.rollback()
			return create_error_response(ERROR.NO_SUCH_CART_EXIST)
		except ShipmentPreviewException as spe:
			Logger.error("[%s] hipment preview responded with Error [%s]" % (g.UUID, str(spe)))
			db.session.rollback()
			return create_error_response(ERROR.SHIPMENT_PREVIEW_FAILED)
		except Exception as e:
			Logger.error("[%s] Exception occurred in getting delivery Info [%s]" % (g.UUID, str(e)), exc_info=True)
			db.session.rollback()
			ERROR.INTERNAL_ERROR.message = str(e)
			return create_error_response(ERROR.INTERNAL_ERROR)

	def get_shipment_preview(self, request_data):
		req_data = self.create_shipment_preview_request_data(request_data)
		url = current_app.config['SHIPMENT_PREVIEW_URL']
		Logger.info("request data for shipment preview API is [%s]" % (json.dumps(req_data)))
		response = requests.post(url=url, data=json.dumps(req_data), headers={'Content-type': 'application/json'})
		Logger.info("[%s] Response got from get shipment preview API is [%s]" % (g.UUID, response))
		if response.status_code != 200:
			raise ShipmentPreviewException(ERROR.SHIPMENT_PREVIEW_FAILED)
		json_data = json.loads(response.text)
		Logger.info("[%s] Shipment Preview Response: [%s]" % (
			g.UUID, json_data))
		if not json_data['success']:
			ERROR.INTERNAL_ERROR.message = "Shipment preview API returning failure as response"
			raise Exception(ERROR.INTERNAL_ERROR)
		return json_data['data']

	def parse_response_and_update_db(self, shipment_preview, cart):
		shipment_list = shipment_preview.get('fulfilment_estimates')[0].get('shipments')
		item_dict = {}
		for each_item in self.cart.cartItem:
			item_dict[each_item.cart_item_id] = each_item

		for i in range(shipment_list.__len__()):
			shipment_id = create_shipment_id()

			order_shipment_detail = OrderShipmentDetail()
			order_shipment_detail.cart_id = self.cart.cart_reference_uuid
			order_shipment_detail.shipment_id = shipment_id
			db.session.add(order_shipment_detail)
			shipment_list[i]["shipment_id"] = shipment_id

		for i in range(shipment_list.__len__()):
			shipment_items_list = shipment_list[i].get('shipment_items')
			shipment_id = shipment_list[i].get('shipment_id')
			for each_item in shipment_items_list:
				custom_field = each_item.get('custom')
				if custom_field is not None and json.loads(custom_field).get('freebie') is True:
					for freebee_item in json.loads(cart.selected_freebee_items):
						if freebee_item['id'] == each_item.get('subscription_id'):
							freebee_item["shipment_id"] = shipment_id
						db.session.add(cart)
				else:
					item = item_dict[each_item.get('subscription_id')]
					item.shipment_id = shipment_id
					db.session().add(item)



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
		if shipping_address.pincode is not None:
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
		i = i+1
		if cart.selected_freebee_items is not None:
			selected_freebies = json.loads(cart.selected_freebee_items)
			for j in range(selected_freebies.__len__()):
				order_item = {}
				order_item["order_item_id"] = str(i + j)
				order_item["subscription_id"] = selected_freebies[j].get('id')
				order_item["quantity"] = 1
				isfreebie = { "freebie": True}
				order_item["custom"] = json.dumps(isfreebie)
				order_item["freebie"] = True
				order_items.append(order_item)

		order_data = {}
		order_data["order_items"] = order_items
		request_data = {}
		request_data["fulfilment_request_object"] = fulfilment_request_object
		request_data["order_data"] = order_data
		Logger.info("[%s] Request data for shipment preview is [%s]" % (g.UUID, json.dumps(request_data)))
		return request_data

	def update_slot(self, body):
		try:
			Logger.info("[%s]************************* Update Delivery Slots Start **************************" % g.UUID)
			Logger.info("[%s] Update Slot API request body [%s]" % (g.UUID, body))
			request_data = parse_request_data(body)
			validate(request_data, UPDATE_DELIVERY_SLOT)
			self.update_delivery_slot(request_data)
			db.session.commit()
			Logger.info("[%s]************************* Update Delivery Slots Start **************************" % g.UUID)
			return create_data_response(data="success")
		except Exception as e:
			Logger.error("[%s] Exception occurred in getting delivery Info [%s]" % (g.UUID, str(e)), exc_info=True)
			db.session.rollback()
			ERROR.INTERNAL_ERROR.message = str(e)
			return create_error_response(ERROR.INTERNAL_ERROR)

	def update_delivery_slot(self, request_data):
		delivery_slots_list = request_data.get('delivery_slots')
		for each_slot in delivery_slots_list:
			shipment_id = each_slot.get('shipment_id')
			timerange = {}
			timerange["start_datetime"] = each_slot.get('start_datetime')
			timerange["end_datetime"] = each_slot.get('end_datetime')
			Logger.info("[%s] Shipment Id [%s], timerange = [%s]" % (g.UUID, shipment_id, timerange))
			order_shipment = OrderShipmentDetail.query.filter_by(shipment_id=shipment_id).first()
			if order_shipment is None:
				raise NoDeliverySlotException(ERROR.NO_DELIVERY_SLOT_ERROR)
			order_shipment.delivery_slot = json.dumps(timerange)
			db.session.add(order_shipment)
