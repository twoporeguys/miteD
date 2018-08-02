import asyncio
import logging
from datetime import datetime
from contextlib import suppress
from json import loads, dumps, JSONDecodeError
from nats.aio.client import Client as NATS

from miteD.service.client import RemoteService
from miteD.service.utils import format_version_str
import miteD.service.response as response


def parse_wrapped_endpoints(cls, *args, **kwargs):
    wrapped = cls(*args, **kwargs)
    endpoints = {'*': {}}
    for member in [getattr(wrapped, member_name) for member_name in dir(wrapped)]:
        if callable(member):
            if hasattr(member, '__rpc_name__') and hasattr(member, '__rpc_versions__'):
                for version in member.__rpc_versions__:
                    members = endpoints.get(version, {})
                    members[member.__rpc_name__] = member
                    endpoints[version] = members
    return endpoints


def rpc_service(name, versions, broker_urls=('nats://127.0.0.1:4222',)):
    def wrapper(cls):

        class Service(object):
            _name = name
            _loop = asyncio.get_event_loop()
            _broker_urls = broker_urls
            _nc = NATS()
            _versions = [format_version_str(v) for v in versions]

            def __init__(self):
                self._logger = logging.getLogger('mited.Service({})'.format(name))
                self._access_log = logging.getLogger('mited.rpc.access')
                cls.loop = self._loop
                cls.get_remote_service = self.get_remote_service
                self.endpoints = parse_wrapped_endpoints(cls)

            def start(self):
                asyncio.ensure_future(self._start())
                self._loop.run_forever()
                self._loop.close()

            def stop(self):
                self._logger.info('Stopping...')
                pending = asyncio.Task.all_tasks(self._loop)
                for task in pending:
                    task.cancel()
                    with suppress(asyncio.CancelledError):
                        self._loop.run_until_complete(task)
                self._loop.close()

            async def _start(self):
                self._logger.info('Connecting to %s', self._broker_urls)
                await self._nc.connect(io_loop=self._loop, servers=self._broker_urls, verbose=True, name=self._name)
                return await asyncio.wait([self._expose_api_version(name, version) for version in self._versions])

            async def handle_message(self, message):
                asyncio.ensure_future(self._handle_request(message))

            def get_remote_service(self, service_name, version):
                self._logger.debug('remote service: %s %s', service_name, version)
                return RemoteService(name=service_name, version=version, nc=self._nc)

            def _get_handler(self, msg):
                subject = msg.subject
                api_version = subject.split('.')[1]
                api_method = subject.split('.')[2]
                api = self.endpoints.get(api_version, self.endpoints['*'])
                method = api.get(api_method, self.endpoints['*'].get(api_method, None))
                if method:
                    return method
                else:
                    raise NotImplementedError(subject)

            async def _expose_api_version(self, api, api_version):
                subject = '{}.{}.*'.format(api, api_version)
                self._logger.info('listening for messages on ' + subject)
                await self._nc.subscribe(subject, cb=self.handle_message)

            async def _handle_request(self, request):
                try:
                    method = self._get_handler(request)
                    data = self._get_payload(request)
                    result = await method(*data)
                    if asyncio.iscoroutine(result):
                        result = await result
                    return await self._send_reply(request, response.ok(result))
                except NotImplementedError:
                    return await self._send_reply(request, response.not_found())
                except JSONDecodeError:
                    return await self._send_reply(request, response.bad_request())
                except RuntimeError:
                    return await self._send_reply(request, response.internal_server_error())

            def _send_reply(self, request, reply):
                body = dumps(reply).encode()
                self._log_access(request, reply['status'], len(body))
                return self._nc.publish(request.reply, body)

            def _log_access(self, request, status, length):
                self._access_log.info('[%s]"%s" %s %s', datetime.utcnow().isoformat(), request.subject, status, length)

            @staticmethod
            def _get_payload(msg):
                return loads(msg.data.decode())

        return Service

    return wrapper


def rpc_method(name=None, versions=None):
    def wrapper(fn):
        fn.__rpc_name__ = name or fn.__name__
        fn.__rpc_versions__ = (format_version_str(v) for v in versions) if versions else ('*', )
        return fn
    return wrapper
