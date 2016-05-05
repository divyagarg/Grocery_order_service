from config import VALID_ORDER_TYPES, ORDER_SOURCE_REFERENCES
from utils.jsonutils.json_schema_validator import *

__author__ = 'divyagarg'

"""
{
  "data": {
    "geo_id": 232,
    "user_id": "121212",
    "order_type": "NDD/National/Grocery/Pharma",
    "order_source": "Web/App",
    "order_source_reference": "android/web",
    "promo_codes": [
      "223",
      "113"
    ],
    "orderitems": [
      {
        "quantity": 1,
        "item_uuid": "23",
        "promo_codes": [
          "223",
          "113"
        ]
      },
      {
        "quantity": 1,
        "item_uuid": "23",
        "promo_codes": [
          "223",
          "113"
        ]
      }
    ]
  }
}

"""

CREATE_CART_SCHEMA = {
    "data": {
        FUNCTIONS: [
            {Dictionary: {}}
        ],
        SCHEMA: {
            "geo_id": {
                FUNCTIONS: [
                    {String: {}}
                ]
            },
            "user_id": {
                FUNCTIONS: [
                    {String: {}}
                ]
            },
            "order_type":{
                REQUIRED:False,
                FUNCTIONS:[
                            {Contained : {"contained_in":VALID_ORDER_TYPES}}
                        ]
            },
            "order_source_reference": {
                REQUIRED:False,
                FUNCTIONS: [
                    {Contained : {"contained_in":ORDER_SOURCE_REFERENCES}}
                ]
            },
            "promo_codes": {
                REQUIRED: False,
                FUNCTIONS: [
                    {List: {}}
                ]
            },
            "orderitems": {
                FUNCTIONS: [
                    {List: {}}
                ],
                SCHEMA: {
                    "quantity": {
                        FUNCTIONS: [
                            {Integer: {"min_value": 0}}
                        ]
                    },
                    "item_uuid": {
                        FUNCTIONS: [
                            {String: {}}
                        ]
                    },
                    "promo_codes": {
                        REQUIRED: False,
                        FUNCTIONS: [
                            {List: {}}
                        ]
                    }
                }
            }

        }
    }
}
