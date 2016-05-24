__author__ = 'divyagarg'
import unittest
import json

from apps import create_app
from flask import url_for
from test import printTest

test_endpoint_name = 'app_v1.test'
cart_end_point = 'app_v1.createOrUpdateCart'


class TestCartCreationUpdation(unittest.TestCase):
	update_cart_with_payment_mode_shipping_address_data = {
		"data": {
			"geo_id": "29557",
			"user_id": "8088275032",
			"order_type": 0,
			"order_source_reference": 0,
			"payment_mode": 0,
			"shipping_address": {
				"name": "Divya Garg",
				"mobile": "1234567890",
				"email": "divi191@gmail.com",
				"address": "121/5 SIlver Oaks Apartment DLF phase 1",
				"city": "Gurgaon",
				"pincode": "122001",
				"state": "Haryana",
				"landmark": "Near Qutub plaza"
			}
		}
	}

	create_cart_without_payment_mode_with_shipping_address_data = {
		"data": {
			"geo_id": "29557",
			"user_id": "8088275032",
			"order_type": 0,
			"order_source_reference": 0,
			"orderitems": [
				{
					"quantity": 1,
					"item_uuid": "1151594"

				},
				{
					"quantity": 1,
					"item_uuid": "2007982"
				}
			],
			"shipping_address": {
				"name": "Divya Garg",
				"mobile": "1234567890",
				"email": "divi191@gmail.com",
				"address": "121/5 SIlver Oaks Apartment DLF phase 1",
				"city": "Gurgaon",
				"pincode": "122001",
				"state": "Haryana",
				"landmark": "Near Qutub plaza"
			}
		}
	}
	create_cart_without_payment_mode_and_shipping_address_data = {
		"data": {
			"geo_id": "29557",
			"user_id": "8088275032",
			"order_type": 0,
			"order_source_reference": 0,
			"orderitems": [
				{
					"quantity": 1,
					"item_uuid": "1151594"

				},
				{
					"quantity": 1,
					"item_uuid": "2007982"
				}
			]
		}
	}

	update_cart_item_quantity_data = {
		"data": {
			"geo_id": "29557",
			"user_id": "8088275032",
			"order_type": 0,
			"order_source_reference": 0,
			"orderitems": [
				{
					"quantity": 0,
					"item_uuid": "1151594"

				},
				{
					"quantity": 3,
					"item_uuid": "2007982"
				}
			]
		}
	}

	view_cart = {
		"data": {
			"geo_id": "29557",
			"user_id": "8088275032",
			"order_type": 0,
			"order_source_reference": 0

		}
	}

	@classmethod
	def setUp(self):
		app = create_app('testing')
		self.app = app.test_client()

	@classmethod
	def tearDown(self):
		self.app.delete()

	def test_unittest(self):
	    url = url_for(test_endpoint_name)
	    headers = {'Content-Type': 'application/json'}
	    r = self.app.get(url, headers=headers)
	    response = json.loads(r.data)
	    self.assertTrue(response["success"])

	def test_add_first_item_to_cart_with_correct_data(self):
		headers = {'Content-Type': 'application/json'}
		url = url_for(cart_end_point)
		r = self.app.post(url, data=json.dumps(self.create_cart_without_payment_mode_and_shipping_address_data), headers=headers)
		self.assertEqual(r._status_code, 200)
		response = json.loads(r.data)
		printTest("Create Cart", url_for(cart_end_point), response)
		self.assertTrue(response['status'])
		self.assertEquals(response['data']['cart_items_count'], 2)

	def test_view_cart(self):
		headers = {'Content-Type': 'application/json'}
		url = url_for(cart_end_point)
		r = self.app.post(url, data=json.dumps(self.view_cart), headers=headers)
		self.assertEqual(r._status_code, 200)
		response = json.loads(r.data)
		printTest("View Cart", url_for(cart_end_point), response)
		self.assertTrue(response['status'])
		self.assertEquals(response['data']['cart_items_count'], 2)

	def test_update_cart_with_payment_mode_and_shipping_address(self):
		headers = {'Content-Type': 'application/json'}
		url = url_for(cart_end_point)
		r = self.app.post(url, data=json.dumps(self.update_cart_with_payment_mode_shipping_address_data), headers=headers)
		self.assertEqual(r._status_code, 200)
		response = json.loads(r.data)
		printTest("Update Cart payment mode and shipping address", url_for(cart_end_point), response)
		self.assertTrue(response['status'])
		self.assertEquals(response['data']['cart_items_count'], 2)

	# def test_view_cart(self):
	# 	headers = {'Content-Type': 'application/json'}
	# 	url = url_for(cart_end_point)
	# 	r = self.app.post(url, data=json.dumps(self.view_cart), headers=headers)
	# 	self.assertEqual(r._status_code, 200)
	# 	response = json.loads(r.data)
	# 	printTest("View Cart", url_for(cart_end_point), response)
	# 	self.assertTrue(response['status'])
	# 	self.assertEquals(response['data']['cart_items_count'], 2)
	#
	# def test_update_quantity_of_items(self):
	# 	headers = {'Content-Type': 'application/json'}
	# 	url = url_for(cart_end_point)
	# 	r = self.app.post(url, data=json.dumps(self.update_cart_item_quantity_data), headers=headers)
	# 	self.assertEqual(r._status_code, 200)
	# 	response = json.loads(r.data)
	# 	printTest("Update Cart payment mode and shipping address", url_for(cart_end_point), response)
	# 	self.assertTrue(response['status'])
	# 	self.assertEquals(response['data']['cart_items_count'], 1)
	#
	# def test_view_cart(self):
	# 	headers = {'Content-Type': 'application/json'}
	# 	url = url_for(cart_end_point)
	# 	r = self.app.post(url, data=json.dumps(self.view_cart), headers=headers)
	# 	self.assertEqual(r._status_code, 200)
	# 	response = json.loads(r.data)
	# 	printTest("View Cart", url_for(cart_end_point), response)
	# 	self.assertTrue(response['status'])
	# 	self.assertEquals(response['data']['cart_items_count'], 1)