import asyncio
from contextlib import suppress
from json import loads, dumps
from nats.aio.client import Client as NATS


def parse_wrapped_endpoints(cls, *args, **kwargs):
    wrapped = cls(*args, **kwargs)
    endpoints = {'*': {}}
    for member in [getattr(wrapped, member_name) for member_name in dir(wrapped)]:
        if hasattr(member, '__rpc_name__') and hasattr(member, '__rpc_versions__'):
            for version in [version.replace('.', '_') for version in member.__rpc_versions__]:
                members = endpoints.get(version, {})
                members[member.__rpc_name__] = member
                endpoints[version] = members
    for version in endpoints.keys():
        print(version, endpoints[version].keys())
    return endpoints


def rpc_service(name, versions, broker_urls=('nats://127.0.0.1:4222',)):
    def wrapper(cls):
        async def listen(loop, endpoints):
            nc = NATS()
            await nc.connect(io_loop=loop, servers=broker_urls)

            def get_payload(msg):
                data = msg.data.decode()
                return loads(data)

            async def handle_request(msg):
                try:
                    subject = msg.subject
                    api_version = subject.split('.')[1]
                    api_method = subject.split('.')[2]
                    reply = msg.reply
                    data = get_payload(msg)
                    api = endpoints.get(api_version, endpoints['*'])
                    method = api.get(api_method, endpoints['*'].get(api_method, None))
                    if method:
                        await nc.publish(reply, dumps(method(*data)).encode())
                    else:
                        raise NotImplementedError()
                except Exception as err:
                    print(err)

            async def expose_api_version(api, api_version):
                subject = '{}.{}.*'.format(api, api_version.replace('.', '_'))
                await nc.subscribe(subject, cb=handle_request)
                print('listening for messages on ' + subject)

            for version in versions:
                await expose_api_version(name, version)

        class Service(object):
            _loop = asyncio.get_event_loop()

            def __init__(self, *args, **kwargs):
                cls.loop = self._loop
                self.endpoints = parse_wrapped_endpoints(cls, *args, *kwargs)

            def start(self):
                self._loop.run_until_complete(listen(self._loop, self.endpoints))
                self._loop.run_forever()
                self._loop.close()

            def stop(self):
                pending = asyncio.Task.all_tasks(self._loop)
                for task in pending:
                    task.cancel()
                    with suppress(asyncio.CancelledError):
                        self._loop.run_until_complete(task)
                self._loop.close()

        return Service
    return wrapper


def rpc_method(name=None, versions=None):
    def wrapper(fn):
        fn.__rpc_name__ = name or fn.__name__
        fn.__rpc_versions__ = versions or ['*']
        return fn
    return wrapper
