import logging
import os

from miteD.service.service import rpc_service, rpc_method


@rpc_service(name='rpc1', versions=['1.0'])
class RpcService:
    def __init__(self):
        self.rpc2 = self.get_remote_service(service_name='rpc2', version='1.0')

    @rpc_method(versions=['1.0'])
    async def ping(self):
        return self.rpc2.foo()


logging.basicConfig(level=logging.getLevelName(os.getenv('LOG_LEVEL', 'INFO')))
test = RpcService()
try:
    test.start()
except KeyboardInterrupt:
    test.stop()
