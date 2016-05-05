__author__ = 'divyagarg'
import unittest
from apps import create_app
from flask import url_for
from test import printTest
import json

api_name = 'app_v1.test'


class TestCartCreationUpdation(unittest.TestCase):
    @classmethod
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()


    @classmethod
    def tearDown(self):
        self.app_context.pop()

    def testabc(self):
        res = self.client.get(url_for(api_name))
        response = json.loads(res.data)
        print(response)





    # def test_add_first_item_to_cart_with_correct_data(self):
    #     data = {
    #         "data": {
    #             "geo_id": "901",
    #             "user_id": "9991",
    #             "order_type": "Grocery",
    #             "order_source_reference": "WEB",
    #             "orderitems": [
    #                 {
    #                     "quantity": 2,
    #                     "item_uuid": "90"
    #                 },
    #                 {
    #                     "quantity": 1,
    #                     "item_uuid": "91"
    #                 }
    #             ]
    #         }
    #     }
    #     headers = {'Content-Type': 'application/json'}
    #     r = self.app.post(url_for(api_name), data=data, headers=headers)
    #     self.assertEqual(r.status_code, 200)
    #     response = json.loads(r.data)
    #     printTest("Create Cart", url_for(api_name, response))
    #     self.assertEqual('success', response['status'])
    #
    #     # url = url_for(api_name)
    #     #
    #     # r = self.app.post(url, data=json.dumps(data), headers=headers)
