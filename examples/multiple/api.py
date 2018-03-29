import logging
import os
from miteD.middleware.api import api
from miteD.middleware.methods import get
from miteD.middleware.types import json, text


@api(name='my-api', versions=['1.0'])
class MyApi:
    def __init__(self):
        self.rpc1 = self.get_remote_service(service_name='rpc1', version='1.0')
        self.rpc2 = self.get_remote_service(service_name='rpc2', version='1.0')

    @get('/')
    @json
    def ping(self, request):
        return self.rpc1.ping()

    @get('/bypass')
    @json
    def bypass(self, request):
        return self.rpc2.foo()

    @get('/not_found')
    @json
    def not_found(self, request):
        return self.rpc2.bar()

    @get('/recurse')
    @text
    def recurse(self, request):
        return self.rpc2.recurse()


logging.basicConfig(level=logging.getLevelName(os.getenv('LOG_LEVEL', 'INFO')))
test = MyApi()
try:
    test.start()
except KeyboardInterrupt:
    test.stop()
