from miteD.service.service import rpc_service, rpc_method


@rpc_service(name='test', versions=['2.0'])
class RpcService:
    @rpc_method(versions=['2.0'])
    def ping(self, *args):
        return 'pong 2.0'

    @rpc_method()
    def hello(self, name):
        return 'Hello ' + name

    @rpc_method(name='add')
    def addition(self, x, y):
        print(x)
        return x + y


test = RpcService()
try:
    test.start()
except KeyboardInterrupt:
    test.stop()

