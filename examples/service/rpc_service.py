from miteD.service.service import rpc_service, rpc_method


@rpc_service(name='test', versions=['1.0', '1.1'])
class RpcService:
    @rpc_method(versions=['1.0'])
    def ping(self, *args):
        return 'pong'

    @rpc_method(name='ping', versions=['1.1'])
    def ping_1_1(self, *args):
        return 'Pong'


test = RpcService()
try:
    test.start()
except KeyboardInterrupt:
    test.stop()
