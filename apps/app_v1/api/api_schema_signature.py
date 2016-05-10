from apps.app_v1.models import DELIVERY_TYPE, ORDER_SOURCE_REFERENCE, VALID_ORDER_TYPES

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
            "order_type": {
                REQUIRED: False,
                FUNCTIONS: [
                    {Contained: {"contained_in": [d.value for d in VALID_ORDER_TYPES]}}
                ]
            },
            "order_source_reference": {
                REQUIRED: True,
                FUNCTIONS: [
                    {Contained: {"contained_in": [d.value for d in ORDER_SOURCE_REFERENCE]}}
                ]
            },
            "promo_codes": {
                REQUIRED: False,
                FUNCTIONS: [
                    {List: {}}
                ]
            },
            "payment_mode":{
                REQUIRED: False,
                FUNCTIONS: [{String: {}}]
            },
            "shipping_address":{
                REQUIRED : False,
                FUNCTIONS: [
                    {Dictionary: {}}
                ],
                SCHEMA: {
                    "name": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "address": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "city": {
                       FUNCTIONS: [{String: {}}]
                    },
                    "pincode": {
                        FUNCTIONS: [{Pincode: {}}]
                    },
                    "state": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "mobile": {
                        FUNCTIONS: [{MobileNumber: {}}]
                    },
                    "email":{
                        REQUIRED : False,
                        FUNCTIONS: [{String: {}}]
                    },
                    "landmark":{
                        REQUIRED : False,
                        FUNCTIONS: [{String: {}}]
                    }
                }},
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

CREATE_ORDER_SCHEMA_WITHOUT_CART_REFERENCE = {
    "data": {
        FUNCTIONS: [
            {Dictionary: {}}
        ],
        SCHEMA: {
            "shipping_address": {
                FUNCTIONS: [
                    {Dictionary: {}}
                ],
                SCHEMA: {
                    "name": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "street_1": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "street_2": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "city": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "pincode": {
                        FUNCTIONS: [{Pincode: {}}]
                    },
                    "state": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "mobile": {
                        FUNCTIONS: [{MobileNumber: {}}]
                    }
                }
            },

            "billing_address": {
                REQUIRED: False,
                FUNCTIONS: [
                    {Dictionary: {}}
                ],
                SCHEMA: {
                    "name": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "street_1": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "street_2": {
                        REQUIRED: False,
                        FUNCTIONS: [{String: {}}]
                    },
                    "city": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "pincode": {
                        FUNCTIONS: [{Pincode: {}}]
                    },
                    "state": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "mobile": {
                        REQUIRED: False,
                        FUNCTIONS: [{MobileNumber: {}}]
                    }
                }
            },
            "payment_mode": {
                REQUIRED: True,
                FUNCTIONS: [{String: {}}]
            },
            "freebie": {
                REQUIRED: False,
                FUNCTIONS: [
                    {List: {}}
                ],
                SCHEMA: {
                    "id": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "attributes": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "items_id": {
                        FUNCTIONS: [{String: {}}]
                    }
                }
            },
            "delivery_type": {
                FUNCTIONS: [{String: {}, Contained: {"contained_in": [d.value for d in DELIVERY_TYPE]}}]
            },
            "delivery_date": {
                REQUIRED: False,
                FUNCTIONS: [{String: {}}]
            },
            "delivery_slot_time": {
                REQUIRED: False,
                FUNCTIONS: [{String: {}}]
            },
            "geo_id": {
                FUNCTIONS: [{String: {}}]
            },
            "user_id": {
                FUNCTIONS: [{String: {}}]
            },
            "promo_codes": {
                REQUIRED: False,
                FUNCTIONS: [
                    {List: {}}
                ]
            },
            "order_type": {
                FUNCTIONS: [
                   {Contained: {"contained_in": [d.value for d in VALID_ORDER_TYPES]}}
                ]
            },
            "order_source_reference": {
                REQUIRED: False,
                FUNCTIONS: [
                    {Contained: {"contained_in": [d.value for d in ORDER_SOURCE_REFERENCE]}}
                ]
            },
            "total_offer_price": {
                FUNCTIONS: [{String: {}}]
            },
            "total_display_price": {
                FUNCTIONS: [{String: {}}]
            },
            "total_discount": {
                REQUIRED: False,
                FUNCTIONS: [{String: {}}]
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
                    },
                    "display_price": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "offer_price": {
                        FUNCTIONS: [{String: {}}]
                    }
                }
            }

        }
    }
}
CREATE_ORDER_SCHEMA_WITH_CART_REFERENCE = {
    "data": {
        FUNCTIONS: [
            {Dictionary: {}}
        ],
        SCHEMA: {
            "cart_reference_uuid": {
                FUNCTIONS: [
                    {String: {}}
                ]
            },
            "shipping_address": {
                FUNCTIONS: [
                    {Dictionary: {}}
                ],
                SCHEMA: {
                    "name": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "street_1": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "street_2": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "city": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "pincode": {
                        FUNCTIONS: [{Pincode: {}}]
                    },
                    "state": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "mobile": {
                        FUNCTIONS: [{MobileNumber: {}}]
                    }
                }
            },

            "billing_address": {
                REQUIRED: False,
                FUNCTIONS: [
                    {Dictionary: {}}
                ],
                SCHEMA: {
                    "name": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "street_1": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "street_2": {
                        REQUIRED: False,
                        FUNCTIONS: [{String: {}}]
                    },
                    "city": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "pincode": {
                        FUNCTIONS: [{Pincode: {}}]
                    },
                    "state": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "mobile": {
                        REQUIRED: False,
                        FUNCTIONS: [{MobileNumber: {}}]
                    }
                }
            },
            "payment_mode": {
                REQUIRED: True,
                FUNCTIONS: [{String: {}}]
            },
            "freebie": {
                REQUIRED: False,
                FUNCTIONS: [
                    {List: {}}
                ],
                SCHEMA: {
                    "id": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "attributes": {
                        FUNCTIONS: [{String: {}}]
                    },
                    "items_id": {
                        FUNCTIONS: [{String: {}}]
                    }
                }
            },
            "delivery_type": {
                FUNCTIONS: [{String: {}, Contained: {"contained_in": [d.value for d in DELIVERY_TYPE]}}]
            },
            "delivery_date": {
                REQUIRED: False,
                FUNCTIONS: [{String: {}}]
            },
            "delivery_slot_time": {
                REQUIRED: False,
                FUNCTIONS: [{String: {}}]
            },
            "order_source_reference": {
                REQUIRED : True,
                FUNCTIONS: [{ Contained: {"contained_in": [o.value for o in ORDER_SOURCE_REFERENCE]}}]
            }
        }
    }
}
