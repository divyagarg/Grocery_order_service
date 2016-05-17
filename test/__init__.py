__author__ = 'divyagarg'

import inspect
import json


def printTest(test, url, response):
    printURLandResponse(url, response, testName=test)
    return

def printURLandResponse(url, response, data=None, testName=None):
    file = open("log_json.txt", "a")
    file.write("\n\n***********************************************************************************************\n\n")
    if testName is None:
        testName = inspect.stack()[1][3]
    file.write("TestName = %s \n"% testName)
    file.write("URL = %s\n"%url)
    if data is not None:
        file.write("Body = %s\n"%json.dumps(data, sort_keys=True, indent=4))
    file.write("Response = %s\n"%json.dumps(response, sort_keys=True, indent=4))