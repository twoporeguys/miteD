from miteD.middleware.api import api, redirect
from miteD.middleware.methods import get
from miteD.middleware.types import json, text


@api(name='my-api', versions=['1.0', '1.1'])
class MyApi:
    def __init__(self):
        self.service = self.get_remote_service(service_name='test', version='1.1')

    @get(path='/')
    @json
    def root(self, request):
        print(dir(self))
        return 'ROOT'

    @get(path='/foo', versions=['1.0'])
    @json
    def foo(self, request):
        return 'foo'

    @get(path='/foo', versions=['1.1'])
    @json
    def foo_1_1(self, request):
        return 'Foo'

    @get(path='/hello/<name>')
    @json
    def hello_name(self, request, name):
        return 'Hello ' + name

    @get(path='/add/<x:int>/<y:int>', versions=['1.1'])
    @json
    def add(self, request, x, y):
        return x + y, 201

    @get(path='/sub/<x:int>/<y:int>', versions=['1.2'])
    @json
    def sub(self, request, x, y):
        return x - y

    @get('/ping')
    @text
    def ping(self, request):
        return self.service.ping(), 201

    @get('/ping2')
    @json
    def ping2(self, request):
        return self.service.ping()

    @get('/redirect/<foo>/<bar>')
    def redirect(self, request, foo, bar):
        return redirect('http://www.google.com/search?q=' + foo + '%2B' + bar)


test = MyApi()
try:
    test.start()
except KeyboardInterrupt:
    test.stop()
