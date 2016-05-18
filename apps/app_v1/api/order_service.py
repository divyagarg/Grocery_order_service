import logging
from apps.app_v1.models import ORDER_STATUS

from apps.app_v1.models.models import Order
from config import APP_NAME
# from apps.app_v1.api import error_code, error_messages
from flask import g
from utils.jsonutils.output_formatter import create_error_response, create_data_response
from apps.app_v1.api import ERROR

__author__ = 'divyagarg'

Logger = logging.getLogger(APP_NAME)


class OrderService:

	def get_count_of_orders_of_user(self, user_id):
		try:
			if user_id is None or not isinstance(user_id, (unicode, str)):
				return create_error_response(ERROR.VALIDATION_ERROR)
			count = Order.query.filter(Order.user_id == user_id).filter(Order.status_code != ORDER_STATUS.CANCELLED.value).count()
		except Exception as e:
			Logger.error('{%s} Exception occured while fetching data from db {%s}' % (g.UUID, str(e)), exc_info=True)
			ERROR.INTERNAL_ERROR.message = str(e)
			return create_error_response(ERROR.INTERNAL_ERROR)

		return create_data_response({"count": count})


    # def __init__(self):
    #     self.billing_address = None
    #     self.shipping_address = None
    #     self.reference_orderid = None
    #     self.payment_mode = None
    #     self.order_status = ORDER_STATUS.CREATED.value
    #     self.order = None
    #     self.now = datetime.datetime.utcnow()
    #     self.total_offer_price = 0.0
    #     self.total_shipping = 0.0
    #     self.total_discount = 0.0
    #     self.total_display_price = 0.0
    #     self.delivery_charges = 0.0
    #     self.cart_reference_id = None
    #     self.freebies = None
    #     self.delivery_type = DELIVERY_TYPE.NORMAL_DELIVERY.value
    #     self.delivery_date = None
    #     self.delivery_slot_time = None
    #     self.geo_id = None
    #     self.user_id = None
    #     self.promo_codes = None
    #     self.order_type = None
    #     self.order_source_reference = ORDER_SOURCE_REFERENCE.WEB.value
    #     self.order_items = None



    # def createOrder(self, body):
    #     request_data = parse_request_data(body)
    #     is_validated = False
    #     try:
    #         validate(request_data, CREATE_ORDER_SCHEMA_WITH_CART_REFERENCE)
    #         is_validated = True
    #     except Exception as e:
    #         Logger.error("[%s] Exception occurred in validating create order request body with cart reference {%s}" % (
    #             g.UUID, str(e)))
    #         return create_error_response(code=error_code['order_validation_request_error'],
    #                                      message=error_messages['order_validation_request_error'])
	#
    #     if is_validated == False:
    #         try:
    #             validate(request_data, CREATE_ORDER_SCHEMA_WITHOUT_CART_REFERENCE)
    #         except Exception as e:
    #             Logger.error(
    #                 "Exception occurred in validating create order request body without cart reference {%s}" % (
    #                     g.UUID, str(e)))
    #             return create_error_response(code=error_code['order_validation_request_error'],
    #                                          message=error_messages['order_validation_request_error'])
	#
    #     print("Validation Success!!")
    #     self.initialize_order_with_request(request_data)
    #     print ("Initialization Of Order Object Successfull")
    #     try:
    #         self.validate_requested_data()
    #         print("Requested data is Correct!!")
    #     except ConnectionError as c:
    #         raise c
    #     except Exception:
    #         raise Exception
    #     order_id = self.save_order()
    #     # print("Order saved [%s]" %order_id)
    #     response = {}
    #     response["order_id"] = order_id
    #     return create_data_response(response)
	#
    # def initialize_order_with_request(self, request_data):
    #     self.cart_reference_id = request_data['data'].get('cart_reference_uuid')
    #     if self.cart_reference_id is not None:
    #         cart = Cart().query.filter_by(cart_reference_uuid=self.cart_reference_id).first()
    #         self.cart_items = cart.cartItem
    #         self.total_offer_price = cart.total_offer_price
    #         self.total_display_price = cart.total_display_price
    #         self.total_discount = cart.total_discount
    #     else:
    #         self.order_items = request_data['data'].get('orderitems')
    #         self.total_offer_price = request_data['data'].get('total_offer_price')
    #         self.total_display_price = request_data['data'].get('total_display_price')
    #         self.total_discount = request_data['data'].get('total_discount')
	#
    #     self.geo_id = request_data['data'].get('geo_id')
    #     self.user_id = request_data['data'].get('user_id')
    #     self.promo_codes = request_data['data'].get('promo_codes')
    #     self.payment_mode = request_data['data'].get('payment_mode')
    #     self.shipping_address = request_data['data'].get('shipping_address')
    #     self.billing_address = self.shipping_address
    #     if request_data['data'].get('billing_address') is not None:
    #         self.billing_address = request_data['data'].get('billing_address')
    #     self.delivery_type = request_data['data'].get('delivery_type')
    #     self.delivery_date = request_data['data'].get('delivery_date')
    #     self.delivery_slot_time = request_data['data'].get('delivery_slot_time')
    #     self.freebies = request_data['data'].get('freebies')
	#
    # def validate_requested_data(self):
    #     self.validate_coupons()
    #     self.validate_product_price()
	#
    # def validate_discount_if_applicable(self):
    #     if self.promo_codes is not None:
    #         self.create_coupon_request_data()
	#
    # def validate_coupons(self):
    #     product_list = list()
    #     if self.cart_reference_id is not None:
    #         for item in self.cart_items:
    #             cart_item_dist = {}
    #             cart_item_dist["item_id"] = item.cart_item_id
    #             cart_item_dist["quantity"] = item.quantity
    #             cart_item_dist["coupon_code"] = item.promo_codes
    #             product_list.append(cart_item_dist)
    #     else:
    #         for item in self.order_items:
    #             order_item_dist = {}
    #             order_item_dist["item_id"] = item.item_id
    #             order_item_dist["quantity"] = item.quantity
    #             order_item_dist["coupon_code"] = item.promo_codes
    #             product_list.append(order_item_dist)
	#
    #     data = {
    #         "coupoun_codes": self.promo_codes,
    #         "area_id": self.geo_id,
    #         "customer_id": self.user_id,
    #         "channel": self.order_source_reference,
    #         "products": product_list
	#
    #         # "payment_mode": "COD"
    #     }
    #     req = Requests(url=current_app.config['COUPON_CHECK_URL'], method='POST', data=json.dumps(data),
    #                    headers={'Content-type': 'application/json'})
    #     try:
    #         req.execute_in_background()
    #         response = req.get_response()
    #     except ConnectionError as e:
    #         Logger.error("[%s] Not able to Connect to Product catalog URl")
    #         raise e
    #         return create_error_response(code=error_code["connection_error"],
    #                                      message=error_messages["connection_error"])
	#
    #     if response is None:
    #         # raise NetworkError("COUPON CHECK API not responding ")
    #         response_data = {
    #             "status": "success",
    #             "totalDiscount": 0,
    #             "products": [
    #                 {
    #                     "discount": 0,
    #                     "item_id": 23,
    #                     "quantity": 1
    #                 },
    #                 {
    #                     "discount": 0,
    #                     "item_id": 24,
    #                     "quantity": 1
    #                 }
    #             ],
    #             "success": "true",
    #             "paymentMode": [
    #                 "Prepaid"
    #             ],
    #             "channel": "WEB"
    #         }
    #     # Logger.info(
    #     #     '{%s} Resonse text from url {%s} with data {%s} is {%s}' % (
    #     #         g.UUID, current_app.config['COUPON_CHECK_URL'], data, response.text))
    #     # response_data = json.loads(response.text)
    #     if response_data['success']:
    #         tot_discount = response_data['totalDiscount']
    #         if tot_discount != self.total_discount:
    #             Logger.error(
    #                 "[%s] Discount provide by request is [%s] and return by coupon service is [%s] does not match" % (
    #                     g.UUID, self.total_discount, tot_discount))
    #             return create_error_response(code=error_code["discount_changed"],
    #                                          message=error_messages["discount_changed"])
    #         pay_mode = response_data['paymentMode']
    #         if self.payment_mode not in pay_mode:
    #             Logger.error(
    #                 "[%s] Payment mode allowed for this order is [%s] but request payment mode is [%s] does not match" % (
    #                     g.UUID, pay_mode, self.payment_mode))
    #             return create_error_response(code=error_code["payment_mode_not_allowed"],
    #                                          message=error_messages["payment_mode_not_allowed"])
	#
    #         if self.freebies is not None:
    #             if response_data['benefits'] is None:
    #                 Logger.error("[%s] Freebie selected by buyer is [%s] but coupon service didn't give any freebie" % (
    #                     g.UUID, self.freebies))
    #                 return create_error_response(code=error_code["freebie_not_allowed"],
    #                                              message=error_messages["freebie_not_allowed"])
	#
    #             else:
    #                 freebies_list = list()
    #                 for each_benefit in response_data['benefits']:
    #                     freebies_list.append(each_benefit["couponCode"])
    #                 if self.freebies not in freebies_list:
    #                     Logger.error(
    #                         "[%s] Freebie selected by buyer is [%s] and coupon service provided freebies are [%s]" % (
    #                             g.UUID, self.freebies, freebies_list))
    #                     return create_error_response(code=error_code["freebie_not_allowed"],
    #                                                  message=["freebie_not_allowed"])
    #         if self.order_source_reference not in response_data['channel']:
    #             Logger.error("[%s] Order source channel is [%s] but coupon is valid only for these channels [%s]" % (
    #                 g.UUID, self.order_source_reference, response_data['channel']))
    #             return create_error_response(code=error_code["coupon_not_applid_for_channel"],
    #                                          message=error_messages["coupon_not_applid_for_channel"])
    #     else:
    #         Logger.error("Error occured while communicating with coupon service")
    #         return create_error_response(code=error_code['coupon_service_returning_failure_status'],
    #                                      message=error_messages['coupon_service_returning_failure_status'])
	#
    # def validate_product_price(self):
    #     request_items = list()
    #     if self.order_items is None:
    #         for cart_item in self.cart_items:
    #             request_item_detail = {}
    #             request_item_detail["item_uuid"] = cart_item.cart_item_id
    #             request_item_detail["quantity"] = cart_item.quantity
    #             request_items.append(request_item_detail)
    #     else:
    #         for order_item in self.order_items:
    #             request_item_detail = {}
    #             request_item_detail["item_uuid"] = order_item.item_id
    #             request_item_detail["quantity"] = order_item.quantity
    #             request_items.append(request_item_detail)
	#
    #     data = {
    #         "geo_id": self.geo_id,
    #         "items": request_items
    #     }
    #     request_data = json.dumps(data)
    #     Logger.info("{%s} Order API: Request data for calculate price API is {%s}" % (g.UUID, request_data))
    #     req = Requests(url=current_app.config['PRODUCT_CATALOGUE_URL'], method='POST', data=request_data,
    #                    headers={'Content-type': 'application/json'})
    #     try:
    #         req.execute_in_background()
    #         response = req.get_response()
    #         if response is None:
    #             response = {
    #                 "items": [
    #                     {
    #                         "item_uuid": "23",
    #                         "display_price": 200,
    #                         "offer_price": 180,
    #                         "quantity": 1
    #                     },
    #                     {
    #                         "item_uuid": "24",
    #                         "display_price": 200,
    #                         "offer_price": 180,
    #                         "quantity": 1
    #                     }
    #                 ],
    #                 "geo_id": "232"
    #             }
    #             # raise ConnectionError("No response")
    #             json_data = response
    #     except ConnectionError as e:
    #         Logger.error("[%s] Not able to Connect to Product catalog URl [%s]" % (g.UUID, str(e)))
    #         raise ConnectionError
    #     # response = requests.post(url=current_app.config['PRODUCT_CATALOGUE_URL'], data=request_data,
    #     #                          headers={'Content-type': 'application/json'})
	#
    #     # json_data = json.loads(response.text)
    #     Logger.info("{%s} Order API: Response got from calculate Price API is {%s}" % (g.UUID, json.dumps(json_data)))
    #     order_item_dict = {}
    #     tot_offer_price = 0.0
    #     tot_display_price = 0.0
    #     print(json_data)
    #     for response_json in json_data['items']:
    #         print(response_json)
    #         order_item_dict[response_json['item_uuid']] = response_json
    #         tot_offer_price += response_json['offer_price']
    #         tot_display_price += response_json['display_price']
	#
    #     if tot_offer_price != self.total_offer_price:
    #         Logger.error(
    #             "[%s] Total Price passed in request [%s] does not match with the response of calculate price API [%s]" % (
    #                 g.UUID, self.total_offer_price, tot_offer_price))
    #         return create_error_response(code=error_code["product_offer_price_changes"],
    #                                      message=error_messages["product_offer_price_changes"])
    #     elif tot_display_price != self.total_display_price:
    #         Logger.error(
    #             "[%s] Total Display Price passed in request [%s] does not match with the response of calculate price API [%s]" % (
    #                 g.UUID, self.total_display_price, tot_display_price))
    #         return create_error_response(code=error_code["product_display_price_changes"],
    #                                      message=error_messages["product_display_price_changes"])
	#
    #     if self.order_items is not None:
    #         for each_product in self.order_items:
    #             json_order_item = order_item_dict.get(each_product['item_uuid'])
    #             if json_order_item['offer_price'] != each_product['offer_price']:
    #                 Logger.error(
    #                     "[%s] Offer price passed in request [%s] does not match with the response of calculate price api [%s]" % (
    #                         g.UUID, each_product['offer_price'], json_order_item['offer_price']))
    #                 return create_error_response(code=error_code["product_offer_price_changes"],
    #                                              message=error_messages["product_offer_price_changes"])
    #             elif json_order_item['display_price'] != each_product['display_price']:
    #                 Logger.error(
    #                     "[%s] Display price passed in request [%s] does not match with the response of calculate price api [%s]" % (
    #                         g.UUID, each_product['display_price'], json_order_item['display_price']))
    #                 return create_error_response(code=error_code["product_display_price_changes"],
    #                                              message=error_messages["product_display_price_changes"])
    #     else:
    #         for each_product in self.cart_items:
    #             json_order_item = order_item_dict.get(each_product.cart_item_id)
    #             if json_order_item['offer_price'] != each_product.offer_price:
    #                 Logger.error(
    #                     "[%s] Offer price passed in request [%s] does not match with the response of calculate price api [%s]" % (
    #                         g.UUID, each_product.offer_price, json_order_item['offer_price']))
    #                 return create_error_response(code=error_code["product_offer_price_changes"],
    #                                              message=error_messages["product_offer_price_changes"])
    #             elif json_order_item['display_price'] != each_product.display_price:
    #                 Logger.error(
    #                     "[%s] Display price passed in request [%s] does not match with the response of calculate price api [%s]" % (
    #                         g.UUID, each_product.display_price, json_order_item['display_price']))
    #                 return create_error_response(code=error_code["product_display_price_changes"],
    #                                              message=error_messages["product_display_price_changes"])
	#
    #     return
	#
    # def save_order(self):
	#
    #     addr1 = self.shipping_address
    #     shipping_address = Address()
    #     shipping_address.name = addr1["name"]
    #     shipping_address.mobile = addr1["mobile"]
    #     shipping_address.street_1 = addr1["street_1"]
    #     shipping_address.street_2 = addr1["street_2"]
    #     shipping_address.city = addr1["city"]
    #     shipping_address.pincode = addr1["pincode"]
    #     shipping_address.state = addr1["state"]
    #     shipping_address.address_hash = shipping_address.__hash__()
    #     db.session.add(shipping_address)
	#
    #     addr2 = self.billing_address
    #     billing_address = Address.get_address(addr2["name"], addr2["mobile"], addr2["street_1"], addr2["street_2"],
    #                                           addr2["city"], addr2["pincode"], addr2["state"])
    #     db.session.add(billing_address)
	#
    #     order = Order()
    #     order.geo_id = self.geo_id
    #     order.user_id = self.user_id
    #     order.order_reference_id = uuid.uuid4().hex
    #     order.order_type = self.order_type
    #     order.order_source_reference = self.order_source_reference
    #     order.promo_codes = str(self.promo_codes)
    #     order.delivery_type = self.delivery_type
    #     order.delivery_due_date = self.delivery_date
    #     order.delivery_slot = self.delivery_slot_time
    #     order.freebie = self.freebies
    #     order.shipping_address_ref = shipping_address.address_hash
    #     order.billing_address_ref = billing_address.address_hash
    #     db.session.add(order)
	#
    #     payment = Payment()
    #     payment.total_offer_price = self.total_offer_price
    #     payment.total_display_price = self.total_display_price
    #     payment.total_discount = self.total_discount
    #     payment.amount = float(self.total_offer_price) - float(self.total_discount) + float(self.delivery_charges)
    #     payment.payment_mode = self.payment_mode
    #     payment.order_id = order.order_reference_id
    #     db.session.add(payment)
	#
    #     order_items_list = list()
    #     if self.cart_items is not None:
    #         for item in self.cart_items:
    #             print(item)
    #             order_item = Order_Item()
    #             order_item.order_id = order.order_reference_id
    #             order_item.item_id = item.cart_item_id
    #             order_item.quantity = item.quantity
    #             order_item.display_price = item.display_price
    #             order_item.offer_price = item.offer_price
    #             order_item.item_discount = item.item_discount
    #             order_item.order_partial_discount = item.order_partial_discount
    #             order_items_list.append(order_item)
	#
    #     else:
    #         items = self.order_items
    #         no_of_items = items.__len__
    #         item_level_discount = self.total_discount / no_of_items
    #         for item in items:
    #             print(item)
    #             order_item = Order_Item()
    #             order_item.order_id = order.order_reference_id
    #             order_item.item_id = item.item_uuid
    #             order_item.quantity = item.quantity
    #             order_item.display_price = item.display_price
    #             order_item.offer_price = item.order_price
    #             order_item.item_discount = item.discount
    #             order_item.order_partial_discount = item_level_discount
    #             order_items_list.append(order_item)
	#
    #     db.session.add_all(order_items_list)
    #     db.session.commit()
    #     return order.order_reference_id

