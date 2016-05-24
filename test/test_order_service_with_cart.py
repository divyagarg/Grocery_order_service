import json
import unittest

from apps import create_app
from apps.app_v1.api import ERROR
from flask import url_for
from test import printTest

__author__ = 'divyagarg'

order_end_point ='app_v1.order'

class TestOrderService(unittest.TestCase):
	@classmethod
	def setUp(self):
		app = create_app('testing')
		self.app = app.test_client()

	@classmethod
	def tearDown(self):
		self.app.delete()

	create_order_data_with_cart_ref = {
		"data": {
			"cart_reference_uuid": "576fa7f0218311e69a7ef45c899d26fb",
			"billing_address": {
				"name": "Divya Garg",
				"mobile": "1234567890",
				"email": "divi191@gmail.com",
				"address": "121/5 SIlver Oaks Apartment DLF phase 1",
				"city": "Gurgaon",
				"pincode": "122001",
				"state": "Haryana",
				"landmark": "Near Qutub plaza"
			},
			"delivery_type": "NORMAL",
			"order_source_reference": 0
		}
	}

	create_order_data_missing_field = {
		"data": {
			"cart_reference_uuid": "576fa7f0218311e69a7ef45c899d26fb",
			"order_source_reference": 0
		}
	}

	create_order_data_wrong_cart_ref = {
		"data": {
			"cart_reference_uuid": "12345nnlnjnlcwdn",
			"billing_address": {
				"name": "Divya Garg",
				"mobile": "1234567890",
				"email": "divi191@gmail.com",
				"address": "121/5 SIlver Oaks Apartment DLF phase 1",
				"city": "Gurgaon",
				"pincode": "122001",
				"state": "Haryana",
				"landmark": "Near Qutub plaza"
			},
			"delivery_type": "NORMAL",
			"order_source_reference": 0
		}
	}

	create_order_data_wrong_delivery_type = {
		"data": {
			"cart_reference_uuid": "263a055c219111e6a44ff45c899d26fb",
			"delivery_type": "0",
			"order_source_reference": 0
		}
	}


	# def test_create_order_with_cart_reference(self):
	# 	headers = {'Content-Type': 'application/json'}
	# 	url = url_for(order_end_point)
	# 	r = self.app.post(url, data=json.dumps(self.create_order_data_with_cart_ref), headers=headers)
	# 	self.assertEqual(r._status_code, 200)
	# 	response = json.loads(r.data)
	# 	printTest("Create Order without cart reference", url_for(order_end_point), response)
	# 	self.assertTrue(response['status'])
	# 	self.assertIsNotNone(response['data'])

	# def test_create_order_required_field_missing(self):
	# 	headers = {'Content-Type': 'application/json'}
	# 	url = url_for(order_end_point)
	# 	r = self.app.post(url, data=json.dumps(self.create_order_data_missing_field), headers=headers)
	# 	self.assertEqual(r._status_code, 1020)
	# 	print(r.data)
	# 	response = json.loads(r.data)
	# 	printTest("Create Order without cart reference", url_for(order_end_point), response)
	# 	self.assertFalse(response['status'])
	#
	# def test_create_order_cart_does_not_exist(self):
	# 	headers = {'Content-Type': 'application/json'}
	# 	url = url_for(order_end_point)
	# 	r = self.app.post(url, data=json.dumps(self.create_order_data_wrong_cart_ref), headers=headers)
	# 	self.assertEqual(r._status_code, 1024)
	# 	print(r.data)
	# 	response = json.loads(r.data)
	# 	printTest("Create Order without cart reference", url_for(order_end_point), response)
	# 	self.assertFalse(response['status'])
	# 	self.assertEquals(response['error']['message'], ERROR.NO_SUCH_CART_EXIST.message)

	def test_crate_order_wrong_delivery_type_given(self):
		headers = {'Content-Type': 'application/json'}
		url = url_for(order_end_point)
		r = self.app.post(url, data=json.dumps(self.create_order_data_wrong_delivery_type), headers=headers)
		self.assertEqual(r._status_code, 200)
		print(r.data)
		response = json.loads(r.data)
		printTest("Create Order without cart reference", url_for(order_end_point), response)
		self.assertTrue(response['status'])