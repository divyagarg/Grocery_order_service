import json
import logging
import traceback
import uuid
import datetime
from apps.app_v1.api.cart_service import CartService
import config
from sqlalchemy import func, distinct
from apps.app_v1.api.api_schema_signature import CREATE_ORDER_SCHEMA_WITH_CART_REFERENCE, \
	CREATE_ORDER_SCHEMA_WITHOUT_CART_REFERENCE
from apps.app_v1.api.status_service import StatusService
from apps.app_v1.models import ORDER_STATUS, DELIVERY_TYPE, order_types, payment_modes_dict, delivery_types
from apps.app_v1.models.models import Order, db, Cart, Address, Order_Item, Status, Payment, Cart_Item
from config import APP_NAME
import requests
from flask import g, current_app
from utils.jsonutils.json_utility import json_serial
from utils.jsonutils.output_formatter import create_error_response, create_data_response
from apps.app_v1.api import ERROR, parse_request_data, NoSuchCartExistException, SubscriptionNotFoundException, \
	PriceChangedException, RequiredFieldMissing, CouponInvalidException, DiscountHasChangedException, \
	FreebieNotApplicableException, NoShippingAddressFoundException, get_shipping_charges, generate_reference_order_id, get_address, \
	get_payment, PaymentCanNotBeNullException
from utils.jsonutils.json_schema_validator import validate
from utils.kafka_utils.kafka_publisher import Publisher

__author__ = 'divyagarg'

Logger = logging.getLogger(APP_NAME)


class OrderService:

	def __init__(self):
		self.cart_reference_id = None
		self.order_reference_id = None
		self.geo_id = None
		self.user_id = None
		self.order_type = None
		self.order_source_reference =None
		self.promo_codes = None
		self.shipping_address = None
		self.billing_address = None
		self.delivery_type = DELIVERY_TYPE.NORMAL.value
		self.delivery_due_date = None
		self.delivery_slot = None
		self.selected_freebies = None
		self.payment_mode = None
		self.order = None
		self.sdd_order = None
		self.ndd_order = None
		# self.now = datetime.datetime.utcnow()
		self.total_offer_price = 0.0
		self.total_shipping_charges = 0.0
		self.total_discount = 0.0
		self.total_display_price = 0.0
		self.total_payble_amount =0.0
		self.order_items = None

		self.item_id_to_item_obj_dict = None
		self.item_id_to_item_json_dict = None

		self.cart_reference_given = None
		self.sdd_items_dict = {}
		self.ndd_items_dict = {}
		self.split_order = False
		self.parent_reference_id = None

	def get_count_of_orders_of_user(self, user_id):
		try:
			if user_id is None or not isinstance(user_id, (unicode, str)):
				return create_error_response(ERROR.VALIDATION_ERROR)
			count = db.session.query(func.count(distinct(Order.parent_order_id))).filter(Order.user_id == user_id).filter(Order.status_id == Status.id).filter(Status.status_code != ORDER_STATUS.CANCELLED.value).group_by(Order.parent_order_id).count()
		except Exception as e:
			Logger.error('{%s} Exception occured while fetching data from db {%s}' % (g.UUID, str(e)), exc_info=True)
			ERROR.INTERNAL_ERROR.message = str(e)
			return create_error_response(ERROR.INTERNAL_ERROR)

		return create_data_response({"count": count})



	def createorder(self, body):
		error = True
		err = None

		while True:

		#1 Parse request
			request_data = parse_request_data(body)
			if "cart_reference_uuid" in request_data.get('data'):
				self.cart_reference_given = True
			else:
				self.cart_reference_given = False
		#2. validate request data fields
			try:
				if self.cart_reference_given:
					validate(request_data, CREATE_ORDER_SCHEMA_WITH_CART_REFERENCE)
				else:
					validate(request_data, CREATE_ORDER_SCHEMA_WITHOUT_CART_REFERENCE)
			except RequiredFieldMissing as rfm:
				Logger.error("[%s] Required field is missing [%s]" %(g.UUID, rfm.message))
				err=rfm
				break
			except Exception as e:
				Logger.error("[%s] Exception occurred in validating order creation request [%s]" %(g.UUID, str(e)), exc_info = True)
				ERROR.INTERNAL_ERROR.message = str(e)
				err = ERROR.INTERNAL_ERROR
				break
		#3. Initialize order Object
			try:
				if self.cart_reference_given:
					self.initialize_order_from_cart_db_data(request_data['data'])
				else:
					self.initialize_order_with_request_data(request_data['data'])
				self.parent_reference_id = generate_reference_order_id()
			except RequiredFieldMissing as rfm:
				Logger.error("[%s] cart is empty [%s]" %(g.UUID, rfm.message))
				err = rfm
				break
			except NoSuchCartExistException as ncee:
				Logger.error("[%s] Cart does not Exist [%s]" %(g.UUID, ncee.message))
				err=ncee
				break
			except Exception as e:
				Logger.error("[%s] Exception occurred in initializing order [%s]" %(g.UUID, str(e)), exc_info = True)
				ERROR.INTERNAL_ERROR.message = str(e)
				err = ERROR.INTERNAL_ERROR
				break
		#3. calculate and validate price
			try:
				self.calculate_and_validate_prices()
			except SubscriptionNotFoundException:
				Logger.error("[%s] Subscript not found for data [%s]" % (g.UUID, json.dumps(request_data['data'])))
				err = ERROR.SUBSCRIPTION_NOT_FOUND
				break
			except  PriceChangedException as pce:
				Logger.error("[%s] Data was stale, price has changed [%s]" %(g.UUID, json.dumps(request_data['data'])))
				err = pce
				break
			except Exception as e:
				Logger.error("[%s] Exception occurred in calculating and validating prices of subscriptions [%s]" %(g.UUID, str(e)), exc_info = True)
				ERROR.INTERNAL_ERROR.message = str(e)
				err = ERROR.INTERNAL_ERROR
				break

		# 4. check and apply coupons and freebie

			try:
				response_data = self.get_response_from_check_coupons_api()
				self.compare_discounts_and_freebies(response_data)
				if self.promo_codes is not None:
					self.apply_coupon()

			except DiscountHasChangedException as dce:
				Logger.error("[%s] Discount has changed  [%s]" % (g.UUID, str(dce.message)))
				err = ERROR.DISCOUNT_CHANGED
				break
			except FreebieNotApplicableException as fnae:
				Logger.error("[%s] Freebie not applicable  [%s]" % (g.UUID, str(fnae.message)))
				err = ERROR.FREEBIE_NOT_ALLOWED
				break
			except CouponInvalidException as cie:
				Logger.error("[%s]Coupon Not valid  [%s]" % (g.UUID, str(cie.message)))
				err = cie
				break
			except Exception as e:
				Logger.error("[%s] Exception occurred in checking discounts [%s]" %(g.UUID, str(e)), exc_info = True)
				ERROR.INTERNAL_ERROR.message = str(e)
				err = ERROR.INTERNAL_ERROR
				break

		#5. Segregate order items based on sdd and ndd, and add freebies with ndd
			self.segregate_order_based_on_ndd_sdd()

		#6 Create two orders based on ndd and sdd and create a master order id
			try:
				self.create_and_save_order()
				self.save_payment()
			except Exception as e:
				Logger.error("[%s] Exception occurred in saving order [%s]" %(g.UUID, str(e)), exc_info = True)
				ERROR.INTERNAL_ERROR.message = str(e)
				err = ERROR.INTERNAL_ERROR
				break

		#7 Delete cart of reference id is given
			try:
				if self.cart_reference_given:
					cart_service = CartService()
					cart_service.remove_cart(self.cart_reference_id)
			except Exception as e:
				traceback.format_exc()
				Logger.error("[%s] Exception occurred in saving order [%s]" %(g.UUID, str(e)), exc_info = True)
				ERROR.INTERNAL_ERROR.message = str(e)
				err = ERROR.INTERNAL_ERROR
				break
		#8 Order History

		#9 Save in old system/ publish on kafka
			# try:
			# 	if not self.split_order:
			# 		message = self.create_publisher_message(self.order)
			# 		Publisher.publish_message(self.order.order_reference_id, json.dumps(message, default=json_serial))
			# 	else:
			# 		message1 = self.create_publisher_message(self.sdd_order)
			# 		Publisher.publish_message(self.order.order_reference_id, json.dumps(message1, default=json_serial))
			# 		message2 = self.create_publisher_message(self.ndd_order)
			# 		Publisher.publish_message(self.order.order_reference_id, json.dumps(message2, default=json_serial))
			# except Exception as e:
			# 	Logger.error("[%s] Exception occured in publishing kafka message [%s]" %(g.UUID, str(e)))
			# 	ERROR.INTERNAL_ERROR.message = str(e)
			# 	err = ERROR.INTERNAL_ERROR
			# 	break
			#
			error = False
			break


		if error:
			db.session.rollback()
			return create_error_response(err)
		else:
			try:
				db.session.commit()
				return create_data_response(self.parent_reference_id)
			except Exception as e:
				Logger.error("[%s] Exception occured in committing db changes [%s]" %(g.UUID, str(e)))
				ERROR.INTERNAL_ERROR.message = str(e)
				return create_error_response(ERROR.INTERNAL_ERROR)

	def initialize_order_from_cart_db_data(self, data):
		self.cart_reference_id = data['cart_reference_uuid']
		cart = Cart.query.filter_by(cart_reference_uuid = self.cart_reference_id).first()
		if cart is None:
			raise NoSuchCartExistException(ERROR.NO_SUCH_CART_EXIST)
		self.user_id = cart.user_id
		self.geo_id = cart.geo_id
		self.order_type = cart.order_type
		self.promo_codes = cart.promo_codes
		self.selected_freebies = cart.selected_freebee_items
		self.total_display_price = cart.total_display_price
		self.total_offer_price = cart.total_offer_price
		self.total_shipping_charges = cart.total_shipping_charges
		self.total_discount = cart.total_discount
		if cart.shipping_address_ref is None:
			raise NoShippingAddressFoundException(ERROR.NO_SHIPPING_ADDRESS_FOUND)
		self.shipping_address = cart.shipping_address_ref
		self.payment_mode = cart.payment_mode
		if cart.cartItem is None:
			raise RequiredFieldMissing(ERROR.CART_EMPTY)
		self.order_items = cart.cartItem
		self.order_source_reference = data['order_source_reference']
		if 'billing_address' in data:
			self.billing_address = data.get('billing_address')
		self.delivery_type = delivery_types[int(data.get('delivery_type'))]
		self.delivery_due_date = data.get('delivery_due_date')
		self.delivery_slot = json.dumps(data.get('delivery_slot'))


	def initialize_order_with_request_data(self, data):
		self.user_id = data.get('user_id')
		self.geo_id = int(data.get('geo_id'))
		self.order_type = order_types[data.get('order_type')]
		self.order_source_reference = data.get('order_source_reference')
		if 'promo_codes' in data and data.__getitem__('promo_codes').__len__() != 0:
			self.promo_codes = data.get('promo_codes')
		if data.get('payment_mode') is not None:
			self.payment_mode = payment_modes_dict[data.get('payment_mode')]
		self.total_display_price = float(data.get('total_display_price')) if data.get('total_display_price') is not None else 0.0
		self.total_offer_price = float(data.get('total_offer_price')) if data.get('total_offer_price') is not None else 0.0
		self.total_shipping_charges = float(data.get('total_shipping_charges')) if data.get('total_shipping_charges') is not None else 0.0
		self.total_discount = float(data.get('total_discount')) if data.get('total_discount') is not None else 0.0
		self.order_items = data.get('orderitems')
		self.shipping_address = data.get('shipping_address')
		if 'billing_address' in data:
			self.billing_address = data.get('billing_address')
		self.selected_freebies = data.get('selected_free_bees_code')
		self.delivery_type = delivery_types[int(data.get('delivery_type'))] if data.get('delivery_type') is not None else None
		self.delivery_slot = json.dumps(data.get('delivery_slot'))

	def fetch_items_price(self, list_of_item_ids):
		req_data = {
			"query": {
				"type": [self.order_type],
				"filters": {
					"id": list_of_item_ids
				},
				"select": config.SEARCH_API_SELECT_CLAUSE
			},
			"count": list_of_item_ids.__len__(),
			"offset": 0
		}
		Logger.info("[%s] Request data for calculate price while creating order is [%s]" %(g.UUID, req_data))
		response = requests.post(url=current_app.config['PRODUCT_CATALOGUE_URL'],
								 data= json.dumps(req_data),
								 headers={'Content-type': 'application/json'})
		json_data = json.loads(response.text)
		Logger.info("{%s} Calculate Price API Request [%s], Response [%s]" % (g.UUID, json.dumps(req_data), json.dumps(json_data)))
		return json_data['results']

	def calculate_and_validate_prices(self):
		list_of_items_ids = list()

		if self.cart_reference_given:
			item_id_to_item_obj_dict = {}
			for order_item in self.order_items:
				list_of_items_ids.append(int(order_item.cart_item_id))
				item_id_to_item_obj_dict[int(order_item.cart_item_id)] = order_item
			self.item_id_to_item_obj_dict = item_id_to_item_obj_dict
		else:
			item_id_to_item_json_dict = {}
			for order_item in self.order_items:
				list_of_items_ids.append(int(order_item.get('item_uuid')))
				item_id_to_item_json_dict[int(order_item.get('item_uuid'))] = order_item
			self.item_id_to_item_json_dict = item_id_to_item_json_dict

		response = self.fetch_items_price(list_of_items_ids)
		if response is None or response.__len__() == 0:
			raise SubscriptionNotFoundException(ERROR.SUBSCRIPTION_NOT_FOUND)
		order_item_dict = {}
		for each_response_item in response[0].get('items')[0].get('items'):
			order_item_dict[int(each_response_item.get('id'))] = each_response_item

		if self.cart_reference_given:
			self.compare_prices_of_items_objects(item_id_to_item_obj_dict, order_item_dict)
		else:
			self.compare_prices_of_items_json(item_id_to_item_json_dict, order_item_dict)

	def compare_prices_of_items_objects(self,item_id_to_item_obj_dict,  order_item_dict):
		for key in item_id_to_item_obj_dict:
			src = order_item_dict.get(key)
			if src is None:
				raise SubscriptionNotFoundException(ERROR.SUBSCRIPTION_NOT_FOUND)
			tar = item_id_to_item_obj_dict.get(key)
			if src.get('basePrice') != tar.display_price:
				raise PriceChangedException(ERROR.PRODUCT_DISPLAY_PRICE_CHANGED)
			if src.get('offerPrice') != tar.offer_price:
				raise PriceChangedException(ERROR.PRODUCT_OFFER_PRICE_CHANGED)
			if (src.get('deliveryDays') == 0 and tar.same_day_delivery == 'NDD') or (src.get('deliveryDays') == 1 and tar.same_day_delivery == 'SDD'):
				tar.same_day_delivery = 'SDD' if src.get('deliveryDays') ==0 else 'NDD'
			if src.get('transferPrice') != tar.transfer_price:
				tar.transfer_price = src.get('transferPrice')


	def compare_prices_of_items_json(self, item_id_to_item_json_dict, order_item_dict):
		for key in item_id_to_item_json_dict:
			src = order_item_dict.get(key)
			if src is None:
				raise SubscriptionNotFoundException(ERROR.SUBSCRIPTION_NOT_FOUND)
			tar = item_id_to_item_json_dict.get(key)
			if src.get('basePrice') != float(tar.get('display_price')):
				raise PriceChangedException(ERROR.PRODUCT_DISPLAY_PRICE_CHANGED)
			if src.get('offerPrice') != float(tar.get('offer_price')):
				raise PriceChangedException(ERROR.PRODUCT_OFFER_PRICE_CHANGED)
			if (src.get('deliveryDays') == 0 and tar.get('same_day_delivery') == False) or (src.get('deliveryDays') == 1 and tar.get('same_day_delivery') == str(True)):
				tar["same_day_delivery"] = 'SDD' if src.get('deliveryDays') == 0 else 'NDD'
			else:
				tar["same_day_delivery"] ='SDD' if tar["same_day_delivery"] == 'True' else 'NDD'
			tar["transfer_price"] = src.get('transferPrice')


	def get_response_from_check_coupons_api(self):
		product_list = list()
		if self.cart_reference_given:
			for key in self.item_id_to_item_obj_dict:
				product = {}
				product["item_id"] = str(key)
				product["quantity"] = self.item_id_to_item_obj_dict[key].quantity
				product["coupon_code"] = self.item_id_to_item_obj_dict[key].promo_codes
				product_list.append(product)
		else:
			for key in self.item_id_to_item_json_dict:
				product = {}
				product["item_id"] = str(key)
				product["quantity"] = self.item_id_to_item_json_dict[key].get('quantity')
				product["coupon_code"] = self.item_id_to_item_json_dict[key].get('promo_codes')
				product_list.append(product)
		req_data = {
			"area_id": str(self.geo_id),
			"customer_id": self.user_id,
			'channel': self.order_source_reference,
			"products": product_list,
			"payment_mode": self.payment_mode
		}
		if self.promo_codes is not None and self.promo_codes != []:
			if self.cart_reference_given:
				req_data["coupon_codes"] = self.promo_codes
			else:
				coupon_codes = map(str, self.promo_codes)
				req_data["coupon_codes"] = coupon_codes

		header = {
			'X-API-USER': current_app.config['X_API_USER'],
			'X-API-TOKEN': current_app.config['X_API_TOKEN'],
			'Content-type': 'application/json'
		}

		response = requests.post(url=current_app.config['COUPON_CHECK_URL'], data=json.dumps(req_data),
								 headers=header)
		json_data = json.loads(response.text)
		Logger.info(
			"[%s] Request to check Coupon data passed is: [%s] and response is: [%s]" % (
				g.UUID, json.dumps(req_data), json_data))
		return json_data

	def compare_discounts_and_freebies(self , response_data):
		if response_data['success']:
			if self.total_discount != float(response_data['totalDiscount']):
				raise DiscountHasChangedException(ERROR.DISCOUNT_CHANGED)

			if self.selected_freebies is not None and self.selected_freebies not in response_data['benefits']:
				raise FreebieNotApplicableException(ERROR.FREEBIE_NOT_ALLOWED)

			item_discount_dict = {}
			for item in response_data['products']:
				item_discount_dict[int(item['itemid'])] = item

			if self.cart_reference_given:
				for key in self.item_id_to_item_obj_dict:
					if self.item_id_to_item_obj_dict[key].item_discount != item_discount_dict[key].get('discount'):
						raise DiscountHasChangedException(ERROR.DISCOUNT_CHANGED)
			else:
				for key in self.item_id_to_item_json_dict:
					if float(self.item_id_to_item_json_dict[key].get('item_discount')) != item_discount_dict[key].get('discount'):
						raise DiscountHasChangedException(ERROR.DISCOUNT_CHANGED)
		else:
			error_msg = response_data['error'].get('error')
			ERROR.COUPON_SERVICE_RETURNING_FAILURE_STATUS.message = error_msg
			raise CouponInvalidException(ERROR.COUPON_SERVICE_RETURNING_FAILURE_STATUS)

	def segregate_order_based_on_ndd_sdd(self):
		if self.cart_reference_given:
			for item_obj in self.item_id_to_item_obj_dict.values():
				if item_obj.same_day_delivery == 'SDD':
					self.sdd_items_dict[item_obj.cart_item_id] = item_obj
				else:
					self.ndd_items_dict[item_obj.cart_item_id] = item_obj
			if self.sdd_items_dict.__len__() == 0 or self.ndd_items_dict.__len__() == 0:
				self.split_order = False
			else:
				self.split_order = True

		else:
			for item_json in self.item_id_to_item_json_dict.values():
				if item_json.get('same_day_delivery') == 'SDD':
					self.sdd_items_dict[item_json['item_uuid']] = item_json
				else:
					self.ndd_items_dict[item_json['item_uuid']] = item_json
			if self.sdd_items_dict.__len__() == 0 or self.ndd_items_dict.__len__() == 0:
				self.split_order = False
			else:
				self.split_order = True


	def create_and_save_order(self):
		if not self.split_order:
			order = Order()
			order.parent_order_id = self.parent_reference_id
			order.order_reference_id = order.parent_order_id

			order_items = self.create_order_items(parent_order_id=order.order_reference_id, sdd_order_id=None, ndd_order_id=None)
			order.orderItem = order_items

			self.create_order(master_order = order, sdd_order = None, ndd_order =None)
			self.order = order
			db.session.add(order)
			db.session.add_all(order_items)
			return order.order_reference_id
		else:
			sdd_order = Order()
			sdd_order.order_reference_id = uuid.uuid1().hex
			sdd_order_items = self.create_order_items(parent_order_id=None, sdd_order_id=sdd_order.order_reference_id, ndd_order_id=None)
			sdd_order.orderItem = sdd_order_items

			ndd_order = Order()
			ndd_order.order_reference_id = uuid.uuid1().hex
			ndd_order_items = self.create_order_items(parent_order_id=None, sdd_order_id=None, ndd_order_id=ndd_order.order_reference_id)
			ndd_order.orderItem = ndd_order_items

			sdd_order.parent_order_id = self.parent_reference_id
			ndd_order.parent_order_id = self.parent_reference_id

			self.create_order(master_order=None, sdd_order = sdd_order, ndd_order = ndd_order)
			self.sdd_order = sdd_order
			self.ndd_order = ndd_order
			all_items = sdd_order_items + ndd_order_items
			db.session.add_all(all_items)
			db.session.add(sdd_order)
			db.session.add(ndd_order)



	def create_order(self, master_order, sdd_order, ndd_order):
		if not self.split_order:
			self.save_common_order_data(master_order)
			self.save_specific_order_data(order=master_order, sdd_order=None, ndd_order=None)
		else:
			self.save_common_order_data(sdd_order)
			self.save_common_order_data(ndd_order)
			self.save_specific_order_data(order=None, sdd_order=sdd_order, ndd_order=ndd_order)

	def save_common_order_data(self, order):
		order.user_id = self.user_id
		order.geo_id = self.geo_id
		order.order_type = self.order_type
		order.order_source_reference = self.order_source_reference
		order.promo_codes = self.promo_codes
		order.delivery_type = self.delivery_type
		order.delivery_slot = self.delivery_slot
		order.status_id = StatusService.get_status_id(ORDER_STATUS.APPROVED_STATUS.value) if self.payment_mode == payment_modes_dict[0] else StatusService.get_status_id(ORDER_STATUS.PENDING_STATUS.value)
		order.total_discount =0.0
		order.total_offer_price =0.0
		order.total_display_price =0.0
		order.total_payble_amount =0.0
		order.total_shipping =0.0
		if self.cart_reference_given:
			order.shipping_address_ref = self.shipping_address
		else:
			shipping_address = self.shipping_address
			address = Address.get_address(shipping_address['name'], shipping_address['mobile'],
										  shipping_address['address'], shipping_address['city'],
										  shipping_address['pincode'], shipping_address['state'],
										  shipping_address.get('email'), shipping_address.get('landmark'))
			order.shipping_address_ref = address.address_hash
		order.billing_address_ref = order.shipping_address_ref
		if self.billing_address is not None:
			billing_address = self.billing_address
			address = Address.get_address(billing_address['name'], billing_address['mobile'],
										  billing_address['address'], billing_address['city'],
										  billing_address['pincode'], billing_address['state'],
										  billing_address.get('email'), billing_address.get('landmark'))
			order.billing_address_ref = address.address_hash


	def save_specific_order_data(self, order, sdd_order, ndd_order):
		if not self.split_order:
			order.freebie = json.dumps(self.selected_freebies) if self.selected_freebies is not None else None
			order.total_discount = self.total_discount
			order.total_display_price = self.total_display_price
			order.total_offer_price = self.total_offer_price
			order.total_shipping = get_shipping_charges(order.total_offer_price, order.total_discount)
			Logger.info("[%s] Total offer price is [%s], Total shipping cost is [%s]" %(g.UUID, order.total_offer_price, order.total_shipping))
			if order.total_shipping != self.total_shipping_charges:
				raise PriceChangedException(ERROR.SHIPPING_CHARGES_CHANGED)
			order.total_payble_amount = self.total_offer_price - self.total_discount + order.total_shipping
		elif sdd_order is not None and ndd_order is not None:
			if self.cart_reference_given:
				for sdd_order_item in self.sdd_items_dict.values():
					sdd_order.total_discount += sdd_order_item.item_discount
					sdd_order.total_display_price += sdd_order_item.display_price * sdd_order_item.quantity
					sdd_order.total_offer_price += sdd_order_item.offer_price * sdd_order_item.quantity
				sdd_order.total_shipping = self.total_shipping_charges
				Logger.info("[%s] SDD Order: Total offer price is [%s], Total shipping cost is [%s]" %(g.UUID, sdd_order.total_offer_price, sdd_order.total_shipping))
				if sdd_order.total_shipping != self.total_shipping_charges:
					raise PriceChangedException(ERROR.SHIPPING_CHARGES_CHANGED)
				sdd_order.total_payble_amount = sdd_order.total_offer_price - sdd_order.total_discount + sdd_order.total_shipping

				for ndd_order_item in self.ndd_items_dict.values():
					ndd_order.total_discount += ndd_order_item.item_discount
					ndd_order.total_display_price += ndd_order_item.display_price * ndd_order_item.quantity
					ndd_order.total_offer_price += ndd_order_item.offer_price * ndd_order_item.quantity
				ndd_order.freebie = json.dumps(self.selected_freebies) if self.selected_freebies is not None else None
				Logger.info("[%s] SDD Order: Total offer price is [%s]" %(g.UUID, ndd_order.total_offer_price))
				ndd_order.total_payble_amount = ndd_order.total_offer_price - ndd_order.total_discount
			else:
				for sdd_order_item in self.sdd_items_dict.values():
					item_discount = float(sdd_order_item["item_discount"]) if sdd_order_item["item_discount"] is not None else 0.0
					display_price = float(sdd_order_item["display_price"]) if sdd_order_item["display_price"] is not None else 0.0
					offer_price = float(sdd_order_item["offer_price"]) if sdd_order_item["offer_price"] is not None else 0.0

					sdd_order.total_discount +=item_discount
					sdd_order.total_display_price += display_price * sdd_order_item["quantity"]
					sdd_order.total_offer_price += offer_price * sdd_order_item["quantity"]

				sdd_order.total_shipping = get_shipping_charges(self.total_offer_price, self.total_discount)
				sdd_order.total_payble_amount = sdd_order.total_offer_price - sdd_order.total_discount + sdd_order.total_shipping

				for ndd_order_item in self.ndd_items_dict.values():
					item_discount = float(ndd_order_item["item_discount"]) if ndd_order_item["item_discount"] is not None else 0.0
					display_price = float(ndd_order_item["display_price"]) if ndd_order_item["display_price"] is not None else 0.0
					offer_price = float(ndd_order_item["offer_price"]) if ndd_order_item["offer_price"] is not None else 0.0

					ndd_order.total_discount += item_discount
					ndd_order.total_display_price += display_price * ndd_order_item["quantity"]
					ndd_order.total_offer_price += offer_price * ndd_order_item["quantity"]
				ndd_order.freebie = json.dumps(self.selected_freebies) if self.selected_freebies is not None else None
				ndd_order.total_payble_amount = ndd_order.total_offer_price - ndd_order.total_discount



	def create_order_items(self, parent_order_id, sdd_order_id, ndd_order_id):
		order_item_list = list()
		if self.cart_reference_given and self.split_order == False:
			self.create_order_item_obj(parent_order_id, self.item_id_to_item_obj_dict, order_item_list)

		elif self.cart_reference_given and self.split_order and sdd_order_id is not None:
			self.create_order_item_obj(sdd_order_id, self.sdd_items_dict, order_item_list)

		elif self.cart_reference_given and self.split_order and ndd_order_id is not None:
			self.create_order_item_obj(ndd_order_id, self.ndd_items_dict, order_item_list)

		elif self.cart_reference_given == False and self.split_order == False:
			self.create_order_item_json(parent_order_id, self.item_id_to_item_json_dict, order_item_list)

		elif self.cart_reference_given == False and self.split_order and sdd_order_id is not None:
			self.create_order_item_json(sdd_order_id, self.sdd_items_dict, order_item_list)

		elif self.cart_reference_given == False and self.split_order and ndd_order_id is not None:
			self.create_order_item_json(ndd_order_id, self.ndd_items_dict, order_item_list)

		return order_item_list


	def create_order_item_obj(self, order_id, src_dict, list_of_items):
		for src_item in src_dict.values():
			order_item = Order_Item()
			order_item.item_id = src_item.cart_item_id
			order_item.quantity = src_item.quantity
			order_item.item_discount = src_item.item_discount
			order_item.offer_price = src_item.offer_price
			order_item.display_price = src_item.display_price
			order_item.transfer_price = src_item.transfer_price

			order_item.order_id = order_id
			list_of_items.append(order_item)

	def create_order_item_json(self, order_id, src_dict, list_of_items):
		for src_item in src_dict.values():
			order_item = Order_Item()
			order_item.item_id = src_item["item_uuid"]
			order_item.quantity = src_item["quantity"]
			order_item.item_discount = float(src_item["item_discount"]) if src_item.get('item_discount') is not None else 0.0
			order_item.offer_price = float(src_item["offer_price"]) if src_item.get('offer_price') is not None else 0.0
			order_item.display_price = float(src_item["display_price"]) if src_item.get('display_price') is not None else 0.0
			order_item.transfer_price = float(src_item.get('transfer_price')) if src_item.get('transfer_price') is not None else 0.0
			order_item.order_id = order_id
			list_of_items.append(order_item)

	def save_payment(self):
		payment = Payment()
		payment.order_id = self.parent_reference_id
		payment.payment_mode = self.payment_mode
		db.session.add(payment)

	def create_publisher_message(self, order):
		data ={}
		data['parent_order_id'] = order.parent_order_id
		data['order_id'] = order.order_reference_id
		data['status_code'] = StatusService.get_status_code(order.status_id)
		data['geo_id'] = order.geo_id
		data['user_id'] = order.user_id
		data['order_type'] = order.order_type
		data['order_source_reference'] = order.order_reference_id
		data['delivery_type'] = order.delivery_type
		data['delivery_slot'] = order.delivery_slot
		data['freebie'] = order.freebie
		data['total_offer_price'] = order.total_offer_price
		data['total_display_price'] = order.total_display_price
		data['total_discount'] = order.total_discount
		data['total_shipping_charges'] = order.total_shipping
		data['total_payble_amount'] = order.total_payble_amount
		data['promo_codes'] = order.promo_codes
		data['created_at'] = order.created_on
		payment = get_payment(order.parent_order_id)
		if payment is not None:
			data['payment_mode'] = payment.payment_mode
		else:
			raise PaymentCanNotBeNullException(ERROR.PAYMENT_CAN_NOT_NULL)
		address = get_address(order.shipping_address_ref)
		if address is None:
			raise NoShippingAddressFoundException(ERROR.NO_SHIPPING_ADDRESS_FOUND)
		data['shipping_address'] =  self.create_address_dict(address)

		if order.shipping_address_ref == order.billing_address_ref:
			data['billing_address'] = data['shipping_address']
		else:
			billing_address = get_address(order.billing_address_ref)
			data['billing_address'] = self.create_address_dict(billing_address)

		order_item_list = list()
		for item in order.orderItem:
			order_item = {}
			order_item['item_id'] = item.item_id
			order_item['quantity'] = item.quantity
			order_item['display_price'] = item.display_price
			order_item['offer_price'] = item.offer_price
			order_item['shipping_charge'] = item.shipping_charge
			order_item['item_discount'] = item.item_discount
			order_item['transfer_price'] = item.transfer_price
			order_item_list.append(order_item)

		data['order_items'] = order_item_list

		publishing_message = {}
		publishing_message['msg_type'] = 'create_order'
		publishing_message['timestamp'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		publishing_message['data'] = data
		print(publishing_message)
		return publishing_message

	def create_address_dict(self, address):
		shipping_address = {}
		shipping_address['name'] = address.name
		shipping_address['mobile'] = address.mobile
		shipping_address['address'] = address.address
		shipping_address['city'] = address.city
		shipping_address['pincode'] = address.pincode
		shipping_address['state'] = address.state
		shipping_address['email'] = address.email
		shipping_address['landmark'] = address.landmark
		return shipping_address

	def apply_coupon(self):
		product_list = list()
		if self.cart_reference_given:
			for key in self.item_id_to_item_obj_dict:
				product = {}
				product["item_id"] = str(key)
				product["quantity"] = self.item_id_to_item_obj_dict[key].quantity
				product_list.append(product)
		else:
			for key in self.item_id_to_item_json_dict:
				product = {}
				product["item_id"] = str(key)
				product["quantity"] = self.item_id_to_item_json_dict[key].get('quantity')
				product_list.append(product)
		req_data = {
			"area_id": str(self.geo_id),
			"customer_id": self.user_id,
			'channel': self.order_source_reference,
			"products": product_list,
			"payment_mode": self.payment_mode,
			"order_id":self.parent_reference_id
		}
		if self.promo_codes is not None and self.promo_codes != []:
			if self.cart_reference_given:
				req_data["coupon_codes"] = self.promo_codes
			else:
				coupon_codes = map(str, self.promo_codes)
				req_data["coupon_codes"] = coupon_codes

		header = {
			'X-API-USER': current_app.config['X_API_USER'],
			'X-API-TOKEN': current_app.config['X_API_TOKEN'],
			'Content-type': 'application/json'
		}

		response = requests.post(url=current_app.config['COUPOUN_APPLY_URL'], data=json.dumps(req_data),
								 headers=header)
		json_data = json.loads(response.text)
		Logger.info(
			"[%s] Request to check Coupon data passed is: [%s] and response is: [%s]" % (
				g.UUID, json.dumps(req_data), json_data))
		if not json_data['success']:
			error_msg = json_data['error'].get('error')
			ERROR.COUPON_APPLY_FAILED.message = error_msg
			raise CouponInvalidException(ERROR.ERROR.COUPON_APPLY_FAILED)







