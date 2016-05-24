import json
import unittest

from apps import create_app
from flask import url_for
from test import printTest

__author__ = 'divyagarg'

order_end_point ='app_v1.order'

class OrderWithoutCart(unittest.TestCase):

	@classmethod
	def setUp(self):
		app = create_app('testing')
		self.app = app.test_client()

	@classmethod
	def tearDown(self):
		self.app.delete()

	create_order_data_without_cart_reference = {
		"data": {
			"geo_id": 29557,
			"user_id": "8088275032",
			"order_type": 0,
			"order_source_reference": 0,
			"total_display_price": "1075.0",
			"total_offer_price": "1055.0",
			"total_discount": "0.0",
			"total_shipping_charges": "0.0",
			"orderitems": [
				{
					"quantity": 10,
					"item_uuid": "1151594",
					"display_price": "90.0",
					"offer_price": "88.0",
					"item_discount": "0.0",
					"same_day_delivery": "True"
				},
				{
					"quantity": 5,
					"item_uuid": "2007982",
					"display_price": "35.0",
					"offer_price": "35.0",
					"item_discount": "0.0",
					"same_day_delivery": "True"
				}
			],
			"payment_mode": 0,
			"shipping_address": {
				"name": "Divya Garg",
				"mobile": "1234567890",
				"email": "divi191@gmail.com",
				"address": "121/5 SIlver Oaks Apartment",
				"city": "Gurgaon",
				"pincode": "122001",
				"state": "Haryana",
				"landmark": "Near Qutub Plaza"
			},
			"billing_address": {
				"name": "Ravi Jain",
				"mobile": "9742690474",
				"email": "ravi.jain@gmail.com",
				"address": "121/5 SIlver Oaks Apartment",
				"city": "Chittorgarh",
				"pincode": "560036",
				"state": "Rajasthan",
				"landmark": "Near Madhuban"
			},
			"selected_free_bees_code": [{"coupon_code": "CODE123", "subscription_id": "6789"}],
			"delivery_type": 1,
			"delivery_slot": [
				{"sdd_slot": "21-05-2016 09:12"},
				{"ndd_slot": "22-05-1016 15:18"}
			]
		}
	}

	def test_create_order_without_cart_reference(self):
		headers = {'Content-Type': 'application/json'}
		url = url_for(order_end_point)
		r = self.app.post(url, data=json.dumps(self.create_order_data_without_cart_reference), headers=headers)
		self.assertEqual(r._status_code, 200)
		response = json.loads(r.data)
		printTest("Create Order without cart reference", url_for(order_end_point), response)
		self.assertTrue(response['status'])
		# self.assertEquals(response['data']['cart_items_count'], 2)
