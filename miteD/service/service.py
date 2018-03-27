import asyncio
import logging
from contextlib import suppress
from json import loads, dumps
from nats.aio.client import Client as NATS

from miteD.service.client import RemoteService


def parse_wrapped_endpoints(cls, *args, **kwargs):
    wrapped = cls(*args, **kwargs)
    endpoints = {'*': {}}
    for member in [getattr(wrapped, member_name) for member_name in dir(wrapped)]:
        if callable(member):
            if hasattr(member, '__rpc_name__') and hasattr(member, '__rpc_versions__'):
                for version in [version.replace('.', '_') for version in member.__rpc_versions__]:
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

            def __init__(self):
                logging.basicConfig(level=logging.INFO)
                cls.loop = self._loop
                cls.get_remote_service = self.get_remote_service
                self.endpoints = parse_wrapped_endpoints(cls)

            def start(self):
                asyncio.ensure_future(self._start())
                self._loop.run_forever()
                self._loop.close()

            def stop(self):
                pending = asyncio.Task.all_tasks(self._loop)
                for task in pending:
                    task.cancel()
                    with suppress(asyncio.CancelledError):
                        self._loop.run_until_complete(task)
                self._loop.close()

            async def _start(self):
                logging.info('[miteD.RPC] Connect %s', self._broker_urls)
                await self._nc.connect(io_loop=self._loop, servers=self._broker_urls, verbose=True, name=self._name)

                return await asyncio.wait([self.expose_api_version(name, version) for version in versions])

            async def handle_request(self, msg):
                try:
                    subject = msg.subject
                    api_version = subject.split('.')[1]
                    api_method = subject.split('.')[2]
                    reply = msg.reply
                    data = self.get_payload(msg)
                    api = self.endpoints.get(api_version, self.endpoints['*'])
                    method = api.get(api_method, self.endpoints['*'].get(api_method, None))
                    if method:
                        await self._nc.publish(reply, dumps(method(*data)).encode())
                    else:
                        raise NotImplementedError()
                except Exception as err:
                    print(err)

            async def expose_api_version(self, api, api_version):
                subject = '{}.{}.*'.format(api, api_version.replace('.', '_'))
                logging.info('listening for messages on ' + subject)
                await self._nc.subscribe(subject, cb=self.handle_request)

            def get_remote_service(self, name, version):
                return RemoteService(name=name, version=version, loop=self._loop, broker_urls=self._broker_urls)

            @staticmethod
            def get_payload(msg):
                data = msg.data.decode()
                return loads(data)

        return Service

    return wrapper


def rpc_method(name=None, versions=None):
    def wrapper(fn):
        fn.__rpc_name__ = name or fn.__name__
        fn.__rpc_versions__ = versions or ['*']
        return fn
    return wrapper
