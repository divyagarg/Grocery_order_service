__author__ = 'divyagarg'
from flask import g
import requests, uuid, gevent, logging
from datetime import datetime


Logger = logging.getLogger('orderapi')

class Requests(object):
    method = None
    url = None
    headers = None
    data = None
    params = None
    timeout = 60
    errors=False
    response=None
    jobs = []
    gevent_joined = False
    gevent_started = False

    def __init__(self, url, method, headers=None, data=None, params=None, timeout=60):

        #to keep track of any request
        self.uuid = str(uuid.uuid4())

        if method not in ['GET', 'POST', 'PUT', 'DELETE']:
            self.errors = 'Method Undefined'

        self.url = url
        self.method = method
        self.headers = headers
        self.data = data
        self.params = params
        self.timeout = timeout

    def execute_in_background(self):
        self.gevent_started = True
        job = gevent.spawn(self.gevent_task)
        self.jobs.append(job)

    def gevent_task(self):
            if self.errors == False:
                method_call = requests.get
                if self.method=='POST':
                    method_call = requests.post

                Logger.info('{%s} Hitting URL {%s} with Headers {%s} data {%s} params {%s} timeout {%s}'%(g.UUID, self.url, self.headers, self.data, self.params, self.timeout))
                try:
                    params = {}
                    if self.url:
                        params['url'] = self.url
                    if self.headers:
                        params['headers'] = self.headers
                    if self.data:
                        params['data'] = self.data
                    if self.params:
                        params['params'] = self.params

                    params['timeout']=self.timeout

                    startTime = datetime.now()
                    self.response = method_call(**params)
                    endTime = datetime.now()
                    deltaTime = (endTime - startTime)
                    Logger.info('{%s} API RESPONSE TIME :  URL {%s} Took {%s}.{%s} seconds'%( g.UUID, self.url, deltaTime.seconds, deltaTime.microseconds))
                    Logger.info('{%s} Successfully places with response {%s} and response text {%s} '%(g.UUID, self.response, self.response.text))
                    self.errors = False

                except Exception as e:
                    Logger.error('{%s} Failed with exception'%(g.UUID), exc_info=True)
                    self.errors = str(e)


    def is_successfull(self):

        #if gevent is not yet started start it
        if self.gevent_started == False:
            self.execute_in_background()

        #let gevent to complete the task
        if self.gevent_joined == False:
            gevent.joinall(self.jobs, timeout=self.timeout)
            self.gevent_joined = True

        if self.response != None:
            return True
        else:
            return self.errors

    def get_response(self):

        #if gevent is not yet started start it
        if self.gevent_started == False:
            self.execute_in_background()

        if self.gevent_joined == False:
            gevent.joinall(self.jobs, timeout=self.timeout)
            self.gevent_joined = True

        return self.response

