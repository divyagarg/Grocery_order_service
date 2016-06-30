import uuid
import json
import logging
import datetime

from requests.exceptions import ConnectTimeout
from flask import g, current_app
import requests
from apps.app_v1.api.coupon_service import CouponService
import config
from apps.app_v1.api import parse_request_data, RequiredFieldMissing,\
	EmptyCartException, IncorrectDataException,	CouponInvalidException,\
	SubscriptionNotFoundException, QuantityNotAvailableException,\
	 get_shipping_charges, ServiceUnAvailableException, \
	FreebieNotApplicableException, RemoveCouponBeforeDeletingLastItem
from apps.app_v1.api.api_schema_signature import CREATE_CART_SCHEMA
from apps.app_v1.models import order_types, payment_modes_dict
from apps.app_v1.models.models import Cart, CartItem, Address, OrderShipmentDetail
from utils.jsonutils.output_formatter import create_error_response, create_data_response
from utils.jsonutils.json_schema_validator import validate
from config import APP_NAME
from apps.app_v1.models.models import db
from apps.app_v1.api import ERROR

__author__ = 'divyagarg'

Logger = logging.getLogger(APP_NAME)


def get_cart_for_geo_user_id(geo_id, user_id):
	return Cart.query.filter_by(geo_id=int(geo_id), user_id=user_id).first()


def check_if_calculate_price_api_response_is_correct_or_quantity_is_available\
				(item, json_order_item):
	if json_order_item is None:
		Logger.error("[%s] No item is found in calculate price API response \
		for the item [%s]", g.UUID, item['item_uuid'], exc_info=True)
		raise SubscriptionNotFoundException(ERROR.SUBSCRIPTION_NOT_FOUND)
	if json_order_item['maxQuantity'] is not None and json_order_item[
		  'maxQuantity'] < item['quantity']:
		Logger.error("[%s] Quantity requested can not be fulfilled\
		  for the item [%s]", g.UUID, item['item_uuid'], exc_info=True)
		raise QuantityNotAvailableException(ERROR.PRODUCT_AVAILABILITY_CHANGED)


def convert_list_type_from_int_to_str(freebies_id_list):
	str_list = list()
	for item in freebies_id_list:
		str_list.append(str(item))
	return str_list


def calculate_price_api(req_data):
	request_data = json.dumps(req_data)
	Logger.info("[%s] Request data for calculate price API is [%s]",
				         g.UUID, request_data)
	response = requests.post(url=current_app.config['PRODUCT_CATALOGUE_URL'],
							                   data=request_data,
							 				   headers={'Content-type': 'application/json'},
							 				   timeout=current_app.config['API_TIMEOUT'])
	if response.status_code != 200:
		if response.status_code == 404:
			Logger.error("[%s] Catalog search API is down", g.UUID)
			raise ServiceUnAvailableException(
										ERROR.PRODUCT_CATALOG_SERVICE_DOWN)
		else:
			Logger.error("[%s] Error from product catalog service", g.UUID)
			ERROR.INTERNAL_ERROR.message = response.reason
			raise Exception(ERROR.INTERNAL_ERROR)
	json_data = json.loads(response.text)
	Logger.info("[%s] Response got from calculate Price API is [%s]",
						 g.UUID, json.dumps(json_data))

	return json_data['results']


def get_freebie_details(freebies_id_list, order_type):
	req_data = {
		"query": {
			"type": [order_type],
			"filters": {
				"id": freebies_id_list
			},
			"select": config.SEARCH_API_SELECT_CLAUSE
		},
		"count": freebies_id_list.__len__(),
		"offset": 0
	}
	response = calculate_price_api(req_data)
	if len(response) == 0:
		return None

	order_item_price_dict = {}
	for response in response[0].get('items')[0].get('items'):
		order_item_price_dict[response.get('id')] = response

	freebie_detail_list = list()
	for each_freebie_id in freebies_id_list:
		freebie_json = {'id': str(each_freebie_id),
						'title': order_item_price_dict.get(
							each_freebie_id).get('title'),
						'image_url': order_item_price_dict.get(
							each_freebie_id).get('imageURL')}
		freebie_detail_list.append(freebie_json)

	return freebie_detail_list


def create_address_json(shipping_address):
	shipping_add = {"name": shipping_address.name,
					"mobile": shipping_address.mobile,
					"address": shipping_address.address,
					"city": shipping_address.city,
					"pincode": shipping_address.pincode,
					"state": shipping_address.state,
					"email": shipping_address.email,
					"landmark": shipping_address.landmark}
	return shipping_add


def get_response_from_check_coupons_api(cart_items, data, cart):
	url = current_app.config['COUPON_CHECK_URL']
	req_data = {
		"area_id": str(data['geo_id']),
		"customer_id": data['user_id'],
		'channel': data['order_source_reference'],
		"products": [
			{"item_id": str(each_cart_item.cart_item_id),
			 "subscription_id": str(each_cart_item.cart_item_id),
			 "quantity": each_cart_item.quantity,
			 "coupon_code": each_cart_item.promo_codes}
			for each_cart_item in cart_items]
	}
	if 'payment_mode' in data:
		req_data['payment_mode'] = payment_modes_dict[
			data.get('payment_mode')]
		url = url + config.COUPON_QUERY_PARAM
	if 'promo_codes' in data:
		if data.get('promo_codes') == []:
			cart.promo_codes = None
		elif hasattr(data.get('promo_codes'), '__iter__') and data.get(
				'promo_codes') != []:
			req_data["coupon_codes"] = map(str, data.get('promo_codes'))
	elif cart is not None and cart.promo_codes is not None:
		req_data["coupon_codes"] = json.loads(cart.promo_codes)
	response = CouponService.call_check_coupon_api(req_data)
	if response.status_code != 200:
		if response.status_code == 404:
			Logger.error("[%s] Coupon service is temporarily unavailable",
						 g.UUID)
			raise ServiceUnAvailableException(ERROR.COUPON_SERVICE_DOWN)
		elif response.status_code == 400:
			Logger.error("[%s] Coupon service is returning error [%s]", g.UUID, json.loads(response.text)['errors'][0])
			ERROR.INTERNAL_ERROR.message = json.loads(response.text)['errors'][0]
			raise CouponInvalidException(ERROR.INTERNAL_ERROR)
	if "coupon_codes" in req_data and cart is not None:
		cart.promo_codes = json.dumps(req_data["coupon_codes"])
	json_data = json.loads(response.text)
	Logger.info(
		"[%s] Request to check Coupon data passed is: [%s] and response is: [%s]",
			g.UUID, json.dumps(req_data), json_data)
	return json_data


def remove_discounts(cart_items, cart):
	for each_cart_item in cart_items:
		each_cart_item.item_discount = 0.0
	cart.total_discount = 0.0
	cart.promo_codes = None


def fetch_product_price(items, data):
	request_items_ids = list()
	for item in items:
		request_items_ids.append(int(item["item_uuid"]))

	order_type = order_types[0]
	if data.get('order_type') is not None:
		order_type = order_types[data.get('order_type')]

	req_data = {
		"query": {
			"type": [order_type],
			"filters": {
				"id": request_items_ids
			},
			"select": config.SEARCH_API_SELECT_CLAUSE
		},
		"count": request_items_ids.__len__(),
		"offset": 0
	}

	return calculate_price_api(req_data)


def fetch_items_price_return_dict(data):
	response_product_fetch_data = fetch_product_price(
		data['orderitems'], data)

	if response_product_fetch_data is None or response_product_fetch_data.__len__() == 0:
		raise SubscriptionNotFoundException(ERROR.SUBSCRIPTION_NOT_FOUND)

	order_item_dict = {}
	for response in response_product_fetch_data[0].get('items')[0].get(
			'items'):
		order_item_dict[response.get('id')] = response
	return order_item_dict


def validate_create_new_cart(data):
	if 'orderitems' not in data or (
			'orderitems' in data and data['orderitems'].__len__() == 0):
		raise EmptyCartException(ERROR.CART_EMPTY)
	else:
		for each_cart_item in data['orderitems']:
			if each_cart_item['quantity'] == 0:
				raise IncorrectDataException(
					ERROR.CART_ZERO_QUANTITY_CAN_NOT_BE_ADDED)


def change_quantity_of_cart_item(cart_item_db, check_price_json,
								 item):
	cart_item_db.quantity = item['quantity']
	cart_item_db.display_price = check_price_json['display_price']
	cart_item_db.offer_price = check_price_json['offer_price']


def remove_cart(cart_reference_id):
	if cart_reference_id is None:
		ERROR.INTERNAL_ERROR.message = "Cart reference id can not be Null"
		raise Exception(ERROR.INTERNAL_ERROR)
	cart = Cart.query.filter_by(
		cart_reference_uuid=cart_reference_id).first()
	db.session.delete(cart)


def check_prices_of_item(request_items, data):

	response_data = fetch_product_price(request_items, data)
	if response_data is None or response_data.__len__() == 0:
		raise SubscriptionNotFoundException(ERROR.SUBSCRIPTION_NOT_FOUND)
	order_item_price_dict = {}

	for response in response_data[0].get('items')[0].get('items'):
		order_item_price_dict[response.get('id')] = response
	for each_item in request_items:
		if int(each_item['item_uuid']) not in order_item_price_dict:
			raise SubscriptionNotFoundException(ERROR.SUBSCRIPTION_NOT_FOUND)
		check_if_calculate_price_api_response_is_correct_or_quantity_is_available(each_item, order_item_price_dict[int(each_item['item_uuid'])])

	return order_item_price_dict


def check_freebie_is_applicable(benefits, cart):
	if (benefits is None or benefits == []) and cart is not None and cart.selected_freebee_items is not None:
		raise FreebieNotApplicableException(ERROR.FREEBIE_NOT_APPLICABLE)
	for each_benefit in benefits:
			if each_benefit.get('type') == 0 or each_benefit.get('type') == 1:
				freebies_id_list = each_benefit['freebies'][0]
				if freebies_id_list is not None and freebies_id_list.__len__() > 0:
					if cart is not None and cart.selected_freebee_items is not None:
						selected_freebies = json.loads(cart.selected_freebee_items)
						selected_freebie_item_id = selected_freebies[0].get('id')
						# Typecasting selected freebie item id t int as coupon service returns freebie items ids as int
						if int(selected_freebie_item_id) not in freebies_id_list:
							raise FreebieNotApplicableException(ERROR.FREEBIE_NOT_APPLICABLE)
				else:
					raise FreebieNotApplicableException(ERROR.FREEBIE_NOT_APPLICABLE)
			elif cart is not None and cart.selected_freebee_items is not None:
					raise FreebieNotApplicableException(ERROR.FREEBIE_NOT_APPLICABLE)

class CartService(object):
	def __init__(self):
		"""

		:type self: object
		"""
		self.cart_reference_uuid = None
		self.total_price = 0.0
		self.total_discount = 0.0
		self.total_display_price = 0.0
		self.now = datetime.datetime.utcnow()

		self.total_shipping_charges = 0.0
		self.benefits = None
		self.cart_items = None
		self.is_cart_empty = False
		self.item_id_to_existing_item_dict = None
		self.deleted_cart_items = None
		self.shipping_address = None
		self.total_cashback = 0.0
		self.payment_mode_allowed = None

	def create_or_update_cart(self, body):
		try:
			Logger.info("[%s] Create/update cart request body [%s]",\
									 g.UUID, body)
			request_data = parse_request_data(body)
			validate(request_data, CREATE_CART_SCHEMA)
			cart = get_cart_for_geo_user_id(request_data['geo_id'], \
											request_data['user_id'])
			if cart is not None:
				return self.update_cart(cart, request_data, 0)
			else:
				return self.create_cart(request_data)

		except IncorrectDataException as ide:
			Logger.error("[%s] Validation Error [%s]",
						 g.UUID, str(ide.message))
			return create_error_response(ide)
		except Exception as exception:
			Logger.error('[%s] Exception occured while creating/updating\
						cart [%s]',g.UUID, str(exception), exc_info=True)
			ERROR.INTERNAL_ERROR.message = str(exception)
			return create_error_response(ERROR.INTERNAL_ERROR)

	def update_cart(self, cart, data, operation):
		Logger.info(
			"[%s]***********************Update Cart Started********************",
			g.UUID)
		error = True
		err = None
		while True:
			# 1 Item update(Added, removed, update)
			try:
				self.update_cart_items(data, cart, operation)

			except RemoveCouponBeforeDeletingLastItem as rc:
				Logger.error("[%s] Remove coupon before deleting last item from the cart [%s]", g.UUID, str(rc.message))
				err = ERROR.REMOVE_COUPON_BEFORE_DELETING_LAST_ITEM
				break
			except IncorrectDataException:
				Logger.error("[%s] Non existing item can not be deleted",\
							 g.UUID)
				err = ERROR.NOT_EXISTING_ITEM_CAN_NOT_BE_DELETED
				break
			except SubscriptionNotFoundException:
				Logger.error("[%s] Subscription is not valid", g.UUID)
				err = ERROR.SUBSCRIPTION_NOT_FOUND
				break
			except QuantityNotAvailableException as qnae:
				Logger.error("[%s] Quantity is not available [%s]",
							 g.UUID, str(qnae))
				err = ERROR.PRODUCT_AVAILABILITY_CHANGED
				break
			except EmptyCartException:
				Logger.error("[%s] Cart has become empty", g.UUID)
				cart.total_discount = 0.0
				cart.total_offer_price = 0.0
				cart.total_display_price = 0.0
				cart.total_shipping_charges = 0.0
				cart.promo_codes = None
				self.is_cart_empty = True
				err = ERROR.CART_EMPTY
				break
			except ConnectTimeout:
				Logger.error("[%s] Timeout exception for product catalog api",
							 g.UUID)
				err = ERROR.PRODUCT_API_TIMEOUT
				break
			except Exception as exception:
				Logger.error(
					"[%s] Exception occurred in updating cart items [%s]",
					g.UUID, str(exception), exc_info=True)
				ERROR.INTERNAL_ERROR.message = str(exception)
				err = ERROR.INTERNAL_ERROR
				break


			# 2 Payment Mode
			if data.get('payment_mode') is not None:
				cart.payment_mode = payment_modes_dict[
					data.get('payment_mode')]

			# Selected Freebie
			try:
				if data.get('selected_freebee_code') is not None and data.get(
						'selected_freebee_code') != []:
					cart.selected_freebee_items = json.dumps(
						data.get('selected_freebee_code'))
				elif data.get(
						'selected_freebee_code') is not None and data.get(
						'selected_freebee_code') == []:
					cart.selected_freebee_items = None
			except Exception as exception:
				Logger.error(
					'[%s] Selected Freebee code could not be set in cart [%s]',
					g.UUID, str(exception),
					exc_info=True)
				ERROR.INTERNAL_ERROR.message = str(exception)
				err = ERROR.INTERNAL_ERROR
				break

			# 3 Check coupons (Cart Level or Item level)
			if not self.is_cart_empty:
				try:
					self.check_for_coupons_applicable(data, cart)

				except ServiceUnAvailableException as se:
					Logger.error("[%s] Coupon service is unavailable", g.UUID)
					err = ERROR.COUPON_SERVICE_DOWN
					break
				except ConnectTimeout:
					Logger.error("[%s] Timeout exception for coupon api",
								 g.UUID)
					err = ERROR.COUPON_API_TIMEOUT
					break

				except CouponInvalidException as cie:
					Logger.error('[%s] Coupon can not be applied [%s]',
								 g.UUID, str(cie), exc_info=True)
					ERROR.COUPON_SERVICE_RETURNING_FAILURE_STATUS.message = cie.message
					err = ERROR.COUPON_SERVICE_RETURNING_FAILURE_STATUS
					break
				except Exception as exception:
					Logger.error("[%s] Exception occurred in coupin service [%s]" % (g.UUID, str(exception)), exc_info=True)
					ERROR.INTERNAL_ERROR.message = str(exception)
					err = ERROR.INTERNAL_ERROR
					break

			# 4 Shipping address
			try:
				self.update_address(data, cart)
			except Exception as exception:
				Logger.error('[%s] Shipping address could not be updated [%s]',
							 g.UUID, str(exception), exc_info=True)
				ERROR.INTERNAL_ERROR.message = str(exception)
				err = ERROR.INTERNAL_ERROR
				break

			# 5 update cart price
			try:
				self.update_cart_total_amounts(cart)
			except Exception as exception:
				Logger.error('[%s] Shipping address could not be updated [%s]',
							 g.UUID, str(exception), exc_info=True)
				ERROR.INTERNAL_ERROR.message = str(exception)
				err = ERROR.INTERNAL_ERROR
				break


			# 6 Save cart
			try:
				db.session.add(cart)
				for each_cart_item in self.item_id_to_existing_item_dict.values():
					db.session.add(each_cart_item)
				if self.deleted_cart_items.values().__len__() > 0:
					for each_deleted_item in self.deleted_cart_items.values():
						db.session.delete(each_deleted_item)

			except Exception as exception:
				Logger.error('[%s] Shipping address could not be updated [%s]',
							 g.UUID, str(exception), exc_info=True)
				err = ERROR.DATABASE_ERROR
				break

			# 7 Create Response
			try:
				response_data = self.generate_response(None, cart, data)
			except Exception as exception:
				Logger.error(
					'[%s] Exception occurred in creating response while updating the cart [%s]',
					g.UUID, str(exception),
					exc_info=True)
				ERROR.INTERNAL_ERROR.message = str(exception)
				err = ERROR.INTERNAL_ERROR
				break

			error = False
			break;
		if error:
			db.session.rollback()
			return create_error_response(err)
		else:
			db.session.commit()
			return create_data_response(data=response_data)

	def create_cart(self, data):
		error = True
		err = None
		while True:

			# 0. Validation
			try:
				validate_create_new_cart(data)
			except EmptyCartException as ece:
				Logger.error(
					'[%s] Cart can not be created without an item [%s]',
					g.UUID, str(ece),
					exc_info=True)
				err = ERROR.CART_EMPTY
				break
			except RequiredFieldMissing as rfm:
				Logger.error(
					'[%s] Required field is missing in creating cart API call[%s]',
					g.UUID, str(rfm),
					exc_info=True)
				err = ERROR.CART_ITEM_MISSING
				break
			except IncorrectDataException as ide:
				Logger.error('[%s] Zero quantity can not be added[%s]',
							 g.UUID, str(ide),
							 exc_info=True)
				err = ERROR.INCORRECT_DATA
				break

			# 1. Initialize cart object
			try:
				self.cart_reference_uuid = uuid.uuid1().hex
				cart = Cart()
				self.populate_cart_object(data, cart)
			except Exception as exception:
				Logger.error("[%s] Exception occurred in populating cart\
							 object [%s]", g.UUID, str(exception), exc_info=True)
				ERROR.INTERNAL_ERROR.message = str(exception)
				err = ERROR.INTERNAL_ERROR
				break

			# 2. Calculate item prices and cart total
			try:
				self.get_price_and_update_in_cart_item(data)

			except ServiceUnAvailableException:
				Logger.error("[%s] Product catalog service is unavailable",
							 g.UUID)
				err = ERROR.PRODUCT_CATALOG_SERVICE_DOWN
				break
			except SubscriptionNotFoundException as snfe:
				Logger.error("[%s] Subscript not found for data [%s]",
							 g.UUID, str(snfe))
				err = ERROR.SUBSCRIPTION_NOT_FOUND
				break
			except QuantityNotAvailableException as qnae:
				Logger.error("[%s] Quantity is not available [%s]",
							 g.UUID, str(qnae))
				err = ERROR.PRODUCT_AVAILABILITY_CHANGED
				break
			except ConnectTimeout:
				Logger.error("[%s] Timeout exception for product price api",
							 g.UUID)
				err = ERROR.PRODUCT_API_TIMEOUT
				break
			except Exception as exception:
				Logger.error(
					"[%s] Exception occurred in getting price and update in cart item [%s]",
					g.UUID, str(exception.message),
					exc_info=True)
				ERROR.INTERNAL_ERROR.message = str(exception.message)
				err = ERROR.INTERNAL_ERROR
				break

			# 3. check coupons
			try:
				if self.cart_items is not None and self.cart_items.__len__()>0:
					response_data = get_response_from_check_coupons_api(
						self.cart_items, data, cart)
					self.update_discounts_item_level(response_data,
													 self.cart_items)
					self.fetch_freebie_details_and_update(
						response_data.get('benefits', []),
						order_types.get(data['order_type']), cart)
			except ServiceUnAvailableException as se:
				Logger.error("[%s] Coupon service is unavailable", g.UUID)
				err = ERROR.COUPON_SERVICE_DOWN
				break
			except SubscriptionNotFoundException as snfe:
				Logger.error(
					"[%s] Exception occured in fetching catalog info [%s]",
					g.UUID, str(snfe))
				err = ERROR.SUBSCRIPTION_NOT_FOUND
				break
			except CouponInvalidException as cie:
				Logger.error(
					"[%s] Exception occurred in checking coupons for cart item [%s]",
					g.UUID, str(cie))
				ERROR.COUPON_SERVICE_RETURNING_FAILURE_STATUS.message = cie.message
				err = ERROR.COUPON_SERVICE_RETURNING_FAILURE_STATUS
				break
			except ConnectTimeout:
				Logger.error("[%s] Timeout exception for coupon api", g.UUID)
				err = ERROR.COUPON_API_TIMEOUT
				break
			except FreebieNotApplicableException as fna:
				Logger.error("[%s] Exception occured Freebie became unapplicable [%s]", g.UUID, str(fna))
				err = ERROR.FREEBIE_NOT_APPLICABLE
				break
			except Exception as exception:
				Logger.error(
					"[%s] Exception occurred in checking coupons for cart item [%s]",
					g.UUID, str(exception.message))
				ERROR.INTERNAL_ERROR.message = str(exception.message)
				err = ERROR.INTERNAL_ERROR
				break

			# 4. apply shipping charges
			try:
				self.total_shipping_charges = get_shipping_charges(
					self.total_price, self.total_discount)
			except Exception as exception:
				Logger.error(
					"[%s] Exception occurred in getting shipping charges for cart item [%s]",
					g.UUID, str(exception),
					exc_info=True)
				ERROR.INTERNAL_ERROR.message = str(exception)
				err = ERROR.INTERNAL_ERROR
				break

			# 5. save in DB
			try:
				self.save_cart(data, cart)
			except Exception as exception:
				Logger.error(
					"[%s] Exception occurred in saving cart item in DB [%s]",
					g.UUID, str(exception), exc_info=True)
				ERROR.DATABASE_ERROR.message = str(exception)
				err = ERROR.DATABASE_ERROR
				break

			# 6. create response
			try:
				response_data = self.generate_response(self.cart_items, cart,
													   data)
			except Exception as exception:
				Logger.error(
					"[%s] Exception occurred in generating response for cart [%s]",
					g.UUID, str(exception),
					exc_info=True)
				ERROR.INTERNAL_ERROR.message = str(exception)
				err = ERROR.INTERNAL_ERROR
				break

			error = False
			break

		if error:
			db.session.rollback()
			return create_error_response(err)
		else:
			db.session.commit()
			return create_data_response(data=response_data)

	def save_cart(self, data, cart):
		cart.total_offer_price = self.total_price
		cart.total_display_price = self.total_display_price
		cart.total_discount = self.total_discount
		cart.total_cashback = self.total_cashback
		cart.total_shipping_charges = self.total_shipping_charges

		self.shipping_address = data.get('shipping_address')
		if self.shipping_address is not None:
			address = Address.get_address(self.shipping_address['name'],
										  self.shipping_address['mobile'],
										  self.shipping_address['address'],
										  self.shipping_address.get('city'),
										  self.shipping_address.get('pincode'),
										  self.shipping_address.get('state'),
										  self.shipping_address.get('email'),
										  self.shipping_address.get(
											  'landmark'))
			cart.shipping_address_ref = address.address_hash

		db.session.add(cart)

		for cart_item in self.cart_items:
			db.session.add(cart_item)

	def add_new_item_to_cart(self, cart_item_db, json_order_item, item):
		cart_item_db.cart_item_id = item['item_uuid']
		cart_item_db.cart_id = self.cart_reference_uuid
		cart_item_db.quantity = item['quantity']
		cart_item_db.cart_id = self.cart_reference_uuid
		cart_item_db.display_price = float(json_order_item['display_price'])
		cart_item_db.offer_price = float(json_order_item['offer_price'])

	def populate_cart_object(self, data, cart):

		cart.geo_id = int(data['geo_id'])
		cart.user_id = data['user_id']
		cart.cart_reference_uuid = self.cart_reference_uuid
		cart.order_type = order_types[0]
		if data.get('order_type') is not None:
			cart.order_type = order_types[data.get('order_type')]
		cart.order_source_reference = data['order_source_reference']
		if data.get('payment_mode') is not None:
			cart.payment_mode = payment_modes_dict[data.get('payment_mode')]
		if data.get('selected_freebee_code') is not None and data.get(
				'selected_freebee_code') != []:
			cart.selected_freebee_items = json.dumps(
				data.get('selected_freebee_code'))
		elif data.get('selected_freebee_code') is not None and data.get(
				'selected_freebee_code') == []:
			cart.selected_freebee_items = None

	def generate_response(self, new_items, cart, data):
		response_json = {
			"orderitems": [],
			"total_offer_price": self.total_price,
			"total_display_price": self.total_display_price,
			"total_payable_price": self.get_total_payble_price(),
			"total_payable_price_without_shipping": self.total_price- self.total_discount,
			"total_saved_amount": (self.total_display_price - self.total_price) + self.total_discount,
			"total_discount": self.total_discount,
			"total_cashback": self.total_cashback,
			"total_shipping_charges": self.total_shipping_charges,
			"cart_reference_uuid": cart.cart_reference_uuid,
			"benefits": self.benefits,
			"cart_items_count": self.get_count_of_items(new_items)
		}
		if cart.promo_codes is not None:
			response_json["promo_codes"] = json.loads(cart.promo_codes)
			response_json["allowed_payment_modes"] = self.payment_mode_allowed
		if cart.selected_freebee_items is not None:
			response_json["selected_freebee_code"] = json.loads(
				cart.selected_freebee_items)

		if self.shipping_address is not None:
			response_json['shipping_address'] = self.shipping_address

		if self.total_cashback > 0:
			if data.get('login_status', 0) == 1:
				response_json[
					'display_message'] = "Coupon applied successfully. Cashback will be credited to your AskmePay Wallet within 24 hours of delivery"
			else:
				response_json['display_message'] = \
					"Coupon applied successfully. Cashback will be credited to your AskmePay Wallet within 24 hours of delivery." \
					" Please verify your number on success / payment page to avail cashback."

		selected_slots = list()
		order_shipment_details = OrderShipmentDetail.query.filter_by(
			cart_id=cart.cart_reference_uuid).all()
		if order_shipment_details is not None:
			for each_shipment_detail in order_shipment_details:
				if each_shipment_detail.delivery_slot is not None:
					selected_slots.append(
						json.loads(each_shipment_detail.delivery_slot))
			if selected_slots.__len__() > 0:
				response_json["selected_delivery_slot"] = selected_slots

		if new_items is not None:
			items = list()
			for item in new_items:
				order_item_dict = {}
				order_item_dict["item_uuid"] = item.cart_item_id
				order_item_dict["display_price"] = item.display_price
				order_item_dict["offer_price"] = item.offer_price
				order_item_dict["quantity"] = item.quantity
				order_item_dict["item_discount"] = item.item_discount
				order_item_dict["title"] = item.title
				order_item_dict["image_url"] = item.image_url
				items.append(order_item_dict)
			response_json["orderitems"] = items

		elif self.item_id_to_existing_item_dict.values().__len__() != 0:
			items = list()
			for item in self.item_id_to_existing_item_dict.values():
				order_item_dict = {}
				order_item_dict["item_uuid"] = item.cart_item_id
				order_item_dict["display_price"] = str(item.display_price)
				order_item_dict["offer_price"] = str(item.offer_price)
				order_item_dict["quantity"] = item.quantity
				order_item_dict["item_discount"] = str(item.item_discount)
				order_item_dict["title"] = item.title
				order_item_dict["image_url"] = item.image_url
				items.append(order_item_dict)
			response_json["orderitems"] = items
		Logger.info("[%s] Response for create/update cart is: [%s]",
					g.UUID, json.dumps(response_json))
		return response_json

	def update_discounts_item_level(self, response_data, cart_items):
		item_discount_dict = {}
		if response_data['success']:
			self.total_discount = float(response_data['totalDiscount'])
			self.total_cashback = float(response_data['totalCashback'])
			if response_data['paymentMode'] is not None:
				self.payment_mode_allowed = response_data['paymentMode']
			# TODO : optimize two loops to one.
			for item in response_data['products']:
				item_discount_dict[item['itemid']] = item

			for each_cart_item in cart_items:
				each_cart_item.item_discount = float(
					item_discount_dict[str(each_cart_item.cart_item_id)][
						'discount'])
				each_cart_item.item_cashback = float(
					item_discount_dict[str(each_cart_item.cart_item_id)][
						'cashback'])

	def update_cart_total_amounts(self, cart):
		cart.total_display_price = 0.0
		cart.total_offer_price = 0.0
		cart.total_discount = self.total_discount
		cart.total_cashback = self.total_cashback
		for each_cart_item in self.item_id_to_existing_item_dict.values():
			unit_offer_price = each_cart_item.offer_price
			unit_display_price = each_cart_item.display_price
			quantity = each_cart_item.quantity
			item_level_discount = each_cart_item.item_discount
			cart.total_display_price += (float(unit_display_price) * quantity)
			cart.total_offer_price += (float(unit_offer_price) * quantity)
			if item_level_discount is None:
				item_level_discount = 0.0
			# cart.total_discount = float(cart.total_discount) + float(item_level_discount)

		self.total_display_price = cart.total_display_price
		self.total_price = cart.total_offer_price
		# self.total_discount = cart.total_discount

		self.total_shipping_charges = get_shipping_charges(self.total_price,
														   self.total_discount)
		cart.total_shipping_charges = self.total_shipping_charges

	def get_price_and_update_in_cart_item(self, data):
		order_item_dict = fetch_items_price_return_dict(data)
		cart_item_list = list()
		for item in data['orderitems']:
			item_id = int(item['item_uuid'])
			json_order_item = order_item_dict.get(item_id)
			check_if_calculate_price_api_response_is_correct_or_quantity_is_available(
				item, json_order_item)
			cart_item = CartItem()
			cart_item.cart_item_id = item_id
			cart_item.cart_id = self.cart_reference_uuid
			cart_item.quantity = item['quantity']
			cart_item.display_price = float(json_order_item['basePrice'])
			cart_item.offer_price = float(json_order_item['offerPrice'])
			cart_item.promo_codes = item.get('promocodes')
			cart_item.same_day_delivery = 'SDD' if json_order_item.get(
				'deliveryDays') == 0 else 'NDD'
			cart_item.transfer_price = float(json_order_item['offerPrice'])
			cart_item.title = json_order_item['title']
			cart_item.image_url = json_order_item['imageURL']
			cart_item_list.append(cart_item)

			self.total_price += float(json_order_item['offerPrice']) * int(
				item['quantity'])
			self.total_display_price += float(
				json_order_item['basePrice']) * int(item['quantity'])

		self.cart_items = cart_item_list

	def save_address_and_get_hash(self, data):
		addr1 = data.get('shipping_address')
		self.shipping_address = data.get('shipping_address')
		address = Address.get_address(name=addr1["name"],
									  mobile=addr1["mobile"],
									  address=addr1["address"],
									  city=addr1.get("city"),
									  pincode=addr1.get("pincode"),
									  state=addr1.get("state"),
									  email=addr1.get('email'),
									  landmark=addr1.get('landmark'))

		return address

	def update_cart_items(self, data, cart, operation):

		self.item_id_to_existing_item_dict = {}
		for existing_cart_item in cart.cartItem:
			self.item_id_to_existing_item_dict[
				existing_cart_item.cart_item_id] = existing_cart_item

		no_of_left_items_in_cart = self.item_id_to_existing_item_dict.values().__len__()
		self.deleted_cart_items = {}
		if 'orderitems' in data and data['orderitems'].__len__() > 0:
			if operation == 0:
				for data_item in data['orderitems']:
					if data_item['quantity'] == 0 and no_of_left_items_in_cart > 0:
						existing_cart_item = self.item_id_to_existing_item_dict.get(data_item['item_uuid'])
						if existing_cart_item is None:
							raise IncorrectDataException(ERROR.NOT_EXISTING_ITEM_CAN_NOT_BE_DELETED)
						del self.item_id_to_existing_item_dict[data_item['item_uuid']]
						no_of_left_items_in_cart = self.item_id_to_existing_item_dict.values().__len__()
						self.deleted_cart_items[data_item['item_uuid']] = existing_cart_item

					elif data_item['quantity'] == 0 and no_of_left_items_in_cart == 0:
						Logger.info("[%s] Cart is empty", g.UUID)
						raise EmptyCartException(ERROR.CART_EMPTY)

					elif data_item[
						'item_uuid'] in self.item_id_to_existing_item_dict:
						existing_cart_item = self.item_id_to_existing_item_dict.get(
							data_item['item_uuid'])
						existing_cart_item.quantity = data_item['quantity']
						existing_cart_item.promo_codes = data_item.get(
							'promo_codes')

					elif data_item[
						'item_uuid'] not in self.item_id_to_existing_item_dict and \
									data_item['quantity'] > 0:
						new_cart_item = CartItem()
						new_cart_item.cart_id = cart.cart_reference_uuid
						new_cart_item.cart_item_id = data_item['item_uuid']
						new_cart_item.quantity = data_item['quantity']
						new_cart_item.promo_codes = data_item.get('promo_codes')
						new_cart_item.item_discount = 0.0
						self.item_id_to_existing_item_dict[
							int(data_item['item_uuid'])] = new_cart_item
						no_of_left_items_in_cart = self.item_id_to_existing_item_dict.values().__len__()

			elif operation == 1:
				for data_item in data['orderitems']:
					if data_item['item_uuid'] in self.item_id_to_existing_item_dict and data_item['quantity']>0:
						existing_cart_item = self.item_id_to_existing_item_dict.get(data_item['item_uuid'])
						existing_cart_item.quantity += data_item['quantity']

					elif data_item['item_uuid'] not in self.item_id_to_existing_item_dict and data_item['quantity']>0:
						new_cart_item = CartItem()
						new_cart_item.cart_id = cart.cart_reference_uuid
						new_cart_item.cart_item_id = data_item['item_uuid']
						new_cart_item.quantity = data_item['quantity']
						new_cart_item.promo_codes = data_item.get('promo_codes')
						new_cart_item.item_discount = 0.0
						self.item_id_to_existing_item_dict[
							int(data_item['item_uuid'])] = new_cart_item

			elif operation == 2:
				for data_item in data['orderitems']:
					existing_cart_item = self.item_id_to_existing_item_dict.get(data_item['item_uuid'])
					if existing_cart_item is None:
						raise IncorrectDataException(ERROR.NOT_EXISTING_ITEM_CAN_NOT_BE_DELETED)
					if no_of_left_items_in_cart ==1 and existing_cart_item.quantity == 1 and cart.promo_codes is not None and cart.promo_codes != []:
						raise RemoveCouponBeforeDeletingLastItem(ERROR.REMOVE_COUPON_BEFORE_DELETING_LAST_ITEM)
					if data_item['quantity'] >= existing_cart_item.quantity:
						existing_cart_item.quantity = 0
					else:
						existing_cart_item.quantity -= data_item['quantity']
					if existing_cart_item.quantity == 0:
						del self.item_id_to_existing_item_dict[data_item['item_uuid']]
						self.deleted_cart_items[data_item['item_uuid']] = existing_cart_item

		request_items = list()
		for cart_item in self.item_id_to_existing_item_dict.values():
			request_item_detail = {"item_uuid": cart_item.cart_item_id,
								   "quantity": cart_item.quantity}
			request_items.append(request_item_detail)

		if self.item_id_to_existing_item_dict.values().__len__() > 0:
			order_item_price_dict = check_prices_of_item(request_items,
															  data)
			Logger.info("order_item_price_dict is [%s]",
						(json.dumps(order_item_price_dict)))
			for key in self.item_id_to_existing_item_dict:
				existing_cart_item = self.item_id_to_existing_item_dict[key]
				key = int(key)
				cart_item = order_item_price_dict.get(key)
				if cart_item is not None:
					existing_cart_item.same_day_delivery = 'SDD' if cart_item.get(
						'deliveryDays') == 0 else 'NDD'
					existing_cart_item.display_price = cart_item.get(
						'basePrice')
					existing_cart_item.offer_price = cart_item.get(
						'offerPrice')
					existing_cart_item.transfer_price = cart_item.get(
						'transferPrice')
					existing_cart_item.title = cart_item.get('title')
					existing_cart_item.image_url = cart_item.get('imageURL')

	def check_for_coupons_applicable(self, data, cart):
		if self.item_id_to_existing_item_dict.values() is not None and self.item_id_to_existing_item_dict.values().__len__()>0:
			response_data = get_response_from_check_coupons_api(
				self.item_id_to_existing_item_dict.values(), data,
				cart)
			if "error" in response_data:
				if 'promo_codes' in data and hasattr(data.get('promo_codes'),
													 '__iter__') and data.get(
						'promo_codes') != []:
					remove_discounts(
						self.item_id_to_existing_item_dict.values(), cart)

					db.session.add(cart)
					db.session.add_all(self.item_id_to_existing_item_dict.values())
					db.session.commit()
					error_msg = response_data['error'].get('error')
					ERROR.INTERNAL_ERROR.message = error_msg
					raise CouponInvalidException(
						ERROR.INTERNAL_ERROR)
				else:
					Logger.info(
						"[%s] Updating discount to 0 because of coupon error [%s]",
						g.UUID, response_data.get('error'))
					remove_discounts(
						self.item_id_to_existing_item_dict.values(), cart)
			else:

				self.fetch_freebie_details_and_update(response_data['benefits'],
													  order_types[
														  data.get('order_type')], cart)
				self.update_discounts_item_level(response_data,
												 self.item_id_to_existing_item_dict.values())

	def update_address(self, data, cart):
		if data.get('shipping_address') is not None:
			address = self.save_address_and_get_hash(data)
			cart.shipping_address_ref = address.address_hash
		elif cart.shipping_address_ref is not None:
			shipping_address = Address.query.filter_by(
				address_hash=cart.shipping_address_ref).first()
			self.shipping_address = create_address_json(shipping_address)

	def get_count_of_items(self, new_items):
		if new_items is not None:
			return new_items.__len__()
		else:
			return self.item_id_to_existing_item_dict.values().__len__()

	def add_item_to_cart(self, body):
		try:
			request_data = parse_request_data(body)
			validate(request_data, CREATE_CART_SCHEMA)
			cart = get_cart_for_geo_user_id(request_data['geo_id'],
											request_data['user_id'])
			if cart is not None:
				Logger.info("[%s] cart existed is: [%s]", g.UUID, cart.cart_reference_uuid)
				return self.update_cart(cart, request_data, 1)
			else:
				Logger.info("[%s] Cart is none so creating it", g.UUID)
				return self.create_cart(request_data)

		except IncorrectDataException as ide:
			Logger.error("[%s] Validation Error [%s]",
						 g.UUID, str(ide.message))
			return create_error_response(ide)
		except Exception as exception:
			Logger.error(
				'[%s] Exception occured while creating/updating cart [%s]',
				g.UUID, str(exception), exc_info=True)
			ERROR.INTERNAL_ERROR.message = str(exception)
			return create_error_response(ERROR.INTERNAL_ERROR)

	def create_cart_no_price_cal(self, data):
		error = True
		err = None
		while True:

			# 0. Validation
			try:
				validate_create_new_cart(data)
			except RequiredFieldMissing as rfm:
				Logger.error(
					'[%s] Required field is missing in creating cart API call[%s]',
					g.UUID, str(rfm),
					exc_info=True)
				err = ERROR.CART_ITEM_MISSING
				break
			except IncorrectDataException as ide:
				Logger.error('[%s] Zero quantity can not be added[%s]',
							 g.UUID, str(ide),
							 exc_info=True)
				err = ERROR.INCORRECT_DATA
				break

			# 1. Initialize cart object
			try:
				self.cart_reference_uuid = uuid.uuid1().hex
				cart = Cart()
				self.prepare_cart_object(data, cart)
			except Exception as exception:
				Logger.error(
					"[%s] Exception occurred in populating cart object [%s]",
					g.UUID, str(exception), exc_info=True)
				ERROR.INTERNAL_ERROR.message = str(exception)
				err = ERROR.INTERNAL_ERROR
				break

			# 2. save in DB
			try:
				self.save_new_item_to_cart(cart)
			except Exception as exception:
				Logger.error(
					"[%s] Exception occurred in saving cart item in DB [%s]",
					g.UUID, str(exception), exc_info=True)
				ERROR.DATABASE_ERROR.message = str(exception)
				err = ERROR.DATABASE_ERROR
				break

			# 3. create response
			try:
				response_data = self.generate_add_item_to_cart_response(
					self.cart_items, cart)
			except Exception as exception:
				Logger.error(
					"[%s] Exception occurred in generating response for cart [%s]",
					g.UUID, str(exception),
					exc_info=True)
				ERROR.INTERNAL_ERROR.message = str(exception)
				err = ERROR.INTERNAL_ERROR
				break

			error = False
			break

		if error:
			db.session.rollback()
			return create_error_response(err)
		else:
			db.session.commit()
			return create_data_response(data=response_data)

	def prepare_cart_object(self, data, cart):

		cart.geo_id = int(data['geo_id'])
		cart.user_id = data['user_id']
		cart.cart_reference_uuid = self.cart_reference_uuid
		cart.order_type = order_types[0]
		if data.get('order_type') is not None:
			cart.order_type = order_types[data.get('order_type')]
		cart.order_source_reference = data['order_source_reference']
		cart_item_list = list()
		for item in data['orderitems']:
			cart_item = CartItem()
			cart_item.cart_item_id = item['item_uuid']
			cart_item.cart_id = self.cart_reference_uuid
			cart_item.quantity = 1 if item.get(
				'quantity') is None else item.get('quantity')
			cart_item_list.append(cart_item)

		self.cart_items = cart_item_list

	def save_new_item_to_cart(self, cart):
		db.session.add(cart)
		for cart_item in self.cart_items:
			db.session.add(cart_item)

	def generate_add_item_to_cart_response(self, new_items, cart):
		response_json = {
			"cart_reference_uuid": cart.cart_reference_uuid,
			"cart_items_count": self.get_count_of_items(new_items)
		}
		return response_json

	def add_item_to_existing_cart_no_price_cal(self, cart, data):
		error = True
		err = None
		while True:
			# 1 Item update(Added, removed, update)
			try:
				self.update_cart_items_no_price_cal(cart, data)

			except IncorrectDataException:
				Logger.error("[%s] Non existing item can not be deleted",
							 g.UUID)
				err = ERROR.NOT_EXISTING_ITEM_CAN_NOT_BE_DELETED
				break
			except EmptyCartException:
				Logger.error("[%s] Cart has become empty", g.UUID)
				self.is_cart_empty = True
				err = ERROR.CART_EMPTY
				break
			except Exception as exception:
				Logger.error(
					"[%s] Exception occurred in updating cart items [%s]",
					g.UUID, str(exception), exc_info=True)
				ERROR.INTERNAL_ERROR.message = str(exception)
				err = ERROR.INTERNAL_ERROR
				break

			# 6 Save cart
			try:

				for each_cart_item in self.item_id_to_existing_item_dict.values():
					db.session.add(each_cart_item)
				if self.deleted_cart_items.values().__len__() > 0:
					for each_deleted_item in self.deleted_cart_items.values():
						db.session.delete(each_deleted_item)

			except Exception as exception:
				Logger.error('[%s] Shipping address could not be updated [%s]',
							 g.UUID, str(exception), exc_info=True)
				err = ERROR.DATABASE_ERROR
				break

			# 7 Create Response
			try:
				response_data = self.generate_add_item_to_cart_response(
					self.item_id_to_existing_item_dict, cart)
			except Exception as exception:
				Logger.error(
					'[%s] Exception occurred in creating response while updating the cart [%s]',
					g.UUID, str(exception),
					exc_info=True)
				ERROR.INTERNAL_ERROR.message = str(exception)
				err = ERROR.INTERNAL_ERROR
				break

			error = False
			break
		if error:
			db.session.rollback()
			return create_error_response(err)
		else:
			db.session.commit()
			return create_data_response(data=response_data)

	def update_cart_items_no_price_cal(self, cart, data):
		self.item_id_to_existing_item_dict = {}
		for existing_cart_item in cart.cartItem:
			self.item_id_to_existing_item_dict[
				existing_cart_item.cart_item_id] = existing_cart_item

		no_of_left_items_in_cart = self.item_id_to_existing_item_dict.values().__len__()
		self.deleted_cart_items = {}

		if 'orderitems' in data and data['orderitems'].__len__() > 0:

			for data_item in data['orderitems']:

				if data_item['quantity'] == 0 and no_of_left_items_in_cart > 0:
					existing_cart_item = self.item_id_to_existing_item_dict.get(
						data_item['item_uuid'])
					if existing_cart_item is None:
						raise IncorrectDataException(
							ERROR.NOT_EXISTING_ITEM_CAN_NOT_BE_DELETED)
					del self.item_id_to_existing_item_dict[
						data_item['item_uuid']]
					no_of_left_items_in_cart = self.item_id_to_existing_item_dict.values().__len__()
					self.deleted_cart_items[
						data_item['item_uuid']] = existing_cart_item

				elif data_item[
					'item_uuid'] in self.item_id_to_existing_item_dict:
					existing_cart_item = self.item_id_to_existing_item_dict.get(
						data_item['item_uuid'])
					existing_cart_item.quantity = existing_cart_item + 1 if data_item.get(
						'quantity') is None else data_item.get('quantity')

				elif data_item[
					'item_uuid'] not in self.item_id_to_existing_item_dict and \
								data_item['quantity'] > 0:
					new_cart_item = CartItem()
					new_cart_item.cart_id = cart.cart_reference_uuid
					new_cart_item.cart_item_id = data_item['item_uuid']
					new_cart_item.quantity = 1 if data_item.get(
						'quantity') is None else data_item.get('quantity')
					self.item_id_to_existing_item_dict[
						int(data_item['item_uuid'])] = new_cart_item
					no_of_left_items_in_cart = self.item_id_to_existing_item_dict.values().__len__()

				if data_item[
					'quantity'] == 0 and no_of_left_items_in_cart == 0:
					Logger.info("[%s] Cart is empty", g.UUID)
					raise EmptyCartException(ERROR.CART_EMPTY)

	def fetch_freebie_details_and_update(self, benefits, order_type, cart):
		benefit_list = list()
		check_freebie_is_applicable(benefits, cart)
		for each_benefit in benefits:
			if each_benefit.get('type') == 0 or each_benefit.get('type') == 1:
				"""
					{
					  "couponCode": "freebie_noida",
					  "items": [
						"1151594",
						"2007982"
					  ],
					  "paymentMode": [],
					  "freebies": [
						[
						  1151594
						]
					  ],
					  "custom": null,
					  "benefit_type": 2,
					  "max_cap": null,
					  "type": 1,
					  "channel": []
					}
				"""
				freebies_id_list = each_benefit['freebies'][0]
				if freebies_id_list is not None and freebies_id_list.__len__() > 0:
					freebee_detail_list = get_freebie_details(freebies_id_list, order_type)
					benefit = dict(freebies=freebee_detail_list,
								   type=each_benefit.get('type'),
								   couponCode=each_benefit.get('couponCode'))
					benefit_list.append(benefit)

		if benefit_list.__len__() > 0:
			self.benefits = benefit_list
		else:
			self.benefits = None

	def get_total_payble_price(self):
		return self.total_price - self.total_discount + self.total_shipping_charges

	def change_user(self, data):
		data = json.loads(data)
		old_user = data.get("old_user_id", None)
		new_user = data.get("user_id", None)
		geo_id = data.get("geo_id", None)

		try:
			cart1 = get_cart_for_geo_user_id(geo_id, old_user)
			cart2 = get_cart_for_geo_user_id(geo_id, new_user)
			if cart1 is not None:
				if len(cart1.cartItem) == 0:
					remove_cart(cart1.cart_reference_uuid)
					# return Cart2
					# TODO: Fix this
					data[
						'order_source_reference'] = cart2.order_source_reference
					data['order_type'] = 0
					return self.update_cart(cart2, data, 0)
				else:
					if cart2 is not None:
						remove_cart(cart2.cart_reference_uuid)
					# replace old_user by new_user
					cart1.user_id = new_user
					# return Cart1
					data[
						'order_source_reference'] = cart1.order_source_reference
					data['order_type'] = 0
					return self.update_cart(cart1, data, 0)
			else:
				# return Cart2
				if cart2 is None:
					return create_error_response(
						ERROR.CHANGE_USER_NOT_POSSIBLE)
				data['order_source_reference'] = cart2.order_source_reference
				data['order_type'] = 0
				return self.update_cart(cart2, data, 0)

		except Exception as exception:
			Logger.error('[%s] Exception occured while change_user [%s]',
						 g.UUID, str(exception), exc_info=True)
			ERROR.INTERNAL_ERROR.message = str(exception)
			return create_error_response(ERROR.INTERNAL_ERROR)

	def add_to_cart(self, body):
		try:
			Logger.info("[%s] Add To Cart request body [%s]", \
						g.UUID, body)
			request_data = parse_request_data(body)
			validate(request_data, CREATE_CART_SCHEMA)
			cart = get_cart_for_geo_user_id(request_data['geo_id'], \
											request_data['user_id'])
			if cart is not None:
				return self.update_cart(cart, request_data, 1)
			else:
				return self.create_cart(request_data)

		except IncorrectDataException as ide:
			Logger.error("[%s] Validation Error [%s]",
						 g.UUID, str(ide.message))
			return create_error_response(ide)
		except Exception as exception:
			Logger.error('[%s] Exception occured while creating/updating\
						cart [%s]', g.UUID, str(exception), exc_info=True)
			ERROR.INTERNAL_ERROR.message = str(exception)
			return create_error_response(ERROR.INTERNAL_ERROR)

	def remove_from_cart(self, body):
		try:
			Logger.info("[%s] Remove from cart request body [%s]", \
						g.UUID, body)
			request_data = parse_request_data(body)
			validate(request_data, CREATE_CART_SCHEMA)
			cart = get_cart_for_geo_user_id(request_data['geo_id'], \
											request_data['user_id'])
			if cart is not None:
				return self.update_cart(cart, request_data, 2)
			else:
				Logger.error("[%s] Cart does not exist for geo_id: [%s] and user_id: [%s]", g.UUID, request_data['geo_id'], request_data['user_id'])
				return create_error_response(ERROR.NO_SUCH_CART_EXIST)
		except RemoveCouponBeforeDeletingLastItem as rc:
			Logger.error("[%s] Remove coupon before deleting last item from the cart [%s]", g.UUID, str(rc.message))
			return create_error_response(rc)
		except IncorrectDataException as ide:
			Logger.error("[%s] Validation Error [%s]", g.UUID, str(ide.message))
			return create_error_response(ide)
		except Exception as exception:
			Logger.error('[%s] Exception occured while creating/updating\
						cart [%s]', g.UUID, str(exception), exc_info=True)
			ERROR.INTERNAL_ERROR.message = str(exception)
			return create_error_response(ERROR.INTERNAL_ERROR)
