from miteD.service.service import rpc_service, rpc_method


@rpc_service(name='test', versions=['1.0', '1.1'], broker_urls=['nats://127.0.0.1:4222/'])
class RpcService:
    @rpc_method(versions=['1.0'])
    async def ping(self, *args):
        return 'pong'

    @rpc_method(name='ping', versions=['1.1'])
    async def ping_1_1(self, *args):
        return 'Pong'


test = RpcService()
try:
    test.start()
except KeyboardInterrupt:
    test.stop()
