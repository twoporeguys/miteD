import logging
from json import loads, dumps
from nats.aio.errors import ErrTimeout

from miteD.service.errors import MiteDRPCError
from miteD.utils import format_version_str


class RemoteService:
    def __init__(self, name, version, nc):
        self._logger = logging.getLogger('mited.RemoteService')
        self._nc = nc
        self._name = name
        self._version = format_version_str(version)
        self._proxy_cache = {}
        self._prefix = 'rpc.service.{}.{}'.format(name, self._version)

    def __getattr__(self, item):
        self._logger.debug('[miteD.RS.__getattr__] %s', item)
        return MethodProxy(self._nc, '{}.{}'.format(self._prefix, item))


class MethodProxy:
    def __init__(self, nc, method_path):
        self._logger = logging.getLogger('mited.MethodProxy({})'.format(method_path))
        self._nc = nc
        self._method_path = method_path

    async def __call__(self, *args):
        try:
            self._logger.debug('<- %s %s', self._method_path, args)
            reply = await self._nc.timed_request(self._method_path, dumps(args).encode(), timeout=3.0)
            return self.__get_result(reply)
        except ErrTimeout:
            msg = 'Call timeout for: "{}"'.format(self._method_path)
            status = 504
            raise MiteDRPCError({'status': status, 'body': msg})
        except MiteDRPCError as err:
            raise err

    def __get_result(self, reply):
        result = loads(reply.data.decode())
        self._logger.debug(result)
        status = result['status']
        if status == 200:
            return result['body']
        else:
            raise MiteDRPCError(result)
