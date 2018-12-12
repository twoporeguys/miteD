import logging
import asyncio
from json import loads, dumps
from collections import deque
from nats.aio.errors import ErrTimeout
from nats.aio.utils import new_inbox
from .errors import MiteDRPCError
from ..utils import format_version_str


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
            unique_sid = new_inbox()
            result_msg = deque()
            future = asyncio.Future()

            async def callback_handler(msg):
                nonlocal future
                nonlocal result_msg
                data = self.unfurl_message(msg)
                if data:
                    result_msg.append(data)
                else:
                    future.set_result(''.join(result_msg))

            await self._nc.subscribe(unique_sid, cb=callback_handler)
            await self._nc.publish_request(self._method_path, unique_sid, dumps(args).encode())
            return loads(await asyncio.wait_for(future, timeout=3.0))
        except (ErrTimeout, asyncio.futures.TimeoutError):
            msg = 'Call timeout for: "{}"'.format(self._method_path)
            status = 504
            raise MiteDRPCError({'status': status, 'body': msg})
        except MiteDRPCError as err:
            raise err
        finally:
            await self._nc.unsubscribe(unique_sid)

    def unfurl_message(self, msg):
        result = loads(msg.data.decode())
        self._logger.debug(result)
        if result['status'] == 200:
            return result['body']
        else:
            raise MiteDRPCError(result)

