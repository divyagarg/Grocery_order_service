from apps.app_v1.models import ORDER_SOURCE_REFERENCE, VALID_ORDER_TYPES, PAYMENT_MODE
from utils.jsonutils.json_schema_validator import *

__author__ = 'divyagarg'

CREATE_CART_SCHEMA = {
	"geo_id": {
		FUNCTIONS: [
			{Integer: {}}
		]
	},
	"user_id": {
		FUNCTIONS: [
			{String: {}}
		]
	},
	"order_type": {
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
	"payment_mode": {
		REQUIRED: False,
		FUNCTIONS: [{Contained: {"contained_in": [d.value for d in PAYMENT_MODE]}}]
	},
	"shipping_address": {
		REQUIRED: False,
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
				REQUIRED: False,
				FUNCTIONS: [{String: {}}]
			},
			"pincode": {
				REQUIRED: False,
				FUNCTIONS: [{Pincode: {}}]
			},
			"state": {
				REQUIRED: False,
				FUNCTIONS: [{String: {}}]
			},
			"mobile": {
				FUNCTIONS: [{MobileNumber: {}}]
			},
			"email": {
				REQUIRED: False,
				FUNCTIONS: [{String: {}}]
			},
			"landmark": {
				REQUIRED: False,
				FUNCTIONS: [{String: {}}]
			}
		}},
	"orderitems": {
		REQUIRED: False,
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
	},
	"selected_freebee_code": {
		REQUIRED: False,
		FUNCTIONS: [
			{List: {}}
		],
		SCHEMA: {
			"coupon_code": {
				FUNCTIONS: [
					{String: {}}
				]
			},
			"id": {
				FUNCTIONS: [
					{String: {}}
				]
			},
			"title": {
				FUNCTIONS: [
					{String: {}}
				]
			},
			"image_url": {
				FUNCTIONS: [
					{String: {}}
				]
			}
		}
	}

}


CREATE_ORDER_SCHEMA_WITHOUT_CART_REFERENCE = {
			"shipping_address": {
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
						REQUIRED: False,
						FUNCTIONS: [{String: {}}]
					},
					"pincode": {
						REQUIRED: False,
						FUNCTIONS: [{Pincode: {}}]
					},
					"state": {
						REQUIRED: False,
						FUNCTIONS: [{String: {}}]
					},
					"mobile": {
						FUNCTIONS: [{MobileNumber: {}}]
					},
					"email": {
						REQUIRED: False,
						FUNCTIONS: [{String: {}}]
					},
					"landmark": {
						REQUIRED: False,
						FUNCTIONS: [{String: {}}]
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
					"address": {
						FUNCTIONS: [{String: {}}]
					},
					"city": {
						REQUIRED: False,
						FUNCTIONS: [{String: {}}]
					},
					"pincode": {
						REQUIRED: False,
						FUNCTIONS: [{Pincode: {}}]
					},
					"state": {
						REQUIRED: False,
						FUNCTIONS: [{String: {}}]
					},
					"mobile": {
						FUNCTIONS: [{MobileNumber: {}}]
					},
					"email": {
						REQUIRED: False,
						FUNCTIONS: [{String: {}}]
					},
					"landmark": {
						REQUIRED: False,
						FUNCTIONS: [{String: {}}]
					}
				}
			},
			"payment_mode": {
				REQUIRED: False,
				FUNCTIONS: [	{Contained: {"contained_in": [d.value for d in PAYMENT_MODE]}}]
			},
			"selected_freebee_code": {
				REQUIRED: False,
				FUNCTIONS: [
					{List: {}}
				],
				SCHEMA: {
					"coupon_code": {
						FUNCTIONS: [
							{String: {}}
						]
					},
					"subscription_id": {
						FUNCTIONS: [
							{String: {}}
						]
					}
				}
			},
			"geo_id": {
				FUNCTIONS: [{Integer: {}}]
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
			"total_shipping_charges": {
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
					},
					"item_discount": {
						FUNCTIONS: [{String: {}}]
					}
				}
			}

		}

CREATE_ORDER_SCHEMA_WITH_CART_REFERENCE = {

			"cart_reference_uuid": {
				FUNCTIONS: [
					{String: {}}
				]
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
					"address": {
						FUNCTIONS: [{String: {}}]
					},
					"city": {
						REQUIRED: False,
						FUNCTIONS: [{String: {}}]
					},
					"pincode": {
						REQUIRED: False,
						FUNCTIONS: [{Pincode: {}}]
					},
					"state": {
						REQUIRED: False,
						FUNCTIONS: [{String: {}}]
					},
					"mobile": {
						FUNCTIONS: [{MobileNumber: {}}]
					},
					"email": {
						REQUIRED: False,
						FUNCTIONS: [{String: {}}]
					},
					"landmark": {
						REQUIRED: False,
						FUNCTIONS: [{String: {}}]
					}
				}
			},
			"order_source_reference": {
				FUNCTIONS: [{Contained: {"contained_in": [o.value for o in ORDER_SOURCE_REFERENCE]}}]
			},
			"delivery_slots": {
				REQUIRED: False,
				FUNCTIONS: [
					{List: {}}
				],
				SCHEMA: {
					"shipment_id": {
						FUNCTIONS: [{String: {}}]
					},
					"start_datetime": {
						FUNCTIONS: [
							{String: {}}
						]
					},
					"end_datetime": {
						FUNCTIONS: [
							{String: {}}
						]
					}
				}
			}
		}

GET_COUNT_OF_CART_ITEMS = {
	"data": {
		FUNCTIONS: [
			{Dictionary: {}}
		],
		SCHEMA: {
			"geo_id": {
				FUNCTIONS: [
					{Integer: {}}
				]
			},
			"user_id": {
				FUNCTIONS: [
					{String: {}}
				]
			},
			"order_type": {
				REQUIRED: True,
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
			"orderitems": {
				REQUIRED: False,
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
					}
				}
			}


		}
	}
}

GET_DELIVERY_DETAILS = {
	"geo_id": {
		FUNCTIONS: [
			{Integer: {}}
		]
	},
	"user_id": {
		FUNCTIONS: [
			{String: {}}
		]
	}
}

UPDATE_DELIVERY_SLOT = {
	"delivery_slots": {
		FUNCTIONS: [
			{List: {}}
		],
		SCHEMA: {
			"shipment_id": {
				FUNCTIONS: [{String: {}}]
			},
			"start_datetime": {
				FUNCTIONS: [
					{String: {}}
				]
			},
			"end_datetime": {
				FUNCTIONS: [
					{String: {}}
				]
			}
		}
	}

}
