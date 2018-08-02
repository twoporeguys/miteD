import asyncio
import logging
from datetime import datetime
from contextlib import suppress
from json import loads, dumps, JSONDecodeError
from nats.aio.client import Client as NATS
from functools import wraps, partial

from miteD.service.client import RemoteService
from miteD.service.utils import get_members_if, format_version_str
import miteD.service.response as response


def is_rpc_method(method):
    return getattr(method, '__rpc_method__', False)


def is_notification_handler(method):
    return getattr(method, '__notification_handler__', False)


def parse_wrapped_endpoints(cls):
    wrapped = cls()
    endpoints = {'*': {}}
    for member in get_members_if(is_rpc_method, wrapped):
        for version in member.__rpc_versions__:
            members = endpoints.setdefault(version, {})
            members[member.__rpc_name__] = member
    return endpoints


def get_notification_handlers(cls):
    wrapped = cls()
    return get_members_if(is_notification_handler, wrapped)


def rpc_service(
        name,
        versions,
        broker_urls=('nats://127.0.0.1:4222',),
        notification_topics=None,
):
    def wrapper(cls):
        class Notify():
            pass

        class Service(object):
            _layer = 'service'
            _name = name
            _loop = asyncio.get_event_loop()
            _broker_urls = broker_urls
            _notification_topics = notification_topics or []
            _nc = NATS()
            _versions = [format_version_str(v) for v in versions]

            def __init__(self):
                self._logger = logging.getLogger('mited.Service({})'.format(name))
                self._access_log = logging.getLogger('mited.rpc.access')
                self._add_notify(cls)
                cls.loop = self._loop
                cls.get_remote_service = self.get_remote_service
                self.endpoints = parse_wrapped_endpoints(cls)
                self.notification_handlers = get_notification_handlers(cls)

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
                await self._start_notification_handlers()
                return await asyncio.wait([self._expose_api_version(name, version) for version in self._versions])

            async def handle_message(self, message):
                asyncio.ensure_future(self._handle_request(message))

            def get_remote_service(self, service_name, version):
                self._logger.debug('remote service: %s %s', service_name, version)
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

            async def _send_notification(self, channel, msg):
                await self._nc.publish(channel, dumps(msg).encode())

            def _add_notify(self, cls):
                if not self._notification_topics:
                    return

                notify = Notify()
                channel_stem = 'notification.{}.{}'.format(self._layer, self._name)
                for version in self._versions:
                    for topic in self._notification_topics:
                        channel = '{}.{}.{}'.format(channel_stem, version, topic)
                        self._logger.info('Reigstering notifications channel: {}'.format(channel))
                        setattr(notify, topic, partial(self._send_notification, channel))

                cls.notify = notify

            @staticmethod
            def assemble_notification_channel_names(handler):
                layer = handler.__notification_layer__
                name = handler.__notification_name__
                versions = handler.__notification_versions__
                topic = handler.__notification_topic__

                return ['notification.{}.{}.{}.{}'.format(layer, name, v, topic) for v in versions]

            async def _start_notification_handlers(self):
                coros = []
                for h in self.notification_handlers:
                    channels = self.assemble_notification_channel_names(h)
                    self._logger.info("Staring notifications handler for channels: {}".format(channels))
                    coros.extend([self._nc.subscribe(c, cb=h) for c in channels])

                await asyncio.gather(*coros)

        return Service

    return wrapper


def rpc_method(name='', versions=None):
    def wrapper(fn):
        fn.__rpc_method__ = True
        fn.__rpc_name__ = name or fn.__name__
        fn.__rpc_versions__ = (format_version_str(v) for v in versions) if versions else ('*', )
        return fn
    return wrapper


def notification_handler(layer='*', name='*', versions=None, topic='*'):
    def wrapper(fn):
        fn.__notification_handler__ = True
        fn.__notification_layer__ = layer
        fn.__notification_name__ = name
        fn.__notification_versions__ = (format_version_str(v) for v in versions) if versions else ('*',)
        fn.__notification_topic__ = topic

        @wraps(fn)
        async def translate(self, msg):
            subject = msg.subject
            data = msg.data.decode()
            if asyncio.iscoroutinefunction(fn):
                return await fn(self, subject, data)
            else:
                return fn(self, subject, data)

        return translate

    return wrapper
