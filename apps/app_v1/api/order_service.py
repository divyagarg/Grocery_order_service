import json
import logging
import os
import traceback
import datetime

from flask import g, current_app
import requests
from requests.exceptions import ConnectTimeout
from apps.app_v1.api.cart_service import remove_cart, get_cart_for_geo_user_id
from apps.app_v1.api.coupon_service import CouponService
from apps.app_v1.api.delivery_service import DeliveryService, validate_delivery_slot
from apps.app_v1.api.ops_panel_service import OpsPanel
import config
from apps.app_v1.api.api_schema_signature import CREATE_ORDER_SCHEMA_WITH_CART_REFERENCE, \
	CREATE_ORDER_SCHEMA_WITHOUT_CART_REFERENCE
from apps.app_v1.api.status_service import StatusService
from apps.app_v1.models import ORDER_STATUS, DELIVERY_TYPE, order_types, payment_modes_dict
from apps.app_v1.models.models import Order, db, Cart, Address, OrderItem, Status, OrderShipmentDetail, \
	MasterOrder, CartItem
from config import APP_NAME
from sqlalchemy import and_
from utils.jsonutils.json_utility import json_serial
from utils.jsonutils.output_formatter import create_error_response, create_data_response
from apps.app_v1.api import ERROR, parse_request_data, NoSuchCartExistException, SubscriptionNotFoundException, \
	PriceChangedException, RequiredFieldMissing, CouponInvalidException, DiscountHasChangedException, \
	FreebieNotApplicableException, NoShippingAddressFoundException, get_shipping_charges, generate_reference_order_id, \
	PaymentCanNotBeNullException, NoDeliverySlotException, OlderDeliverySlotException, \
	ServiceUnAvailableException, get_address, send_sms
from utils.jsonutils.json_schema_validator import validate

from utils.kafka_utils.kafka_publisher import Publisher


__author__ = 'divyagarg'
Logger = logging.getLogger(APP_NAME)


def get_cart(cart_reference_id):
	return Cart.query.filter_by(cart_reference_uuid=cart_reference_id).first()


def get_delivery_slot(cart_reference_id):
	shipment = OrderShipmentDetail.query.filter_by(cart_id=cart_reference_id).first()
	if shipment is None:
		raise NoDeliverySlotException(ERROR.NO_DELIVERY_SLOT_ERROR)
	if shipment.delivery_slot is None:
		raise NoDeliverySlotException(ERROR.NO_DELIVERY_SLOT_ERROR)
	return validate_delivery_slot(shipment.delivery_slot, 'string')


def get_count_of_orders_of_user(user_id):
	try:
		if user_id is None or not isinstance(user_id, (unicode, str)):
			return create_error_response(ERROR.VALIDATION_ERROR)
		count = MasterOrder.query.filter(MasterOrder.user_id == user_id).filter(MasterOrder.status_id == Status.id).filter(Status.status_code != ORDER_STATUS.CANCELLED.value).count()
	except Exception as exception:
		Logger.error('[%s] Exception occured while fetching data from db [%s]',g.UUID, str(exception), exc_info=True)
		ERROR.INTERNAL_ERROR.message = str(exception)
		return create_error_response(ERROR.INTERNAL_ERROR)

	return create_data_response({"count": count})


def get_order_count_for_today(args):
	try:
		status_code = args.get('status')
		if status_code is None:
			return create_error_response(ERROR.INVALID_STATUS)
		status = Status.query.filter_by(status_code = status_code).first()
		if status is None:
			Logger.error('[%s] Status given is invalid [%s]', g.UUID, status_code)
			return create_error_response(ERROR.INVALID_STATUS)
		filters = []
		filters.append(MasterOrder.status_id == status.id)
		from_date = args.get('from_date')
		if from_date is not None:
			filters.append(MasterOrder.created_on >= from_date)
		to_date = args.get('to_date')
		if to_date is not None:
			filters.append(MasterOrder.created_on <= to_date)
		final_filter = and_(*filters)
		count = MasterOrder.query.filter(final_filter).count()
	except Exception as exception:
		Logger.error('[%s] Exception occured while getting order count [%s]',g.UUID, str(exception), exc_info=True)
		ERROR.INTERNAL_ERROR.message = str(exception)
		return create_error_response(ERROR.INTERNAL_ERROR)

	return create_data_response({"count": count})


def convert_order_to_cod(body):
	try:
		request_data = parse_request_data(body)
		order_id = request_data.get('order_id')
		response = check_if_cod_possible_for_order(order_id= order_id)
		if response.get('status'):
			master_order = MasterOrder.query.filter_by(order_id = order_id).first()
			master_order.payment_mode = payment_modes_dict[0]
			db.session.add(master_order)
			db.session.commit()
			return create_data_response(data= "Converted Order to COD")
		else:
			return response
	except Exception as exception:
		Logger.error('[%s] Exception occured while converting order to COD [%s]',g.UUID, str(exception), exc_info=True)
		ERROR.INTERNAL_ERROR.message = str(exception)
		return create_error_response(ERROR.INTERNAL_ERROR)



def check_if_cod_possible_for_order(order_id):
	try:
		if order_id is None:
			Logger.error("[%s] Order id can not be null", g.UUID)
			return create_error_response(ERROR.VALIDATION_ERROR)
		master_order = MasterOrder.query.filter_by(order_id = order_id).first()
		if master_order is None:
			Logger.error("[%s] Order does not exist for order Id:[%s]", g.UUID, order_id)
			return create_error_response(ERROR.NO_ORDER_FOUND_ERROR)
		if master_order.promo_codes is None:
			return create_data_response({"message": "COD is allowed"})

		orders = Order.query.filter_by(parent_order_id=order_id).all()
		req_data = {}
		if orders.__len__() > 0:
			req_data["area_id"] = str(orders[0].geo_id)
			req_data["customer_id"] = orders[0].user_id
			req_data["channel"] = orders[0].order_source_reference
			req_data["coupon_codes"]= json.loads(orders[0].promo_codes)
			req_data["payment_mode"]= "COD"

			if orders.__len__() == 1:
				req_data["products"] = [
						{"item_id": str(each_order_item.item_id),
						 "subscription_id": str(each_order_item.item_id),
						 "quantity": each_order_item.quantity,
						}
						for each_order_item in orders[0].orderItem]
			elif orders.__len__() > 1:
				product_list = list()
				for each_order in orders:
					for order_item in each_order.orderIten:
						product ={
							"item_id": str(order_item.item_id),
							 "subscription_id": str(order_item.item_id),
							 "quantity": order_item.quantity,
						}
						product_list.append(product)
				req_data["products"] = product_list


			response = CouponService.call_check_coupon_api(req_data)
			if response.status_code == 200:
				return create_data_response({"message": "COD is allowed"})
			elif response.status_code == 400:
				ERROR.PAYMENT_MODE_NOT_ALLOWED.message = "Coupon code is not valid for COD"
				return create_error_response(ERROR.PAYMENT_MODE_NOT_ALLOWED)
	except Exception as exception:
		Logger.error('[%s] Exception occured while checking if cod is possible on order [%s]',g.UUID, str(exception), exc_info=True)
		ERROR.INTERNAL_ERROR.message = str(exception)
		return create_error_response(ERROR.INTERNAL_ERROR)


def compare_prices_of_items_objects(item_id_to_item_obj_dict, order_item_dict):
	for key in item_id_to_item_obj_dict:
		src = order_item_dict.get(key)
		if src is None:
			raise SubscriptionNotFoundException(ERROR.SUBSCRIPTION_NOT_FOUND)
		tar = item_id_to_item_obj_dict.get(key)
		if src.get('basePrice') != tar.display_price:
			raise PriceChangedException(ERROR.PRODUCT_DISPLAY_PRICE_CHANGED)
		if src.get('offerPrice') != tar.offer_price:
			raise PriceChangedException(ERROR.PRODUCT_OFFER_PRICE_CHANGED)
		if (src.get('deliveryDays') == 0 and tar.same_day_delivery == 'NDD') or (
						src.get('deliveryDays') == 1 and tar.same_day_delivery == 'SDD'):
			tar.same_day_delivery = 'SDD' if src.get('deliveryDays') == 0 else 'NDD'
		if src.get('transferPrice') != tar.transfer_price:
			tar.transfer_price = src.get('transferPrice')


def compare_prices_of_items_json(item_id_to_item_json_dict, order_item_dict):
	for key in item_id_to_item_json_dict:
		src = order_item_dict.get(key)
		if src is None:
			raise SubscriptionNotFoundException(ERROR.SUBSCRIPTION_NOT_FOUND)
		tar = item_id_to_item_json_dict.get(key)
		if src.get('basePrice') != float(tar.get('display_price')):
			raise PriceChangedException(ERROR.PRODUCT_DISPLAY_PRICE_CHANGED)
		if src.get('offerPrice') != float(tar.get('offer_price')):
			raise PriceChangedException(ERROR.PRODUCT_OFFER_PRICE_CHANGED)
		if (src.get('deliveryDays') == 0 and tar.get('same_day_delivery') is False) or (
						src.get('deliveryDays') == 1 and tar.get('same_day_delivery') == str(True)):
			tar["same_day_delivery"] = 'SDD' if src.get('deliveryDays') == 0 else 'NDD'
		else:
			tar["same_day_delivery"] = 'SDD' if tar["same_day_delivery"] is 'True' else 'NDD'
		tar["transfer_price"] = src.get('transferPrice')


def create_order_item_obj(order_id, src_list, list_of_items):
	for src_item in src_list:
		order_item = OrderItem()
		order_item.item_id = src_item.cart_item_id
		order_item.quantity = src_item.quantity
		order_item.item_discount = src_item.item_discount
		order_item.item_cashback = src_item.item_cashback
		order_item.offer_price = src_item.offer_price
		order_item.display_price = src_item.display_price
		order_item.transfer_price = src_item.transfer_price
		order_item.title = src_item.title
		order_item.image_url = src_item.image_url
		order_item.seller_id = src_item.seller_id

		order_item.order_id = order_id
		list_of_items.append(order_item)


def create_order_item_json(order_id, src_dict, list_of_items):
	for src_item in src_dict.values():
		order_item = OrderItem()
		order_item.item_id = src_item["item_uuid"]
		order_item.quantity = src_item["quantity"]
		order_item.item_discount = float(src_item["item_discount"]) if src_item.get(
			'item_discount') is not None else 0.0
		order_item.offer_price = float(src_item["offer_price"]) if src_item.get('offer_price') is not None else 0.0
		order_item.display_price = float(src_item["display_price"]) if src_item.get(
			'display_price') is not None else 0.0
		order_item.transfer_price = float(src_item.get('transfer_price')) if src_item.get(
			'transfer_price') is not None else 0.0
		order_item.order_id = order_id
		list_of_items.append(order_item)


def create_address_dict(address):
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


def get_default_slot():
	return None

class OrderService(object):
	def __init__(self):
		self.cart = None
		self.shipment_id_slot_dict = {}
		self.shipment_id_delivery_type_dict = {}
		self.cart_reference_id = None
		self.order_reference_id = None
		self.geo_id = None
		self.user_id = None
		self.order_type = None
		self.order_source_reference = None
		self.promo_codes = None
		self.promo_type = None
		self.promo_max_discount = 0.0
		self.shipping_address = None
		self.billing_address = None
		self.delivery_type = DELIVERY_TYPE.NORMAL.value
		self.delivery_due_date = None
		self.delivery_slot = None
		self.selected_freebies = None
		self.payment_mode = None
		self.order = None

		self.total_offer_price = 0.0
		self.total_shipping_charges = 0.0
		self.total_discount = 0.0
		self.total_cashback = 0.0
		self.total_display_price = 0.0
		self.total_payble_amount = 0.0
		self.order_items = None

		self.item_id_to_item_obj_dict = None
		self.item_id_to_item_json_dict = None

		self.cart_reference_given = None

		self.master_order = None
		self.order_list = list()
		self.split_order = False
		self.parent_reference_id = None
		self.shipment_items_dict = None
		self.apply_coupon_code_list = None

		self.shipment_preview_present = None
		self.shipment_id_to_item_ids_dict = {}
		self.delivery_slot = None
		self.final_order_ids = list()

	def createorder(self, body):
		error = True
		err = None

		while True:

			# 1 Parse request
			request_data = parse_request_data(body)

			self.cart_reference_given = bool("cart_reference_uuid" in request_data) or bool("geo_id" in request_data and "user_id" in request_data)

			# 2. validate request data fields
			try:
				if self.cart_reference_given:
					validate(request_data, CREATE_ORDER_SCHEMA_WITH_CART_REFERENCE)
				else:
					validate(request_data, CREATE_ORDER_SCHEMA_WITHOUT_CART_REFERENCE)
			except RequiredFieldMissing as rfm:
				Logger.error("[%s] Required field is missing [%s]", g.UUID, rfm.message)
				err = rfm
				break
			except Exception as exception:
				Logger.error("[%s] Exception occurred in validating order creation request [%s]", g.UUID, str(exception),
							 exc_info=True)
				ERROR.INTERNAL_ERROR.message = str(exception)
				err = ERROR.INTERNAL_ERROR
				break
			# 3. Initialize order Object
			try:
				if self.cart_reference_given:
					self.initialize_order_from_cart_db_data(request_data)
				else:
					self.initialize_order_with_request_data(request_data)
				self.parent_reference_id = generate_reference_order_id()
			except RequiredFieldMissing as rfm:
				Logger.error("[%s] cart is empty [%s]", g.UUID, rfm.message)
				err = rfm
				break
			except NoSuchCartExistException as ncee:
				Logger.error("[%s] Cart does not Exist [%s]", g.UUID, ncee.message)
				err = ncee
				break
			except PaymentCanNotBeNullException as pe:
				Logger.error("[%s] Please select payment mode before creating Order [%s]", g.UUID, str(pe))
				err = ERROR.PAYMENT_CAN_NOT_NULL
				break
			except Exception as exception:
				Logger.error("[%s] Exception occurred in initializing order [%s]", g.UUID, str(exception), exc_info=True)
				ERROR.INTERNAL_ERROR.message = str(exception)
				err = ERROR.INTERNAL_ERROR
				break
			# 3. calculate and validate price
			try:
				self.calculate_and_validate_prices()
			except SubscriptionNotFoundException:
				Logger.error("[%s] Subscript not found for data [%s]", g.UUID, json.dumps(request_data))
				err = ERROR.SUBSCRIPTION_NOT_FOUND
				break
			except  PriceChangedException as pce:
				Logger.error("[%s] Data was stale, price has changed [%s]", g.UUID, json.dumps(request_data))
				err = pce
				break
			except ServiceUnAvailableException as se:
				Logger.error("[%s] Product catalog API is unavailable", g.UUID)
				err = se
				break
			except ConnectTimeout:
				Logger.error("[%s] Request timeout for product catalog", g.UUID)
				err = ERROR.PRODUCT_API_TIMEOUT
				break
			except Exception as exception:
				Logger.error("[%s] Exception occurred in calculating and validating prices of subscriptions [%s]",
					g.UUID, str(exception), exc_info=True)
				ERROR.INTERNAL_ERROR.message = str(exception)
				err = ERROR.INTERNAL_ERROR
				break

			# 4. check and apply coupons and freebie

			try:
				response_data = self.get_response_from_check_coupons_api()
				self.compare_discounts_and_freebies(response_data)
				if self.apply_coupon_code_list is not None:
					self.apply_coupon()

			except DiscountHasChangedException as dce:
				Logger.error("[%s] Discount has changed  [%s]", g.UUID, str(dce.message))
				err = ERROR.DISCOUNT_CHANGED
				break
			except FreebieNotApplicableException as fnae:
				Logger.error("[%s] Freebie not applicable  [%s]", g.UUID, str(fnae.message))
				err = ERROR.FREEBIE_NOT_ALLOWED
				break
			except CouponInvalidException as cie:
				Logger.error("[%s]Coupon Not valid  [%s]", g.UUID, str(cie.message))
				ERROR.COUPON_SERVICE_RETURNING_FAILURE_STATUS.message = cie.message
				err = ERROR.COUPON_SERVICE_RETURNING_FAILURE_STATUS
				break
			except ServiceUnAvailableException:
				Logger.error("[%s] Coupon service is unavailable", g.UUID)
				err = ERROR.COUPON_SERVICE_DOWN
				break
			except ConnectTimeout:
				Logger.error("[%s] Timeout exception for coupon api", g.UUID)
				err = ERROR.COUPON_API_TIMEOUT
				break
			except Exception as exception:
				Logger.error("[%s] Exception occurred in checking discounts [%s]", g.UUID, str(exception), exc_info=True)
				ERROR.INTERNAL_ERROR.message = str(exception)
				err = ERROR.INTERNAL_ERROR
				break

			# 4.1 calculate shipping charges
			if self.total_shipping_charges != get_shipping_charges(self.total_offer_price, self.total_discount):
				err = ERROR.SHIPPING_CHARGES_CHANGED
				break


			# 5. Segregate order items based on shipments, and add freebies with ndd
			self.segregate_order_based_on_shipments()

			# 6 Create two orders based on ndd and sdd and create a master order id
			try:
				self.create_and_save_order()
			except NoDeliverySlotException as nse:
				Logger.error("[%s] For placing Order Delivery slot is needed [%s]", g.UUID, str(nse))
				err = ERROR.NO_DELIVERY_SLOT_ERROR
				break
			except OlderDeliverySlotException as odse:
				Logger.error("[%s] Older delivery slot found [%s]", g.UUID, str(odse))
				err = ERROR.OLDER_DELIVERY_SLOT_ERROR
				break
			except Exception as exception:
				Logger.error("[%s] Exception occurred in saving order [%s]", g.UUID, str(exception), exc_info=True)
				ERROR.INTERNAL_ERROR.message = str(exception)
				err = ERROR.INTERNAL_ERROR
				break

			# 7 Delete cart of reference id is given
			try:
				if self.cart_reference_given:
					#TODO For Time being not removing cart for payment mode Prepaid
					if self.payment_mode != 'Prepaid':
						remove_cart(self.cart_reference_id)
			except Exception as exception:
				traceback.format_exc()
				Logger.error("[%s] Exception occurred in saving order [%s]", g.UUID, str(exception), exc_info=True)
				ERROR.INTERNAL_ERROR.message = str(exception)
				err = ERROR.INTERNAL_ERROR
				break
			# 8 Order History

			# 9 publish on kafka
			if os.environ.get('HOSTENV') != "production":
				try:
					self.publish_create_order()
				except Exception as exception:
					Logger.error("[%s] Exception occured in publishing kafka message [%s]", g.UUID, str(exception), exc_info = True)
					ERROR.INTERNAL_ERROR.message = str(exception)
					err = ERROR.INTERNAL_ERROR
					break

			# 10 Save in old system
			try:
				if self.payment_mode != "Prepaid":
				   ops_data = OpsPanel.create_order_request(self)
				   OpsPanel.send_order(ops_data)
				   self.master_order.ops_panel_status = 1
			except Exception as e:
				self.master_order.ops_panel_status = 2
				Logger.error("[%s] Exception occured in pusing order to OPS Panel [%s]", g.UUID, str(e), exc_info=True)

			try:
				address = get_address(self.master_order.shipping_address_ref)
				if self.split_order is False:
					sms_body = current_app.config['COD_ORDER_CONFIRMATION_SMS_TEXT_ONE_SHIPMENT']%self.master_order.order_id
				else:
					shipmentIds = []
					for each_order in self.order_list:
						shipmentIds.append(each_order.order_reference_id)
					sms_body = current_app.config['COD_ORDER_CONFIRMATION_SMS_TEXT_TWO_SHIPMENTS']%(shipmentIds[0],shipmentIds[1])
				response = send_sms(address.mobile, sms_body)
				if response.status_code != 200:
					Logger.error('[%s] Sms could not be sent to user [%s]', g.UUID, response.text)
				else:
					Logger.info('[%s] SMS successfully sent to [%s]', g.UUID, address.mobile)
			except Exception:
				Logger.error('[%s] Exception occurred in sending sms', g.UUID, exc_info= True)

			error = False
			break

		if error:
			db.session.rollback()
			return create_error_response(err)
		else:
			try:
				db.session.commit()
				response = {}
				if self.final_order_ids.__len__() == 0:
					response['master_order_id'] = self.parent_reference_id
					response['shipments'] = [{"id": self.parent_reference_id}]
				else:
					response['master_order_id'] = self.parent_reference_id
					response['shipments'] = [{ "id": each_shipment}
											 for each_shipment in self.final_order_ids]


				if self.total_cashback > 0.0:
					response['total_cashback'] = self.total_cashback
					if request_data.get('login_status') == 1:
						response[
							'display_message'] = "Cashback will be credited to your AskmePay Wallet within 24 hours of delivery"
					else:
						response['display_message'] = \
							"Cashback will be credited to your AskmePay Wallet within 24 hours of delivery." \
							" Verify your number to avail cashback."
				else:
					if request_data.get('login_status') == 0:
						response[
							'display_message'] = "To get exciting cash-backs and rewards on your next purchases. Please verify your number"

				return create_data_response(data=response)
			except Exception as exception:
				Logger.error("[%s] Exception occured in committing db changes [%s]", g.UUID, str(exception))
				ERROR.INTERNAL_ERROR.message = str(exception)
				return create_error_response(ERROR.INTERNAL_ERROR)

	def initialize_order_from_cart_db_data(self, data):
		if 'cart_reference_uuid' in data:
			self.cart_reference_id = data['cart_reference_uuid']
			cart = get_cart(self.cart_reference_id)
		elif 'user_id' in data and 'geo_id' in data:
			cart = get_cart_for_geo_user_id(data.get('geo_id'), data.get('user_id'))
			self.cart_reference_id = cart.cart_reference_uuid
		if cart is None:
			raise NoSuchCartExistException(ERROR.NO_SUCH_CART_EXIST)
		self.cart = cart
		self.user_id = cart.user_id
		self.geo_id = cart.geo_id
		self.order_type = cart.order_type
		self.promo_codes = json.loads(cart.promo_codes) if cart.promo_codes is not None else None
		self.selected_freebies = json.loads(
			cart.selected_freebee_items) if cart.selected_freebee_items is not None else None
		self.total_display_price = cart.total_display_price
		self.total_offer_price = cart.total_offer_price
		self.total_shipping_charges = cart.total_shipping_charges
		self.total_discount = cart.total_discount
		self.total_cashback = cart.total_cashback
		if cart.shipping_address_ref is None:
			raise NoShippingAddressFoundException(ERROR.NO_SHIPPING_ADDRESS_FOUND)
		self.shipping_address = cart.shipping_address_ref
		self.payment_mode = cart.payment_mode
		if self.payment_mode is None:
			raise PaymentCanNotBeNullException(ERROR.PAYMENT_CAN_NOT_NULL)
		if cart.cartItem is None:
			raise RequiredFieldMissing(ERROR.CART_EMPTY)
		self.order_items = cart.cartItem
		self.order_source_reference = data['order_source_reference']
		if 'billing_address' in data:
			self.billing_address = data.get('billing_address')
		if 'delivery_slots' in data and data.get('delivery_slots') is not None:
			for each_delivery_slot in data.get('delivery_slots'):
				slot = {}
				slot['start_datetime'] = each_delivery_slot.get('start_datetime')
				slot['end_datetime'] = each_delivery_slot.get('end_datetime')
				self.shipment_id_slot_dict[each_delivery_slot.get('shipment_id')] = json.dumps(slot)

	def initialize_order_with_request_data(self, data):
		self.user_id = data.get('user_id')
		self.geo_id = int(data.get('geo_id'))
		self.order_type = order_types[data.get('order_type')]
		self.order_source_reference = data.get('order_source_reference')
		if 'promo_codes' in data and data.__getitem__('promo_codes').__len__() != 0:
			self.promo_codes = data.get('promo_codes')
			self.promo_codes = json.dumps(map(str, data.get('promo_codes')))
		if data.get('payment_mode') is not None:
			self.payment_mode = payment_modes_dict[data.get('payment_mode')]
		self.total_display_price = float(data.get('total_display_price')) if data.get(
			'total_display_price') is not None else 0.0
		self.total_offer_price = float(data.get('total_offer_price')) if data.get(
			'total_offer_price') is not None else 0.0
		self.total_shipping_charges = float(data.get('total_shipping_charges')) if data.get(
			'total_shipping_charges') is not None else 0.0
		self.total_discount = float(data.get('total_discount')) if data.get('total_discount') is not None else 0.0
		self.order_items = data.get('orderitems')
		self.shipping_address = data.get('shipping_address')
		if 'billing_address' in data:
			self.billing_address = data.get('billing_address')
		self.selected_freebies = data.get('selected_free_bees_code')

	# self.delivery_type = delivery_types[int(data.get('delivery_type'))] if data.get(
	# 	'delivery_type') is not None else None
	# self.delivery_slot = json.dumps(data.get('delivery_slot'))

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
		headers = {'Content-type': 'application/json'}
		Logger.info("[%s] Request data for calculate price while creating order is [%s]", g.UUID, req_data)
		response = requests.post(url=current_app.config['PRODUCT_CATALOGUE_URL'], data=json.dumps(req_data), headers=headers, timeout= current_app.config['API_TIMEOUT'])
		if response.status_code != 200:
			if response.status_code == 404:
				Logger.error("[%s] Catalog search API is down", g.UUID)
				raise ServiceUnAvailableException(ERROR.PRODUCT_CATALOG_SERVICE_DOWN)
			else:
				Logger.error("[%s] Error from product catalog service", g.UUID)
				ERROR.INTERNAL_ERROR.message = "Product catalog return error"
				raise Exception(ERROR.INTERNAL_ERROR)
		json_data = json.loads(response.text)
		Logger.info("[%s] Calculate Price API Request [%s], Response [%s]",
			g.UUID, json.dumps(req_data), json.dumps(json_data))
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
			compare_prices_of_items_objects(item_id_to_item_obj_dict, order_item_dict)
		else:
			compare_prices_of_items_json(item_id_to_item_json_dict, order_item_dict)

	def get_response_from_check_coupons_api(self):
		product_list = list()
		if self.cart_reference_given:
			for key in self.item_id_to_item_obj_dict:
				product = {}
				product["item_id"] = str(key)
				product["subscription_id"] = str(key)
				product["quantity"] = self.item_id_to_item_obj_dict[key].quantity
				product["coupon_code"] = self.item_id_to_item_obj_dict[key].promo_codes
				product_list.append(product)
		else:
			for key in self.item_id_to_item_json_dict:
				product = {}
				product["item_id"] = str(key)
				product["subscription_id"] = str(key)
				product["quantity"] = self.item_id_to_item_json_dict[key].get('quantity')
				product["coupon_code"] = self.item_id_to_item_json_dict[key].get('promo_codes')
				product_list.append(product)
		if product_list.__len__()>0:
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

			response = CouponService.call_check_coupon_api(req_data)
			if response.status_code != 200:
					if response.status_code == 404:
						Logger.error("[%s] Coupon service is temporarily unavailable", g.UUID)
						raise ServiceUnAvailableException(ERROR.COUPON_SERVICE_DOWN)
					elif response.status_code == 400:
						ERROR.INTERNAL_ERROR.message = json.loads(response.text)['errors'][0]
						Logger.error("[%s] Coupon service is returning error", g.UUID, ERROR.INTERNAL_ERROR.message)
						raise CouponInvalidException(ERROR.INTERNAL_ERROR)
			json_data = json.loads(response.text)
			return json_data

	def compare_discounts_and_freebies(self, response_data):
		if response_data['success']:
			if self.total_discount != float(response_data['totalDiscount']):
				Logger.error("[%s] Cart discount is [%s] but now discount is [%s]", g.UUID, self.total_discount, response_data['totalDiscount'])
				raise DiscountHasChangedException(ERROR.DISCOUNT_CHANGED)
			if self.total_cashback != float(response_data['totalCashback']):
				Logger.error("[%s] Cart cashback is [%s] but now cashback is [%s]", g.UUID, self.total_cashback, response_data['totalCashback'])
				raise DiscountHasChangedException(ERROR.DISCOUNT_CHANGED)

			#TODO: Assuming only one coupon is allowed
			if self.promo_codes is not None:
				for each_benefit in response_data['benefits']:
					if each_benefit["couponCode"] == self.promo_codes[0]:
						self.promo_type = each_benefit.get("benefit_type", 0)
						if self.promo_type == 0:
						  self.promo_max_discount = each_benefit.get("amount", 0.0)
						else:
						  self.promo_max_discount = each_benefit.get("max_cap", 0.0)
						break;


			freebie_coupon_code_list = list()
			if self.selected_freebies is not None:

				for each_selected_freebie in self.selected_freebies:
					freebie_coupon_code_list.append(each_selected_freebie.get('coupon_code'))
				benefit_list = list()
				for each_benefit in response_data['benefits']:
					benefit_list.append(each_benefit.get('couponCode'))
				if not all(x in benefit_list for x in freebie_coupon_code_list):
					raise FreebieNotApplicableException(ERROR.FREEBIE_NOT_ALLOWED)
			if freebie_coupon_code_list.__len__() > 0:
				self.apply_coupon_code_list = freebie_coupon_code_list

			if self.promo_codes is not None:
				if self.apply_coupon_code_list is not None:
					self.apply_coupon_code_list = self.apply_coupon_code_list + self.promo_codes
				else:
					self.apply_coupon_code_list = self.promo_codes

			item_discount_dict = {}
			for item in response_data['products']:
				item_discount_dict[int(item['itemid'])] = item

			if self.cart_reference_given:
				for key in self.item_id_to_item_obj_dict:
					if self.item_id_to_item_obj_dict[key].item_discount != item_discount_dict[key].get('discount'):
						raise DiscountHasChangedException(ERROR.DISCOUNT_CHANGED)
					if self.item_id_to_item_obj_dict[key].item_cashback != item_discount_dict[key].get('cashback'):
						raise DiscountHasChangedException(ERROR.DISCOUNT_CHANGED)
			else:
				for key in self.item_id_to_item_json_dict:
					if float(self.item_id_to_item_json_dict[key].get('item_discount')) != item_discount_dict[key].get(
							'discount'):
						raise DiscountHasChangedException(ERROR.DISCOUNT_CHANGED)
		else:
			error_msg = response_data['error'].get('error')
			ERROR.COUPON_SERVICE_RETURNING_FAILURE_STATUS.message = error_msg
			raise CouponInvalidException(ERROR.COUPON_SERVICE_RETURNING_FAILURE_STATUS)

	def segregate_order_based_on_shipments(self):
		order_shipment_details = OrderShipmentDetail.query.filter_by(cart_id=self.cart_reference_id).all()
		if order_shipment_details is None or order_shipment_details.__len__() == 0:
			self.shipment_preview_present = False
			shipment_response = self.get_shipment_preview_for_items()
			shipments_list = shipment_response.get('fulfilment_estimates')[0].get('shipments')
			if shipments_list.__len__() > 1:
				self.split_order = True
				self.create_shipment_item_ids_dict_from_preview_response(shipments_list)
			else:
				self.split_order = False
		elif order_shipment_details.__len__() > 1:
			self.shipment_preview_present = True
			self.split_order = True
			self.create_shipment_item_ids_dict_from_cart(order_shipment_details)
		elif order_shipment_details.__len__() == 1:
			self.shipment_preview_present = True
			self.split_order = False
			self.create_shipment_item_ids_dict_from_cart(order_shipment_details)

	#TODO: This fuction should never called as shipments are always created at cart level
	def create_shipment_item_ids_dict_from_preview_response(self, shipment_list):
		for i in range(shipment_list.__len__()):
			subscription_id_list = list()
			shipment_items = shipment_list[i].get('shipment_items')
			for j in range(shipment_items.__len__()):
				# subscription id will be string here
				subscription_id_list.append(shipment_items[j].get('subscription_id'))

			self.shipment_id_to_item_ids_dict[i] = subscription_id_list
			self.shipment_id_slot_dict[i] = get_default_slot()
			self.shipment_id_delivery_type_dict[i] = 0 if shipment_list[i].get('IS_LAST_MILE_ONLY') is True else 1

	def create_shipment_item_ids_dict_from_cart(self, order_shipment_details):
		slot_present_in_request = True
		if self.shipment_id_slot_dict.values().__len__() == 0:
			slot_present_in_request = False
		for each_row in order_shipment_details:
			self.shipment_id_delivery_type_dict[each_row.shipment_id] = each_row.delivery_type
			if slot_present_in_request is False:
				self.shipment_id_slot_dict[each_row.shipment_id] = each_row.delivery_slot
			subscription_id_list = list()
			items = CartItem.query.filter_by(shipment_id=each_row.shipment_id).all()
			for cart_item_row in items:
				subscription_id_list.append(cart_item_row.cart_item_id)
			self.shipment_id_to_item_ids_dict[each_row.shipment_id] = subscription_id_list

	def save_master_order(self):
		order = MasterOrder()
		order.order_id = self.parent_reference_id
		order.total_discount = self.total_discount
		order.total_cashback = self.total_cashback
		order.total_display_price = self.total_display_price
		order.total_offer_price = self.total_offer_price
		order.total_shipping = self.total_shipping_charges
		order.total_payble_amount = self.total_offer_price - self.total_discount + order.total_shipping

		order.user_id = self.user_id
		order.geo_id = self.geo_id
		order.order_type = self.order_type
		order.order_source = self.order_source_reference
		order.promo_codes = self.promo_codes
		order.promo_types = self.promo_type
		order.promo_max_discount = self.promo_max_discount
		order.payment_mode = self.payment_mode
		order.payment_status = "pending"
		if self.payment_mode == "Prepaid":
			order.status_id = StatusService.get_status_id(ORDER_STATUS.PENDING_STATUS.value)
		else:
			order.status_id = StatusService.get_status_id(ORDER_STATUS.CONFIRMED_STATUS.value)

		if self.cart_reference_given:
			order.shipping_address_ref = self.shipping_address
		else:
			shipping_address = self.shipping_address
			address = Address.get_address(shipping_address['name'], shipping_address['mobile'],
										  shipping_address['address'], shipping_address['city'],
										  shipping_address['pincode'], shipping_address['state'],
										  shipping_address.get('email'), shipping_address.get('landmark'))
			order.shipping_address_ref = address.address_hash

		if self.billing_address is not None:

			billing_address = self.billing_address
			address = Address.get_address(billing_address['name'], billing_address['mobile'],
										  billing_address['address'], billing_address['city'],
										  billing_address['pincode'], billing_address['state'],
										  billing_address.get('email'), billing_address.get('landmark'))
			order.billing_address_ref = address.address_hash
		else:
			order.billing_address_ref = order.shipping_address_ref

		db.session.add(order)
		self.master_order = order

	def create_and_save_order(self):
		self.save_master_order()
		if not self.split_order:
			order = Order()
			order.parent_order_id = self.parent_reference_id
			order.order_reference_id = self.parent_reference_id
			order_item_list = list()
			create_order_item_obj(self.parent_reference_id, self.item_id_to_item_obj_dict.values(),
									   order_item_list)
			order.orderItem = order_item_list

			if self.shipment_id_slot_dict is not None and self.shipment_id_slot_dict.__len__() > 0:
				order.delivery_slot = validate_delivery_slot(self.shipment_id_slot_dict.values()[0], 'string')
				order.delivery_type = self.shipment_id_delivery_type_dict.values()[0]
			else:
				order.delivery_slot = None
			# if self.delivery_slot is not None:
			# 	order.delivery_slot = self.delivery_slot
			self.save_common_order_data(order)
			if self.selected_freebies is not None:
				order.freebie = json.dumps(self.selected_freebies)
			order.total_discount = self.total_discount
			order.promo_max_discount = self.promo_max_discount
			order.total_cashback = self.total_cashback
			order.total_display_price = self.total_display_price
			order.total_offer_price = self.total_offer_price
			order.total_shipping = self.total_shipping_charges
			order.total_payble_amount = self.total_offer_price - self.total_discount + order.total_shipping

			self.order = order
			self.order_list.append(order)
			db.session.add(order)
			db.session.add_all(order_item_list)
			return order.order_reference_id
		elif self.split_order:
			freebee_given = False
			for key in self.shipment_id_to_item_ids_dict:
				sub_order = Order()
				# total cashback was coming as None so intializing with 0
				sub_order.total_cashback = 0.0
				sub_order.parent_order_id = self.parent_reference_id
				sub_order.order_reference_id = generate_reference_order_id()
				self.final_order_ids.append(sub_order.order_reference_id)
				if key in self.shipment_id_slot_dict:
					sub_order.delivery_slot = validate_delivery_slot(self.shipment_id_slot_dict[key], 'string')
					sub_order.delivery_type = self.shipment_id_delivery_type_dict[key]
				else:
					sub_order.delivery_slot = None
					sub_order.delivery_type = 0 # 0 -> SDD

				self.save_common_order_data(sub_order)
				items = db.session.query(CartItem).filter(
					CartItem.cart_item_id.in_(self.shipment_id_to_item_ids_dict[key])).filter(
					CartItem.cart_id == self.cart_reference_id).all()

				order_item_list = list()
				create_order_item_obj(sub_order.order_reference_id, items, order_item_list)
				for each_item in items:
					sub_order.total_discount += each_item.item_discount
					sub_order.total_cashback += each_item.item_cashback
					sub_order.total_display_price += each_item.display_price * each_item.quantity
					sub_order.total_offer_price += each_item.offer_price * each_item.quantity

				sub_order.total_shipping = self.total_shipping_charges / self.shipment_id_to_item_ids_dict.__len__()
				sub_order.total_payble_amount = sub_order.total_offer_price - sub_order.total_discount + sub_order.total_shipping
				# Currently Only one Freebie can be givenon a order, so after freebee is given we are setting freebie_given as True
				if self.selected_freebies is not None and freebee_given is False:
					for freebie in self.selected_freebies:
						shipment_id = freebie.get('shipment_id')
						if shipment_id == key:
							sub_order.freebie = json.dumps(self.selected_freebies)
					freebee_given = True

				sub_order.promo_max_discount = self.promo_max_discount * (sub_order.total_payble_amount/self.master_order.total_payble_amount)

				sub_order.orderItem = order_item_list
				db.session.add(sub_order)
				db.session.add_all(order_item_list)
				self.order_list.append(sub_order)

	def save_common_order_data(self, order):
		order.user_id = self.user_id
		order.geo_id = self.geo_id
		order.order_type = self.order_type
		order.order_source_reference = self.order_source_reference
		order.promo_codes = json.dumps(self.promo_codes)
		order.promo_types = self.promo_type
		order.delivery_slot = order.delivery_slot
		if self.payment_mode == "Prepaid":
			order.status_id = StatusService.get_status_id(ORDER_STATUS.PENDING_STATUS.value)
		else:
			order.status_id = StatusService.get_status_id(ORDER_STATUS.CONFIRMED_STATUS.value)
		order.total_discount = 0.0
		order.total_offer_price = 0.0
		order.total_display_price = 0.0
		order.total_payble_amount = 0.0
		order.total_shipping = 0.0
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

	# def save_specific_order_data(self, order, sdd_order, ndd_order):
	# 	if not self.split_order:
	# 		order.freebie = json.dumps(self.selected_freebies) if self.selected_freebies is not None else None
	# 		order.total_discount = self.total_discount
	# 		order.total_display_price = self.total_display_price
	# 		order.total_offer_price = self.total_offer_price
	# 		order.total_shipping = get_shipping_charges(order.total_offer_price, order.total_discount)
	# 		Logger.info("[%s] Total offer price is [%s], Total shipping cost is [%s]" % (
	# 		g.UUID, order.total_offer_price, order.total_shipping))
	# 		if order.total_shipping != self.total_shipping_charges:
	# 			raise PriceChangedException(ERROR.SHIPPING_CHARGES_CHANGED)
	# 		order.total_payble_amount = self.total_offer_price - self.total_discount + order.total_shipping
	# 	elif sdd_order is not None and ndd_order is not None:
	# 		if self.cart_reference_given:
	# 			for sdd_order_item in self.sdd_items_dict.values():
	# 				sdd_order.total_discount += sdd_order_item.item_discount
	# 				sdd_order.total_display_price += sdd_order_item.display_price * sdd_order_item.quantity
	# 				sdd_order.total_offer_price += sdd_order_item.offer_price * sdd_order_item.quantity
	# 			sdd_order.total_shipping = self.total_shipping_charges
	# 			Logger.info("[%s] SDD Order: Total offer price is [%s], Total shipping cost is [%s]" % (
	# 			g.UUID, sdd_order.total_offer_price, sdd_order.total_shipping))
	# 			if sdd_order.total_shipping != self.total_shipping_charges:
	# 				raise PriceChangedException(ERROR.SHIPPING_CHARGES_CHANGED)
	# 			sdd_order.total_payble_amount = sdd_order.total_offer_price - sdd_order.total_discount + sdd_order.total_shipping
	#
	# 			for ndd_order_item in self.ndd_items_dict.values():
	# 				ndd_order.total_discount += ndd_order_item.item_discount
	# 				ndd_order.total_display_price += ndd_order_item.display_price * ndd_order_item.quantity
	# 				ndd_order.total_offer_price += ndd_order_item.offer_price * ndd_order_item.quantity
	# 			ndd_order.freebie = json.dumps(self.selected_freebies) if self.selected_freebies is not None else None
	# 			Logger.info("[%s] SDD Order: Total offer price is [%s]" % (g.UUID, ndd_order.total_offer_price))
	# 			ndd_order.total_payble_amount = ndd_order.total_offer_price - ndd_order.total_discount
	# 		else:
	# 			for sdd_order_item in self.sdd_items_dict.values():
	# 				item_discount = float(sdd_order_item["item_discount"]) if sdd_order_item[
	# 																			  "item_discount"] is not None else 0.0
	# 				display_price = float(sdd_order_item["display_price"]) if sdd_order_item[
	# 																			  "display_price"] is not None else 0.0
	# 				offer_price = float(sdd_order_item["offer_price"]) if sdd_order_item[
	# 																		  "offer_price"] is not None else 0.0
	#
	# 				sdd_order.total_discount += item_discount
	# 				sdd_order.total_display_price += display_price * sdd_order_item["quantity"]
	# 				sdd_order.total_offer_price += offer_price * sdd_order_item["quantity"]
	#
	# 			sdd_order.total_shipping = get_shipping_charges(self.total_offer_price, self.total_discount)
	# 			sdd_order.total_payble_amount = sdd_order.total_offer_price - sdd_order.total_discount + sdd_order.total_shipping
	#
	# 			for ndd_order_item in self.ndd_items_dict.values():
	# 				item_discount = float(ndd_order_item["item_discount"]) if ndd_order_item[
	# 																			  "item_discount"] is not None else 0.0
	# 				display_price = float(ndd_order_item["display_price"]) if ndd_order_item[
	# 																			  "display_price"] is not None else 0.0
	# 				offer_price = float(ndd_order_item["offer_price"]) if ndd_order_item[
	# 																		  "offer_price"] is not None else 0.0
	#
	# 				ndd_order.total_discount += item_discount
	# 				ndd_order.total_display_price += display_price * ndd_order_item["quantity"]
	# 				ndd_order.total_offer_price += offer_price * ndd_order_item["quantity"]
	# 			ndd_order.freebie = json.dumps(self.selected_freebies) if self.selected_freebies is not None else None
	# 			ndd_order.total_payble_amount = ndd_order.total_offer_price - ndd_order.total_discount

	# def create_order_items(self, parent_order_id, sdd_order_id, ndd_order_id):
	# 	order_item_list = list()
	# 	if self.cart_reference_given and self.split_order == False:
	# 		self.create_order_item_obj(parent_order_id, self.item_id_to_item_obj_dict, order_item_list)
	#
	# 	elif self.cart_reference_given and self.split_order and sdd_order_id is not None:
	# 		self.create_order_item_obj(sdd_order_id, self.sdd_items_dict, order_item_list)
	#
	# 	elif self.cart_reference_given and self.split_order and ndd_order_id is not None:
	# 		self.create_order_item_obj(ndd_order_id, self.ndd_items_dict, order_item_list)
	#
	# 	elif self.cart_reference_given == False and self.split_order == False:
	# 		self.create_order_item_json(parent_order_id, self.item_id_to_item_json_dict, order_item_list)
	#
	# 	elif self.cart_reference_given == False and self.split_order and sdd_order_id is not None:
	# 		self.create_order_item_json(sdd_order_id, self.sdd_items_dict, order_item_list)
	#
	# 	elif self.cart_reference_given == False and self.split_order and ndd_order_id is not None:
	# 		self.create_order_item_json(ndd_order_id, self.ndd_items_dict, order_item_list)
	#
	# 	return order_item_list

	def apply_coupon(self):
		product_list = list()
		if self.cart_reference_given:
			for key in self.item_id_to_item_obj_dict:
				product = {"item_id": str(key), "subscription_id": str(key),
						   "quantity": self.item_id_to_item_obj_dict[key].quantity}
				product_list.append(product)
		else:
			for key in self.item_id_to_item_json_dict:
				product = {"item_id": str(key), "subscription_id": str(key),
						   "quantity": self.item_id_to_item_json_dict[key].get('quantity')}
				product_list.append(product)

		if product_list.__len__() > 0:
			req_data = {
				"area_id": str(self.geo_id),
				"customer_id": self.user_id,
				'channel': self.order_source_reference,
				"products": product_list,
				"payment_mode": self.payment_mode,
				"order_id": self.parent_reference_id
			}
			if self.apply_coupon_code_list is not None and self.apply_coupon_code_list != []:
				if self.cart_reference_given:
					req_data["coupon_codes"] = self.apply_coupon_code_list

				else:
					coupon_codes = map(str, self.promo_codes)
					req_data["coupon_codes"] = coupon_codes

			response = CouponService.apply_coupon(req_data)
			if response.status_code != 200:
					if response.status_code == 404:
						Logger.error("[%s] Coupon service is down", g.UUID)
						raise ServiceUnAvailableException(ERROR.COUPON_SERVICE_DOWN)
					elif response.status_code == 400:
						ERROR.COUPON_APPLY_FAILED.message = json.loads(response.text)['errors'][0]
						Logger.error("[%s] Exception in coupon apply API", g.UUID, ERROR.COUPON_APPLY_FAILED.message)
						raise CouponInvalidException(ERROR.COUPON_APPLY_FAILED)
			json_data = json.loads(response.text)
			if not json_data['success']:
				error_msg = json_data['error'].get('error')
				ERROR.COUPON_APPLY_FAILED.message = error_msg
				raise CouponInvalidException(ERROR.COUPON_APPLY_FAILED)

	def get_shipment_preview_for_items(self):
		request_data = {'geo_id': self.geo_id, 'user_id': self.user_id}
		delivery_service = DeliveryService()
		return delivery_service.get_shipment_preview(request_data)

	def publish_create_order(self):

		message = {}
		message["msg_type"] = "create_order"
		message['timestamp'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		data = {}
		data["master_order_id"] = self.parent_reference_id
		data["order_source"] =  self.order_source_reference
		data["user_id"] = self.user_id
		data["created_at"] = self.master_order.created_on
		data["geo_id"] =  self.geo_id
		data["order_type"] = 0

		data["total_offer_price"] = self.total_offer_price
		data["total_shipping_amount"] = self.total_shipping_charges
		data["total_discount"] = self.total_discount
		data["total_payable_amount"] = self.total_payble_amount
		coupons = list()
		if self.promo_codes is not None:
			for promo_code in self.promo_codes:
				coupon = { "code" : promo_code, "coupon_type": "Flat"}
				coupons.append(coupon)
		data["coupon_used"] = coupons
		data["status"] = StatusService.get_status_code(self.master_order.status_id)
		data["payment_mode"] = self.payment_mode

		data["total_mrp"] = 0

		data["sub_orders"] = list()
		for order in self.order_list:
			sub_order = {}
			sub_order["sub_order_id"] = order.order_reference_id
			sub_order["item_count"] = len(order.orderItem)
			sub_order["total_mrp"] = order.total_display_price
			data["total_mrp"] = data["total_mrp"] + order.total_display_price
			sub_order["total_offer_price"] = order.total_offer_price
			sub_order["total_shipping_amount"] = order.total_shipping
			sub_order["total_discount"] = order.total_discount
			sub_order["status"] = order.status_id
			if order.delivery_slot is not None:
				sub_order["delivery_slot"] = json.loads(order.delivery_slot)
			address = get_address(order.shipping_address_ref)
			sub_order["shipping_address"] = {
				"name":address.name,
				"mobile":address.mobile,
				"address":address.address,
				"city": address.city,
				"pincode": address.pincode,
				"state": address.state
			}
			if address.email is not None:
				sub_order["shipping_address"]["email"] = address.email
			if address.landmark is not None:
				sub_order["shipping_address"]["landmark"] = address.landmark

			sub_order["total_payable_amount"] = order.total_payble_amount
			sub_order["freebies"] = order.freebie
			sub_order["delivery_type"] = 0
			#sub_order["delivery_slot"] = order.delivery_slot
			sub_order['item_list'] = list()
			for order_item in order.orderItem:
				item = {}
				item['shipping_price'] = order_item.shipping_charge
				item['dealer_price'] = order_item.transfer_price
				item['customer_offer_price'] = order_item.offer_price
				item['mrp'] = order_item.display_price
				item['item_discount'] = order_item.item_discount
				item['item_id'] = order_item.item_id
				item['quantity'] = order_item.quantity
				item['product_name'] = order_item.title
				item['image_url'] = order_item.image_url
				item['seller_id'] = order_item.seller_id
				item['final_item_price'] = (order_item.offer_price * order_item.quantity)
				if order_item.shipping_charge is not None:
					item['final_item_price'] = item['final_item_price']  + order_item.shipping_charge
				if order_item.item_discount is not None:
					item['final_item_price'] = item['final_item_price'] - order_item.item_discount
				sub_order['item_list'].append(item)

			data["sub_orders"].append(sub_order)

		message["data"] = data

		Publisher.publish_message(self.parent_reference_id, json.dumps(message, default=json_serial))



