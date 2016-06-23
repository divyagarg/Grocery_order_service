
import json
import logging
import requests

from apps.app_v1.api import ERROR, ServiceUnAvailableException

from config import APP_NAME
from flask import current_app, g


from apps.app_v1.models.models import Address

__author__ = 'amit.bansal'

Logger = logging.getLogger(APP_NAME)


class OpsPanel(object):
    def __init__(self):
        pass

    @staticmethod
    def send_order(data):
        try:
            url = current_app.config['OPS_PANEL_CREATE_ORDER_URL']
            headers = {"Content-type": "application/json"}

            request = requests.post(url=url, data=json.dumps(data), headers=headers, timeout=current_app.config['API_TIMEOUT'])

            if request.status_code == 200:
                response = json.loads(request.text)
                if response['Success'] == True:
                    return True
                else:
                    raise Exception(response['Errors'][0]["errorMsg"])
            else:
                if request.status_code == 404:
                    Logger.error("[%s] OPS Panel service is down", g.UUID)
                    raise ServiceUnAvailableException(ERROR.OPS_PANEL_DOWN)
                else:
                    Logger.error("[%s] Exception occurred in OPS Panel service", g.UUID)
                    raise Exception("could not push order to ops panel")

        except Exception as e:
            Logger.error("[%s] Exception occurred in OPS Panel service", g.UUID)
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

        data["CouponUsed"] = [{
                "Code" :  order_data.promo_codes,
                "CouponType": order_data.promo_type,
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
                "FreebieItems": order.freebie,
                "DeliveryType": order_data.delivery_type,
                "DeliverySlot": order_data.delivery_slot,
                "CouponMax": order_data.promo_max_discount
            }

            sub_order['ItemList'] = list()
            for order_item in order.orderItem:
                item = {
                     "ShippingAmt": order_item.shipping_charge,
                     "DealerPrice": order_item.transfer_price,
                     "CustomerPrice": order_item.offer_price,
                     "MRP": order_item.display_price,
                     "ItemDiscount": order_item.item_discount,
                     "OfferPrice": order_item.offer_price,
                     "ItemID": order_item.item_id,
                     "Quantity": order_item.quantity,
                     "ProductName": order_item.title,
                     "ItemType": 0
                }

                sub_order['ItemList'].append(item)

            data["SubOrders"].append(sub_order)

        data["PaymentDetails"] = {
            "Status" :  1 if order_data.payment_mode == 0 else 0,  # 1->Confirmed, 0->prepaid pending
            "PaymanetModes": [
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
        pass





"""
{
 "MasterOrderId": "GRCY000000489",
 "OrderSource": "2",
 "UserID": "583551",
 "CreatedAt": "2016-06-13 12:25:54.680",
 "GeoId": 57179,
 "IBLUID": "0",
 "IsContracted": 0,
 "IsLeader": 0,
 "OptIn": 1,

 "ShippingAddress": {
   "GeoId": "57179",
   "PinCode": "110014",
   "Name": "App User1",
   "Mobile": "9800000005",
   "Address": "121/5 SIlver Oaks Apartment DLF phase 1",
   "Landmark": "Near Qutub plaza"

 },
 "CouponUsed": [{
    "Code" :  "FLAT1250",
    "CouponType": "Flat",
    "CouponMax": "250.00"
}]
,
 "SubOrders": [
   {
     "SubOrderId": "GRCY010000226",
     "TotalItem": 4,
     "TotalDisplayPrice": 1111.00,
     "TotalOfferPrice": 1053.60,
     "TotalShippingAmt": 0.0,
     "TotalDiscount": 196.33,
     "TotalPayableAmt": 857.27,
     "FreebieItems": [],
     "DeliveryType": 0,
     "DeliverySlot": "2016-06-10 12:25:55.210",
     "CouponMax": "196.33",
     "ItemList": [
       {
         "ShippingAmt": 0.0,
         "DealerPrice": 97.77,
         "CustomerPrice": 102.50,
         "MRP": 109.00,
         "ItemDiscount": 57.30,
         "OfferPrice": 307.50,
         "ItemID": "8063",
         "Quantity": 3,
         "ProductName": "Real Fruit Power Juice - Pomegranate 1 Lt",
         "ItemType": 0
       },
       {
         "ShippingAmt": 0.0,
         "DealerPrice": 156.00,
         "CustomerPrice": 151.05,
         "MRP": 164.00,
         "ItemDiscount": 56.30,
         "OfferPrice": 302.10,
         "ItemID": "556486",
         "Quantity": 2,
         "ProductName": "Pepsi Soft Drink 2 x 2.25 ltr",
         "ItemType": 0
       }
     ]
   },
   {
     "SubOrderId": "GRCY020000227",
     "TotalItem": 2,
     "TotalDisplayPrice": 320,
     "TotalOfferPrice": 288.00,
     "TotalShippingAmt": 0.0,
     "TotalDiscount": 53.67,
     "TotalPayableAmt": 234.33,
     "FreebieItems": [],
     "DeliveryType": 1,
     "DeliverySlot": "2016-06-10 13:25:56.280",
     "CouponMax": "53.67",
     "ItemList": [
       {
         "ShippingAmt": 0.0,
         "DealerPrice": 57.00,
         "CustomerPrice": 54.00,
         "MRP": 60.00,
         "ItemDiscount": 20.14,
         "OfferPrice": 108.00,
         "ItemID": "922635",
         "Quantity": 2,
         "ProductName": "Kurkure Namkeen - Masala Munch 3 x 100 gm",
         "ItemType": 0
       },
       {
         "ShippingAmt": 0.0,
         "DealerPrice": 95.00,
         "CustomerPrice": 90.00,
         "MRP": 100.00,
         "ItemDiscount": 33.54,
         "OfferPrice": 180.00,
         "ItemID": "922654",
         "Quantity": 2,
         "ProductName": "Lays Potato Chips - American Style Cream & Onion Flavour 5 x 52 gm",
         "ItemType": 0
       }
     ]
   }
 ],
 "OrderStatus": "0",
 "PaymentDetails" : {
    "Status" : "1",
    "PaymanetModes": [
	    {
            "Mode": "19",
            "Status": "2",
            "PGReferenceID": "",
            "Amount": 102.5
        }
    ]
 }
}


{
	"errors": [],
	"benefits": [{
		"flat_cashback": 0,
		"flat_discount": 0,
		"couponCode": "freebie_test2",
		"items": [
			"1151594",
			"2007982"
		],
		"paymentMode": [],
		"freebies": [
			[
				1,
				2,
				3
			]
		],
		"prorated_cashback": 0,
		"max_discount": null,
		"prorated_agent_discount": 0,
		"type": 1,
		"channel": [],
		"prorated_discount": 0,
		"prorated_agent_cashback": 0,
		"custom": null,
		"flat_agent_discount": 0,
		"flat_agent_cashback": 0
	}],
	"success": true,
	"totalAgentCashback": 0,
	"totalAgentDiscount": 0,
	"paymentMode": [],
	"totalDiscount": 0,
	"totalCashback": 0,
	"products": [{
		"itemid": "1151594",
		"agent_discount": 0,
		"agent_cashback": 0,
		"discount": 0,
		"cashback": 0,
		"quantity": 3
	}, {
		"itemid": "2007982",
		"agent_discount": 0,
		"agent_cashback": 0,
		"discount": 0,
		"cashback": 0,
		"quantity": 1
	}],
	"channel": [],
	"couponCodes": [
		"freebie_test2"
	]
}
"""



