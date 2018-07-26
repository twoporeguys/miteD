from miteD.service.service import rpc_service, rpc_method


@rpc_service(name='test', versions=['2.0'], broker_urls=['nats://127.0.0.1:4222'])
class RpcService:
    @rpc_method(versions=['2.0'])
    async def ping(self, *args):
        return 'pong 2.0'

    @rpc_method()
    async def hello(self, name):
        return 'Hello ' + name

    @rpc_method(name='add')
    async def addition(self, x, y):
        print(x)
        return x + y


test = RpcService()
try:
    test.start()
except KeyboardInterrupt:
    test.stop()

