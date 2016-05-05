from apps.app_v1.api.api_schema_signature import CREATE_CART_SCHEMA
from apps.app_v1.models.models import Cart, Cart_Item
from utils.api_utils.api_utils import Requests
from utils.jsonutils.output_formatter import create_error_response, create_data_response
from utils.jsonutils.json_schema_validator import validate
from config import APP_NAME
import datetime, logging, json, uuid, requests
from flask import g
from apps.app_v1.models.models import db
import config
from decimal import Decimal

__author__ = 'divyagarg'

Logger = logging.getLogger(APP_NAME)


def check_if_calculate_price_api_response_is_correct_or_quantity_is_available(item, json_order_item):
    if json_order_item is None:
        Logger.error("{%s} No item is found in calculate price API response for the item {%s}" % (g.UUID, item['item_uuid']),
                     exc_info=True)
        return create_error_response(200, message='Error in calculate price')
    if json_order_item.get('available_quantity') is not None:
        Logger.error(
            "{%s} Item quantity asked for is not available {%s} for the quantity {%s}" % (g.UUID, item['item_uuid'], item[
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
        self.total_price = 0
        self.total_discount = 0
        self.total_display_price = 0
        self.now = datetime.datetime.utcnow()
        self.cart_items = None

    def createOrUpdateCart(self, body):
        try:
            request_data = self.parse_request_data(body)
            validate(request_data, CREATE_CART_SCHEMA)
            self.initialize_cart_with_request(request_data)

            cart = Cart().query.filter_by(geo_id=self.geoid, user_id=self.userid).first()
            if cart is not None:
                Logger.info("{%s}Updating the cart {%s}" %(g.UUID, cart.cart_reference_uuid))
                self.cart_reference_uuid = cart.cart_reference_uuid
                self.total_price = cart.total_offer_price
                self.total_display_price = cart.total_display_price
                return self.update_items_in_cart(cart)
            else:
                cart = Cart()
                self.cart_reference_uuid = uuid.uuid1().hex
                Logger.info("{%s} Creating the cart {%s}" %(g.UUID, self.cart_reference_uuid))
                return self.insert_data_to_new_cart(request_data, cart)
                # self.check_coupons(cart)

        except Exception as e:
            Logger.error('{%s} Exception occured while creating/updating cart {%s}' % (g.UUID, str(e)), exc_info=True)
            return create_error_response(message=str(e))

    def parse_request_data(self, body):
        Logger.info('{%s} Received request to create cart for request {%s}' % (g.UUID, body))
        json_data = json.loads(body)
        Logger.info('{%s} Json encoded content {%s}' % (g.UUID, json_data))
        return json_data

    def remove_cart_item_from_cart(self, cart_item_db):
        self.total_display_price -= Decimal(cart_item_db.display_price)
        self.total_price -= Decimal(cart_item_db.offer_price)
        db.session.delete(cart_item_db)
        db.session.commit()

    def change_quantity_of_cart_item(self, cart_item_db, json_order_item, item):
        cart_item_db.quantity = item['quantity']
        self.total_display_price = self.total_display_price - cart_item_db.display_price
        self.total_price = self.total_price - cart_item_db.offer_price
        # cart_item_db.promo_codes = str(item['promo_codes'])
        cart_item_db.display_price = json_order_item['display_price']
        cart_item_db.offer_price = json_order_item['offer_price']

        self.total_display_price += json_order_item['display_price']
        self.total_price += json_order_item['offer_price']

    def add_new_item_to_cart(self, cart_item_db, json_order_item, item):
        cart_item_db.cart_item_id = item['item_uuid']
        cart_item_db.cart_id = self.cart_reference_uuid
        cart_item_db.quantity = item['quantity']
        cart_item_db.cart_id = self.cart_reference_uuid
        # cart_item_db.promo_codes = str(item['promo_codes'])
        cart_item_db.display_price = json_order_item['display_price']
        cart_item_db.offer_price = json_order_item['offer_price']
        self.total_display_price += json_order_item['display_price']
        self.total_price += json_order_item['offer_price']

    def calculate_item_price(self, item):
        dummy_item_list = list()
        dummy_item_list.append(item)
        response_data = self.fetch_product_price(dummy_item_list)
        order_item_dict = {}
        for response in response_data:
            order_item_dict[response['item_uuid']] = response
        return order_item_dict

    def update_items_in_cart(self, cart):
        cart_items_list = list()
        for item in self.cart_items:
            try:
                cart_item_db = Cart_Item().query.filter_by(cart_item_id=item['item_uuid']).first()
                if cart_item_db is not None and item['quantity'] <= 0:
                    self.remove_cart_item_from_cart(cart_item_db)
                else:
                    order_item_dict = self.calculate_item_price(item)
                    json_order_item = order_item_dict.get(item['item_uuid'])
                    check_if_calculate_price_api_response_is_correct_or_quantity_is_available(item, json_order_item)

                    if cart_item_db is not None and (item['quantity'] != cart_item_db.quantity):
                        self.change_quantity_of_cart_item(cart_item_db, json_order_item, item)

                    elif cart_item_db is None and item['quantity'] > 0:
                        cart_item_db = Cart_Item()
                        self.add_new_item_to_cart(cart_item_db, json_order_item, item)

                    db.session.add(cart_item_db)
                    cart_items_list.append(cart_item_db)
            except Exception as e:
                Logger.error("{%s} Exception occurred in Updating the cart {%s} " %(g.UUID, str(e)), exc_info=True)
                return create_error_response(code=401, message="Exception in udating the Cart")

        # if self.promocodes is not None:
        #     common_promo_codes = set(self.promocodes) & set(cart.promo_codes)
        #     if common_promo_codes != cart.promo_codes:
        #         cart.promo_codes = self.promocodes
        cart.total_display_price = self.total_display_price
        cart.total_offer_price = self.total_price
        try:
            db.session.add(cart)
            response_data = self.get_response(cart_items_list)
            db.session.commit()
            return create_data_response(data=response_data)
        except Exception as e:
            Logger.error("{%s} Error in getting response {%s}" % (g.UUID, str(e)), exc_info=True)
            return create_error_response(code=401, message="Error Occurred")


    def populate_cart_object(self, request_data, cart):
        cart.geo_id = self.geoid
        cart.user_id = self.userid
        cart.cart_reference_uuid = self.cart_reference_uuid
        cart.order_type = request_data['data']['order_type']
        cart.order_source_reference = request_data['data']['order_source_reference']
        # cart.promo_codes = str(self.promocodes)


    def fetch_items_price_return_dict(self, cart_items):
        response_product_fetch_data = self.fetch_product_price(cart_items)
        order_item_dict = {}
        for response in response_product_fetch_data:
            order_item_dict[response['item_uuid']] = response
        return order_item_dict


    def insert_data_to_new_cart(self, request_data, cart):
        self.populate_cart_object(request_data, cart)
        order_item_dict = self.fetch_items_price_return_dict(self.cart_items)

        cart_item_list = list()
        for item in self.cart_items:
            json_order_item = order_item_dict.get(item['item_uuid'])
            check_if_calculate_price_api_response_is_correct_or_quantity_is_available(item, json_order_item)

            cart_item = Cart_Item()
            cart_item.cart_item_id = item['item_uuid']
            cart_item.cart_id = self.cart_reference_uuid
            cart_item.quantity = json_order_item['quantity']
            cart_item.display_price = json_order_item['display_price']
            cart_item.offer_price = json_order_item['offer_price']
            # cart_item.promo_codes = str(item['promo_codes'])

            cart_item_list.append(cart_item)

            self.total_price += json_order_item['offer_price']
            self.total_display_price += json_order_item['display_price']

        self.cart_items = cart_item_list
        cart.total_offer_price = self.total_price
        cart.total_display_price = self.total_display_price

        try:
            db.session.add(cart)
            for cart_item in self.cart_items:
                db.session.add(cart_item)
            response_data = self.get_response(self.cart_items)
            db.session.commit()
            return create_data_response(data=response_data)
        except Exception as e:
            Logger.error("{%s} Exception occurred while insert new items to Cart {%s}" % (g.UUID, str(e)), exc_info=True)
            db.session.rollback()
            return create_error_response(code=500, message='DB Error')


    def check_coupons(self, cart):
        cart_items = Cart_Item().query.filter_by(cart_id=cart.id).all()
        data = {
            "coupoun_codes": self.promocodes,
            "area_id": self.geoid,
            "customer_id": self.userid,
            'channel': self.order_source_reference,
            "products": [
                {"item_id": item.cart_item_id, "quantity": item.quantity, "coupon_code": item.promo_codes}
                for item in cart_items]
        }
        req = Requests(url=config.DevelopmentConfig.COUPON_CHECK_URL, method='POST', data=json.dumps(data),
                       headers={'Content-type': 'application/json'})
        req.execute_in_background()
        response = req.get_response()
        Logger.info(
            '{%s} Resonse text from url {%s} with data {%s} is {%s}' % (
                g.UUID, config.DevelopmentConfig.COUPON_CHECK_URL, data, response.text))
        response_data = json.loads(response.text)

        item_discount_dict = {}
        if response_data['success']:
            self.total_discount = response_data['totalDiscount']
            cart.total_discount = self.total_discount
            db.session.add(cart)
            for item in response_data['products']:
                item_discount_dict[item['item_id']] = item

            for cart_item in cart_items:
                cart_item.item_discount = item_discount_dict[cart_item.cart_item_id]['discount']
                cart_item.order_partial_discount = 0.0

            db.session.add_all(cart_items)
            self.cart_items = cart_items
            db.session.commit()


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
        response = requests.post(url=config.DevelopmentConfig.PRODUCT_CATALOGUE_URL, data=request_data,
                                 headers={'Content-type': 'application/json'})
        json_data = json.loads(response.text)
        Logger.info("{%s} Response got from calculate Price API is {%s}" % (g.UUID, json.dumps(json_data)))
        return json_data['items']


    def get_response(self, cart_items):
        response_json = {
            "orderitems": [],
            "total_offer_price": str(self.total_price),
            "total_display_price": str(self.total_display_price),
            "total_discount": str(self.total_discount),
            "cart_reference_uuid": str(self.cart_reference_uuid)
        }
        items = list()
        for item in cart_items:
            order_item_dict = {}
            order_item_dict["item_uuid"] = item.cart_item_id
            order_item_dict["quantity"] = item.quantity
            order_item_dict["display_price"] = str(item.display_price)
            order_item_dict["offer_price"] = str(item.offer_price)
            items.append(order_item_dict)

        response_json["orderitems"].append(items)

        return response_json


    def initialize_cart_with_request(self, request_data):
        self.geoid = request_data['data']['geo_id']
        self.userid = request_data['data']['user_id']
        self.order_type = request_data['data'].get('order_type')
        if request_data['data'].get('order_source_reference') is not None:
            self.order_source_reference = request_data['data']['order_source_reference']
        # if hasattr(request_data['data'].get('promo_codes'), '__iter__'):
        #     self.promocodes = str(request_data['data']['promo_codes'])
        self.cart_items = request_data['data']['orderitems']



