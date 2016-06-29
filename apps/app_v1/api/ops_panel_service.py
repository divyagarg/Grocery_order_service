
import json
import logging
import requests

from apps.app_v1.api import ERROR, ServiceUnAvailableException

from config import APP_NAME
from flask import current_app, g
import datetime


from apps.app_v1.models.models import Address

__author__ = 'amit.bansal'

Logger = logging.getLogger(APP_NAME)

def format_delivery_slot(delivery_slot):
    if delivery_slot == None:
        return "NNNNNNNN:NN"

    try:
        delivery_slot = json.loads(delivery_slot)

        start = datetime.datetime.strptime(delivery_slot["start_datetime"], "%Y-%m-%dT%H:%M:%S+00:00")
        end = datetime.datetime.strptime(delivery_slot["end_datetime"], "%Y-%m-%dT%H:%M:%S+00:00")

        slot = datetime.datetime.strftime(start, "%Y%m%d%H")[2:10] + datetime.datetime.strftime(end, ":%H")
        return slot
    except Exception as e:
        Logger.error("[%s] Exception occurred in delivery_slot_format : %s", g.UUID, str(e))
        return "NNNNNNNN:NN"


class OpsPanel(object):
    def __init__(self):
        pass

    @staticmethod
    def send_order(data):
        try:
            url = current_app.config['OPS_PANEL_CREATE_ORDER_URL']
            headers = {"Content-type": "application/json"}

            #print(json.dumps(data))
            Logger.info("[%s] Request data for OpsPanel send_order is [%s]", g.UUID, json.dumps(data))

            request = requests.post(url=url, data=json.dumps(data), headers=headers, timeout=current_app.config['API_TIMEOUT'])

            if request.status_code == 200:
                response = json.loads(request.text)
                Logger.info("[%s] Response data for OpsPanel send_order is [%s]", g.UUID, json.dumps(response))
                if response['Success'] == True:
                    return True
                else:
                    #print(response)
                    raise Exception(response['Errors'][0]["errorMsg"])
            else:
                if request.status_code == 404:
                    Logger.error("[%s] OPS Panel service is down", g.UUID)
                    raise ServiceUnAvailableException(ERROR.OPS_PANEL_DOWN)
                else:
                    Logger.error("[%s] Exception occurred in OPS Panel service", g.UUID)
                    raise Exception("could not push order to ops panel")

        except Exception as e:
            raise e


    @staticmethod
    def create_order_request(order_data):
        data = {}
        data["MasterOrderId"] = order_data.parent_reference_id
        data["OrderSource"] =  order_data.order_source_reference
        data["UserID"] = order_data.user_id
        data["CreatedAt"] = str(order_data.master_order.created_on)
        data["GeoId"] =  order_data.geo_id

        data["IBLUID"] =  "0"
        data["IsContracted"] = 0
        data["IsLeader"] = 0
        data["OptIn"] = 1

        shipping_address = Address.find(order_data.shipping_address)
        data["ShippingAddress"] =  {
               "GeoId": order_data.geo_id,
               "PinCode": shipping_address.pincode,
               "Name": shipping_address.name,
               "Mobile": shipping_address.mobile,
               "Address": shipping_address.address,
               "Landmark": shipping_address.landmark
             }

        #print(type(order_data.promo_codes))
        data["CouponUsed"] = [{
                "Code" :  order_data.promo_codes[0],
                "CouponType": "Flat" if order_data.promo_type == 0 else "Percent",
                "CouponMax": order_data.promo_max_discount
            }]

        if order_data.payment_mode == "COD": # 0 -> COD, 1->Prepaid
           data["OrderStatus"] =  "0" # 0 -> Confirmed, 1->Pending
        else:
           data["OrderStatus"] =  "1"

        data["SubOrders"]= list()
        for order in order_data.order_list:
            sub_order = {
                "SubOrderId": order.order_reference_id,
                "TotalItem": len(order.orderItem),
                "TotalDisplayPrice": order.total_display_price,
                "TotalOfferPrice": order.total_offer_price,
                "TotalShippingAmt": order.total_shipping,
                "TotalDiscount": order.total_discount,
                "TotalPayableAmt": order.total_payble_amount,
                "FreebieItems": [] if order.freebie is None else order.freebie,
                "DeliveryType": order.delivery_type,
                "DeliverySlot": format_delivery_slot(order.delivery_slot),
                "CouponMax": order.promo_max_discount
            }

            sub_order['ItemList'] = list()
            for order_item in order.orderItem:
                item_offer_price = (order_item.offer_price * order_item.quantity) + order_item.shipping_charge\
                                   - order_item.item_discount
                item = {
                     "ShippingAmt": order_item.shipping_charge,
                     "DealerPrice": order_item.transfer_price,
                     "CustomerPrice": order_item.offer_price,
                     "MRP": order_item.display_price,
                     "ItemDiscount": order_item.item_discount,
                     "OfferPrice": item_offer_price,
                     "ItemID": order_item.item_id,
                     "Quantity": order_item.quantity,
                     "ProductName": order_item.title,
                     "ItemType": 0
                }

                sub_order['ItemList'].append(item)

            data["SubOrders"].append(sub_order)

        data["PaymentDetails"] = {
            "Status" :  1 if order_data.payment_mode == 0 else 0,  # 1->Confirmed, 0->prepaid pending
            "PaymentModes": [
                {
                    "Mode": 19 if order_data.payment_mode == 0 else 20,  # 19->COD, 20 -> Prepaid
                    "Status": "21",
                    "PGReferenceID": "000",
                    "Amount": order_data.total_payble_amount
                }
            ]
        }

        return data


    @staticmethod
    def update_payment_request(order_data, payment_data):
        data = {}
        data["MasterOrderId"] = order_data.order_id
        data["OrderSource"] =  order_data.order_source
        data["UserID"] = order_data.user_id
        data["CreatedAt"] = str(order_data.created_on)
        data["GeoId"] =  order_data.geo_id

        data["IBLUID"] =  "0"
        data["IsContracted"] = 0
        data["IsLeader"] = 0
        data["OptIn"] = 1

        shipping_address = Address.find(order_data.shipping_address_ref)
        data["ShippingAddress"] =  {
               "GeoId": order_data.geo_id,
               "PinCode": shipping_address.pincode,
               "Name": shipping_address.name,
               "Mobile": shipping_address.mobile,
               "Address": shipping_address.address,
               "Landmark": shipping_address.landmark
             }

        data["CouponUsed"] = [{
                "Code" :  order_data.promo_codes[0],
                "CouponType": "Flat" if order_data.promo_types == 0 else "Percent",
                "CouponMax": order_data.promo_max_discount
            }]


        if order_data.payment_mode == "COD": # 0 -> COD, 1->Prepaid
           data["OrderStatus"] =  "0" # 0 -> Confirmed, 1->Pending
        else:
           data["OrderStatus"] =  "1"

        data["SubOrders"]= list()
        for order in order_data.sub_orders:
            sub_order = {
                "SubOrderId": order.order_reference_id,
                "TotalItem": len(order.orderItem),
                "TotalDisplayPrice": order.total_display_price,
                "TotalOfferPrice": order.total_offer_price,
                "TotalShippingAmt": order.total_shipping,
                "TotalDiscount": order.total_discount,
                "TotalPayableAmt": order.total_payble_amount,
                "FreebieItems": [] if order.freebie is None else order.freebie,
                "DeliveryType": order.delivery_type,
                "DeliverySlot": format_delivery_slot(order.delivery_slot),
                "CouponMax": order.promo_max_discount
            }

            sub_order['ItemList'] = list()
            for order_item in order.orderItem:
                item_offer_price = (order_item.offer_price * order_item.quantity) + order_item.shipping_charge\
                                   - order_item.item_discount
                item = {
                     "ShippingAmt": order_item.shipping_charge,
                     "DealerPrice": order_item.transfer_price,
                     "CustomerPrice": order_item.offer_price,
                     "MRP": order_item.display_price,
                     "ItemDiscount": order_item.item_discount,
                     "OfferPrice": item_offer_price,
                     "ItemID": order_item.item_id,
                     "Quantity": order_item.quantity,
                     "ProductName": order_item.title,
                     "ItemType": 0
                }

                sub_order['ItemList'].append(item)

            data["SubOrders"].append(sub_order)

        data["PaymentDetails"] = {
            "Status" :  1 if payment_data.get('status') == "success" else 0,  # 1->Confirmed, 0->prepaid pending
            "PaymentModes": [
                {
                    "Mode": 20,  # 19->COD, 20 -> Prepaid
                    "Status": "0" if payment_data.get('status') == "success" else "21",
                    "PGReferenceID": payment_data.get('pgTxnId', "000") ,
                    "Amount": payment_data.get('txnAmount', 0.0)
                }
            ]
        }

        return data