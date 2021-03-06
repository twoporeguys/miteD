import logging

from miteD.middleware.api import api, redirect
from miteD.middleware.methods import get
from miteD.middleware.types import json, text


@api(
    name='my-api',
    versions=['1.0', '1.1'],
    broker_urls=['nats://127.0.0.1:4222']
)
class MyApi:
    def __init__(self):
        self.service = self.get_remote_service(service_name='test', version='1.1')

    @get(path='/')
    @json
    def root(self, request):
        return 'ROOT', 200

    @get(path='/foo', versions=['1.0'])
    @json
    def foo(self, request):
        return 'foo', 200

    @get(path='/foo', versions=['1.1'])
    @json
    def foo_1_1(self, request):
        return 'Foo', 200

    @get(path='/hello/<name>')
    @json
    def hello_name(self, request, name):
        return 'Hello ' + name, 200

    @get(path='/add/<x:int>/<y:int>', versions=['1.1'])
    @json
    def add(self, request, x, y):
        return x + y, 200

    @get(path='/sub/<x:int>/<y:int>', versions=['1.2'])
    @json
    def sub(self, request, x, y):
        return x - y, 200

    @get('/ping')
    @text
    def ping(self, request):
        return self.service.ping(), 200

    @get('/ping2')
    @json
    def ping2(self, request):
        return self.service.ping(), 200

    @get('/redirect/<foo>/<bar>')
    def redirect(self, request, foo, bar):
        return redirect('http://www.google.com/search?q=' + foo + '%2B' + bar)

    @get('/not_found')
    @json
    async def not_found(self, request):
        return '', 404

    @get('/not_found2')
    @json
    def not_found2(self, request):
        return '', 404


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)
    test = MyApi()
    try:
        test.start()
    except KeyboardInterrupt:
        test.stop()
