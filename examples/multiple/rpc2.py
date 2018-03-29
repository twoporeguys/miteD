import logging
import os
from miteD.service.service import rpc_service, rpc_method


@rpc_service(name='rpc2', versions=['1.0'])
class RpcService:
    def __init__(self):
        self.rpc1 = self.get_remote_service(service_name='rpc1', version='1.0')

    @rpc_method(name='foo', versions=['1.0'])
    async def ping(self):
        return 'PONG'

    @rpc_method(versions=['1.0'])
    async def recurse(self):
        return self.rpc1.ping()


logging.basicConfig(level=logging.getLevelName(os.getenv('LOG_LEVEL', 'INFO')))
test = RpcService()
try:
    test.start()
except KeyboardInterrupt:
    test.stop()
