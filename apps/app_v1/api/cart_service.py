from apps.app_v1.api import parse_request_data, RequiredFieldMissing, EmptyCartException, IncorrectDataException, \
	CouponInvalidException
from apps.app_v1.api.api_schema_signature import CREATE_CART_SCHEMA
from apps.app_v1.models.models import Cart, Cart_Item, Address
from utils.jsonutils.output_formatter import create_error_response, create_data_response
from utils.jsonutils.json_schema_validator import validate
from config import APP_NAME
import datetime, logging, json, uuid, requests
from flask import g, current_app
from apps.app_v1.models.models import db
import config
from apps.app_v1.api import error_code, error_messages

__author__ = 'divyagarg'

Logger = logging.getLogger(APP_NAME)


def check_if_calculate_price_api_response_is_correct_or_quantity_is_available(item, json_order_item):
	if json_order_item is None:
		Logger.error(
			"{%s} No item is found in calculate price API response for the item {%s}" % (g.UUID, item['item_uuid']),
			exc_info=True)
		return create_error_response(200, message='Error in calculate price')
	if json_order_item.get('available_quantity') is not None:
		Logger.error(
			"{%s} Item quantity asked for is not available {%s} for the quantity {%s}" % (
				g.UUID, item['item_uuid'], item[
					'quantity']), exc_info=True)
		return create_error_response(200, message='Quanity is not Available')


class CartService:
	def __init__(self):
		"""

		:type self: object
		"""
		self.cart_reference_uuid = None
		self.geoid = None
		self.userid = None
		self.order_type = None
		self.order_source_reference = "WEB"
		self.promocodes = None
		self.items = None
		self.total_price = 0.0
		self.total_discount = 0.0
		self.total_display_price = 0.0
		self.now = datetime.datetime.utcnow()
		self.cart_items = None
		self.item_id_to_existing_item_map = None
		self.total_shipping_charges = 0.0
		self.payment_mode = None,
		self.shipping_address = None
		self.benefits = None

	def create_or_update_cart(self, body):
		try:
			request_data = parse_request_data(body)
			validate(request_data, CREATE_CART_SCHEMA)
			self.initialize_cart_with_request(request_data)
			cart = self.get_cart_for_geo_user_id()
			if cart is not None:
				return self.update_cart(cart)
			else:
				if self.cart_items.__len__() == 0:
					raise RequiredFieldMissing(code=error_code['data_missing'], message='cart items are missing')
				else:
					for each_cart_item in self.cart_items:
						if each_cart_item['quantity'] == 0:
							raise IncorrectDataException(code=error_code['data_missing'],
														 message='zero quantity can not be added')
				return self.create_cart(request_data)

		except RequiredFieldMissing as rfm:
			Logger.error('{%s} Required field is missing in creating/updating cart API call{%s}' % (g.UUID, str(rfm)),
						 exc_info=True)
			return create_error_response(code=error_code["data_missing"], message=str(rfm))
		except IncorrectDataException as ide:
			Logger.error('{%s} Zero quantity can not be added{%s}' % (g.UUID, str(ide)),
						 exc_info=True)
			return create_error_response(code=error_code["data_missing"], message=str(ide))
		except Exception as e:
			Logger.error('{%s} Exception occured while creating/updating cart {%s}' % (g.UUID, str(e)), exc_info=True)
			return create_error_response(code=error_code["cart_error"], message=str(e))

	def initialize_cart_with_request(self, request_data):
		self.geoid = request_data['data']['geo_id']
		self.userid = request_data['data']['user_id']
		self.order_type = request_data['data'].get('order_type')
		self.order_source_reference = request_data['data']['order_source_reference']
		if hasattr(request_data['data'].get('promo_codes'), '__iter__'):
			self.promocodes = map(str, request_data['data']['promo_codes'])
		self.cart_items = request_data['data']['orderitems']
		self.payment_mode = request_data['data'].get('payment_mode')
		self.shipping_address = request_data['data'].get('shipping_address')

	def get_cart_for_geo_user_id(self):
		return Cart().query.filter_by(geo_id=self.geoid, user_id=self.userid).first()

	def update_cart(self, cart):
		item_id_to_existing_item_map = {}
		for existing_cart_item in cart.cartItem:
			item_id_to_existing_item_map[existing_cart_item.cart_item_id] = existing_cart_item

		self.item_id_to_existing_item_map = item_id_to_existing_item_map
		Logger.info("[%s] Updating the cart [%s]" % (g.UUID, cart.cart_reference_uuid))
		self.cart_reference_uuid = cart.cart_reference_uuid
		if self.promocodes == []:
			cart.promo_codes = None
		else:
			cart.promo_codes = self.promocodes
		return self.update_items_in_cart(cart)

	def create_cart(self, request_data):
		cart = Cart()
		self.cart_reference_uuid = uuid.uuid1().hex
		Logger.info("[%s] Creating the cart [%s]" % (g.UUID, self.cart_reference_uuid))
		return self.insert_data_to_new_cart(request_data, cart)

	def remove_cart_item_from_cart(self, cart_item_db):
		db.session.delete(cart_item_db)

	def change_quantity_of_cart_item(self, cart_item_db, check_price_json, item):
		cart_item_db.quantity = item['quantity']
		cart_item_db.display_price = check_price_json['display_price']
		cart_item_db.offer_price = check_price_json['offer_price']

	def add_new_item_to_cart(self, cart_item_db, json_order_item, item):
		cart_item_db.cart_item_id = item['item_uuid']
		cart_item_db.cart_id = self.cart_reference_uuid
		cart_item_db.quantity = item['quantity']
		cart_item_db.cart_id = self.cart_reference_uuid
		cart_item_db.display_price = float(json_order_item['display_price'])
		cart_item_db.offer_price = float(json_order_item['offer_price'])

	def check_quantity_availability_of_item(self, item):
		dummy_item_list = list()
		dummy_item_list.append(item)
		response_data = self.fetch_product_price(dummy_item_list)
		order_item_dict = {}
		for response in response_data:
			order_item_dict[response['item_uuid']] = response
		json_order_item = order_item_dict.get(item['item_uuid'])
		check_if_calculate_price_api_response_is_correct_or_quantity_is_available(item, json_order_item)
		return order_item_dict

	def update_items_in_cart(self, cart):
		if self.cart_items.__len__() > 0:
			try:
				self.update_quantity_of_items_in_cart()
			except EmptyCartException:
				cart.total_discount = 0.0
				cart.total_offer_price = 0.0
				cart.total_display_price = 0.0
				cart.total_shipping_charges = 0.0
				cart.promo_codes = None
				db.session.add(cart)
				db.session.commit()
				return create_data_response(data=self.generate_response(None))

		cart.payment_mode = self.payment_mode
		response_data = self.get_response_from_check_coupons_api(self.item_id_to_existing_item_map.values())
		try:
			self.update_discounts_item_level(response_data, self.item_id_to_existing_item_map.values())
		except CouponInvalidException as cie:
			Logger.error('[%s] Coupon can not be applied [%s]' % (g.UUID, str(cie)),
						 exc_info=True)
			db.session.rollback()
			return create_error_response(code=error_code['coupon_error'], message=str(cie))
		try:
			self.update_cart_total_amounts(cart)
			if self.shipping_address is not None:
				hash = self.save_address_and_get_hash()
				cart.shipping_address_ref = hash
			cart.total_shipping_charges = 0.0
			self.get_shipping_charges()
			cart.total_shipping_charges = self.total_shipping_charges

			db.session.add(cart)
			for each_cart_item in self.item_id_to_existing_item_map.values():
				db.session.add(each_cart_item)
			response_data = self.generate_response(None)
			db.session.commit()
			return create_data_response(data=response_data)
		except Exception as e:
			Logger.error("[%s] Error in getting response [%s]" % (g.UUID, str(e)), exc_info=True)
			db.session.rollback()
			return create_error_response(code=error_code["cart_error"], message=str(e))

	def populate_cart_object(self, request_data, cart):
		cart.geo_id = self.geoid
		cart.user_id = self.userid
		cart.cart_reference_uuid = self.cart_reference_uuid
		cart.order_type = request_data['data']['order_type']
		cart.order_source_reference = request_data['data']['order_source_reference']
		cart.total_shipping_charges = self.total_shipping_charges
		print("Updating cart promo code from [%s] to [%s]" % (cart.promo_codes, self.promocodes))
		cart.promo_codes = self.promocodes
		cart.payment_mode = request_data['data'].get('payment_mode')
		addr1 = request_data['data'].get('shipping_address')
		if addr1 is not None:
			shipping_address = Address()
			shipping_address.name = addr1["name"]
			shipping_address.mobile = addr1["mobile"]
			shipping_address.street_1 = addr1["address"]
			shipping_address.city = addr1["city"]
			shipping_address.pincode = addr1["pincode"]
			shipping_address.state = addr1["state"]
			shipping_address.email = addr1["mobile"]
			shipping_address.landmark = addr1["landmark"]
			shipping_address.address_hash = shipping_address.__hash__()
			db.session.add(shipping_address)
			cart.shipping_address_ref = shipping_address.address_hash

	def fetch_items_price_return_dict(self, cart_items):
		response_product_fetch_data = self.fetch_product_price(cart_items)
		order_item_dict = {}
		for response in response_product_fetch_data:
			order_item_dict[response['item_uuid']] = response
		return order_item_dict

	def insert_data_to_new_cart(self, request_data, cart):
		self.get_shipping_charges()
		self.populate_cart_object(request_data, cart)
		self.get_price_and_update_in_cart_item()
		response_data = self.get_response_from_check_coupons_api(self.cart_items)
		self.update_discounts_item_level(response_data, self.cart_items)
		cart.total_offer_price = self.total_price
		cart.total_display_price = self.total_display_price
		cart.total_discount = self.total_discount
		try:
			db.session.add(cart)
			for cart_item in self.cart_items:
				db.session.add(cart_item)
			response_data = self.generate_response(self.cart_items)
			db.session.commit()
			return create_data_response(data=response_data)
		except Exception as e:
			Logger.error("{%s} Exception occurred while insert new items to Cart {%s}" % (g.UUID, str(e)),
						 exc_info=True)
			db.session.rollback()
			return create_error_response(code=500, message='DB Error')

	def fetch_product_price(self, items):
		request_items = list()
		for item in items:
			request_item_detail = {}
			request_item_detail["item_uuid"] = item["item_uuid"]
			request_item_detail["quantity"] = item["quantity"]
			request_items.append(request_item_detail)

		data = {
			"geo_id": self.geoid,
			"items": request_items
		}
		request_data = json.dumps(data)
		Logger.info("{%s} Request data for calculate price API is {%s}" % (g.UUID, request_data))
		response = requests.post(url=current_app.config['PRODUCT_CATALOGUE_URL'], data=request_data,
								 headers={'Content-type': 'application/json'})
		json_data = json.loads(response.text)
		Logger.info("{%s} Response got from calculate Price API is {%s}" % (g.UUID, json.dumps(json_data)))
		return json_data['items']

	def generate_response(self, new_items):

		response_json = {
			"orderitems": [],
			"total_offer_price": self.total_price,
			"total_display_price": self.total_display_price,
			"total_discount": self.total_discount,
			"total_shipping_charges": self.total_shipping_charges,
			"cart_reference_uuid": str(self.cart_reference_uuid),
			"benefits": self.benefits
		}

		if new_items is not None:
			items = list()
			for item in new_items:
				order_item_dict = {}
				order_item_dict["item_uuid"] = item.cart_item_id
				order_item_dict["display_price"] = item.display_price
				order_item_dict["offer_price"] = item.offer_price
				order_item_dict["quantity"] = item.quantity
				order_item_dict["item_discount"] = item.item_discount
				items.append(order_item_dict)
			response_json["orderitems"].append(items)

		elif self.item_id_to_existing_item_map.values().__len__() != 0:
			items = list()
			for item in self.item_id_to_existing_item_map.values():
				order_item_dict = {}
				order_item_dict["item_uuid"] = item.cart_item_id
				order_item_dict["display_price"] = str(item.display_price)
				order_item_dict["offer_price"] = str(item.offer_price)
				order_item_dict["quantity"] = item.quantity
				order_item_dict["item_discount"] = str(item.item_discount)
				items.append(order_item_dict)
			response_json["orderitems"].append(items)

		return response_json

	def update_discounts_item_level(self, response_data, cart_items):
		item_discount_dict = {}
		if response_data['success']:
			self.total_discount = float(response_data['totalDiscount'])
			self.benefits = response_data['benefits']
			for item in response_data['products']:
				item_discount_dict[item['itemid']] = item

			for each_cart_item in cart_items:
				each_cart_item.item_discount = float(item_discount_dict[int(each_cart_item.cart_item_id)]['discount'])
		else:
			error_msg = response_data['error'].get('error')
			raise CouponInvalidException(code = error_code['coupon_error'], message = error_msg)

	def get_shipping_charges(self):
		if (self.total_price - self.total_discount) <= config.SHIPPING_COST_THRESHOLD and (self.total_price - self.total_discount)>0:
			self.total_shipping_charges = float(config.SHIPPING_COST)

	def update_quantity_of_items_in_cart(self):
		no_of_left_items_in_cart = self.item_id_to_existing_item_map.values().__len__()
		for item in self.cart_items:
			try:
				cart_item_db = self.item_id_to_existing_item_map.get(item['item_uuid'])
				check_price_json = self.check_quantity_availability_of_item(item)
				if cart_item_db is not None:
					cart_item_db.same_day_delivery = check_price_json.get(item['item_uuid']).get('same_day_delivery')
					if item.get('promocodes') is not None:
						cart_item_db.promo_codes = item['promocodes']
					if item['quantity'] == 0:
						self.remove_cart_item_from_cart(cart_item_db)
						del self.item_id_to_existing_item_map[item['item_uuid']]
						no_of_left_items_in_cart = self.item_id_to_existing_item_map.values().__len__()
					elif cart_item_db.quantity == item['quantity']:
						continue
					elif item['quantity'] != cart_item_db.quantity:
						self.change_quantity_of_cart_item(cart_item_db, check_price_json[item['item_uuid']], item)
				elif cart_item_db is None and item['quantity'] > 0:
					cart_item_db = Cart_Item()
					cart_item_db.same_day_delivery = check_price_json.get(item['item_uuid']).get('same_day_delivery')
					self.add_new_item_to_cart(cart_item_db, check_price_json[item['item_uuid']], item)
					self.item_id_to_existing_item_map[item['item_uuid']] = cart_item_db
			except Exception as e:
				Logger.error("[%s] Exception occurred in Updating the cart [%s] " % (g.UUID, str(e)), exc_info=True)
				return create_error_response(code=error_code["cart_error"], message=str(e))
		if self.cart_items.__len__() > 0 and no_of_left_items_in_cart == 0:
			Logger.info("[%s] Cart is empty" % g.UUID)
			raise EmptyCartException(code=error_code['cart_empty'], message=error_messages["cart_empty"])

	def update_cart_total_amounts(self, cart):
		cart.total_display_price = 0.0
		cart.total_offer_price = 0.0
		cart.total_discount = 0.0
		for each_cart_item in self.item_id_to_existing_item_map.values():
			unit_offer_price = each_cart_item.offer_price
			unit_display_price = each_cart_item.display_price
			quantity = each_cart_item.quantity
			item_level_discount = each_cart_item.item_discount
			cart.total_display_price += (float(unit_display_price) * quantity)
			cart.total_offer_price += (float(unit_offer_price) * quantity)
			cart.total_discount = float(cart.total_discount) + float(item_level_discount)

		self.total_display_price = cart.total_display_price
		self.total_price = cart.total_offer_price
		self.total_discount = cart.total_discount

	def get_response_from_check_coupons_api(self, cart_items):
		data = {
			"coupon_codes": self.promocodes,
			"area_id": self.geoid,
			"customer_id": self.userid,
			'channel': self.order_source_reference,
			"products": [
				{"item_id": each_cart_item.cart_item_id, "quantity": each_cart_item.quantity,
				 "coupon_code": each_cart_item.promo_codes}
				for each_cart_item in cart_items],
			"payment_mode": self.payment_mode
		}
		header = {
			'X-API-USER': 'askmegrocery',
			'X-API-TOKEN': 'M2JmN2U5NGYtMDJlNi0xMWU2LWFkZGQtMjRhMDc0ZjE1MGYy',
			'Content-type': 'application/json'
		}

		response = requests.post(url=current_app.config['COUPON_CHECK_URL'], data=json.dumps(data),
								 headers=header)
		json_data = json.loads(response.text)
		Logger.info(
			"[%s] Request to check Coupon data passed is: [%s] and response is: [%s]" % (g.UUID, data, json_data))
		Logger.info(
			'{%s} Resonse text from url {%s} with data {%s} is {%s}' % (
				g.UUID, current_app.config['COUPON_CHECK_URL'], data, json_data))
		return json_data

	def get_price_and_update_in_cart_item(self):
		order_item_dict = self.fetch_items_price_return_dict(self.cart_items)
		cart_item_list = list()
		for item in self.cart_items:
			json_order_item = order_item_dict.get(item['item_uuid'])
			check_if_calculate_price_api_response_is_correct_or_quantity_is_available(item, json_order_item)
			cart_item = Cart_Item()
			cart_item.cart_item_id = item['item_uuid']
			cart_item.cart_id = self.cart_reference_uuid
			cart_item.quantity = json_order_item['quantity']
			cart_item.display_price = float(json_order_item['display_price'])
			cart_item.offer_price = float(json_order_item['offer_price'])
			cart_item.promo_codes = item.get('promocodes')
			cart_item.same_day_delivery = json_order_item.get('same_day_delivery')

			cart_item_list.append(cart_item)

			self.total_price += float(json_order_item['offer_price'])
			self.total_display_price += float(json_order_item['display_price'])

		self.cart_items = cart_item_list

	def save_address_and_get_hash(self):
		addr1 = self.shipping_address
		address = Address.get_address(name=addr1["name"], mobile = addr1["mobile"], address = addr1["address"], city = addr1["city"], pincode = addr1["pincode"],state = addr1["state"], email = addr1.get('email'), landmark = addr1.get('landmark'))

		return address.address_hash
