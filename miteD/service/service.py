import asyncio
import logging
import json
from datetime import datetime
from nats.aio.client import Client as NATS

from .client import RemoteService
from ..utils import get_members_if, format_version_str, CustomJsonEncoder
from ..mixin.notifications import NotificationsMixin
from . import response


def is_rpc_method(method):
    return getattr(method, '__is_rpc_method__', False)


def parse_wrapped_endpoints(cls):
    wrapped = cls()
    endpoints = {'*': {}}
    for member in get_members_if(is_rpc_method, wrapped):
        for version in member.__rpc_versions__:
            members = endpoints.setdefault(version, {})
            members[member.__rpc_name__] = member
    return endpoints


def rpc_service(
        name,
        versions,
        broker_urls=('nats://127.0.0.1:4222',),
        notification_topics=None,
        chunking_size=65536
):
    def wrapper(cls):
        class Service(NotificationsMixin):
            _layer = 'service'
            _name = name
            _loop = asyncio.get_event_loop()
            _broker_urls = broker_urls
            _notification_topics = notification_topics or []
            _versions = [format_version_str(v) for v in versions]

            def __init__(self, nc=NATS()):
                self._logger = logging.getLogger('mited.Service({})'.format(self._name))
                self._nc = nc
                self.chunking_size = chunking_size
                self._access_log = logging.getLogger('mited.rpc.access')
                self._add_notify(cls)
                cls.loop = self._loop
                cls.get_remote_service = self.get_remote_service
                self.endpoints = parse_wrapped_endpoints(cls)
                self.notification_handlers = self.get_notification_handlers(cls)

            def start(self):
                asyncio.ensure_future(self._start())
                self._loop.run_forever()
                self._loop.close()

            def stop(self):
                self._logger.info('Stopping...')
                group = asyncio.gather(*asyncio.Task.all_tasks(), return_exceptions=True)
                group.cancel()
                self._loop.run_until_complete(group)
                self._loop.close()

            async def _start(self):
                self._logger.info('Connecting to %s', self._broker_urls)
                await self._nc.connect(io_loop=self._loop, servers=self._broker_urls, verbose=True, name=self._name)
                await self._start_notification_handlers()
                return await asyncio.wait([self._expose_api_version(name, version) for version in self._versions])

            async def handle_message(self, message):
                asyncio.ensure_future(self._handle_request(message))

            def get_remote_service(self, service_name, version):
                self._logger.debug('Remote service: %s %s', service_name, version)
                return RemoteService(name=service_name, version=version, nc=self._nc)

            def _get_handler(self, msg):
                subject = msg.subject
                api_version = subject.split('.')[3]
                api_method = subject.split('.')[4]
                api = self.endpoints.get(api_version, self.endpoints['*'])
                method = api.get(api_method, self.endpoints['*'].get(api_method, None))
                if method:
                    return method
                else:
                    raise NotImplementedError(subject)

            async def _expose_api_version(self, api, api_version):
                subject = '{}.{}.{}.{}.*'.format('rpc', 'service', api, api_version)
                self._logger.info('listening for RPC calls on ' + subject)
                await self._nc.subscribe(subject, cb=self.handle_message)

            async def _handle_request(self, request):
                try:
                    method = self._get_handler(request)
                    data = self._get_payload(request)
                    result = await method(*data)
                    if asyncio.iscoroutine(result):
                        result = await result
                    serialized_result = json.dumps(result, cls=CustomJsonEncoder)
                    if len(serialized_result) <= self.chunking_size:
                        await self._send_reply(request, response.ok(serialized_result))
                    else:
                        while serialized_result:
                            await self._send_reply(request, response.ok(serialized_result[:self.chunking_size]))
                            serialized_result = serialized_result[self.chunking_size:]
                    return await self._send_reply(request, response.ok(''))

                except NotImplementedError:
                    return await self._send_reply(request, response.not_found())
                except json.JSONDecodeError:
                    return await self._send_reply(request, response.bad_request())
                except RuntimeError:
                    return await self._send_reply(request, response.internal_server_error())

            def _send_reply(self, request, reply):
                body = json.dumps(reply, cls=CustomJsonEncoder).encode()
                self._log_access(request, reply['status'], len(body))
                return self._nc.publish(request.reply, body)

            def _log_access(self, request, status, length):
                self._access_log.info('[%s]"%s" %s %s', datetime.utcnow().isoformat(), request.subject, status, length)

            @staticmethod
            def _get_payload(msg):
                return json.loads(msg.data.decode())

        return Service
    return wrapper


def rpc_method(name='', versions=None):
    def wrapper(fn):
        fn.__is_rpc_method__ = True
        fn.__rpc_name__ = name or fn.__name__
        fn.__rpc_versions__ = (format_version_str(v) for v in versions) if versions else ('*', )
        return fn
    return wrapper
