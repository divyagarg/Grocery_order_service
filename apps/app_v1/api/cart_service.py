from apps.app_v1.api.api_schema_signature import CREATE_CART_SCHEMA
from apps.app_v1.models.models import Cart, Cart_Item
from utils.api_utils.api_utils import Requests
from utils.jsonutils.output_formatter import create_error_response
from utils.jsonutils.json_schema_validator import validate
from config import APP_NAME, ORDER_SOURCE_REFERENCES
import datetime, logging, json
from flask import g
from apps.app_v1.models.models import db
import config


__author__ = 'divyagarg'

Logger = logging.getLogger(APP_NAME)


class CartService:
    def __init__(self):
        self.cart_reference_uuid = None
        self.geoid = None
        self.userid = None
        self.order_type = None
        self.order_source_reference = ORDER_SOURCE_REFERENCES.WEB
        self.orderitems = None
        self.promocodes = None
        self.items = None
        self.total_price = 0
        self.total_discount = 0
        self.total_display_price = 0
        self.now = datetime.utcnow()

    def createOrUpdateCart(self, body):
        try:
            request_data = self.parse_request_data(body)
            validate(request_data, CREATE_CART_SCHEMA)
            self.userid = request_data['data']['user_id']
            self.geoid = request_data['data']['geo_id']
            self.orderitems = request_data['data']['orderitems']
            self.order_type = request_data['data']['order_type']
            if hasattr(self.cart.request_data['data']['promo_codes'], '__iter__'):
                self.promocodes = request_data['data']['promo_codes']

            if request_data['data']['order_source_reference'] is not None:
                self.order_source_reference = request_data['data']['order_source_reference']
            cart = Cart().query.filter_by(geo_id=self.geoid, user_id = self.userid).first()
            if cart is not None:
                for item in self.orderitems:
                    item_uuid = item['item_uuid']
                    quantity = item['quantity']
                    cart_item = Cart_Item().query.filter_by(cart_item_id = item_uuid).first()
                    if cart_item is not None and quantity == 0:
                        db.session.delete(cart_item)

                    elif cart_item is not None and quantity > 0:
                        cart_item.quantity = quantity
                        cart_item.promo_codes = item['promo_codes']
                        db.session.add(cart_item)

                    db.session.commit()

            self.check_coupons()

        except Exception as e:
            Logger.error('{%s} Exception occured while creating cart {%s}' % (g.UUID, str(e)), exc_info=True)
            return create_error_response(message=str(e))

    def parse_request_data(self, body):
        Logger.info('{%s} Received request to create cart for request {%s}' % (g.UUID, body))
        raw_json_body = body
        json_data = json.loads(raw_json_body)
        Logger.info('{%s} Json encoded content {%s}' % (g.UUID, json_data))
        return json_data

    def check_coupons(self):
        data = {
            "coupoun_codes": self.promocodes,
            "area_id": self.geoid,
            "customer_id": self.userid,
            'channel': self.order_source_reference,
            "products": [
                {"item_id": item['item_uuid'], "quantity": item['quantity'], "coupon_code": item['promo_codes']}
                for item in self.orderitems]
        }
        req = Requests(url=config.DevelopmentConfig.COUPON_CHECK_URL, method='POST', data=json.dumps(data),
                       headers={'Content-type': 'application/json'})
        req.execute_in_background()
        response = req.get_response()
        Logger.info(
            '{%s} Resonse text from url {%s} with data {%s} is {%s}' % (g.UUID, config.DevelopmentConfig.COUPON_CHECK_URL, data, response.text))
        response_data = json.loads(response.text)