import asyncio
from contextlib import suppress

from nats.aio.client import Client as NATS
from sanic import Sanic

from miteD.service.client import RemoteService


def parse_wrapped_endpoints(wrapped):
    endpoints = {'*': {}}
    for member in [getattr(wrapped, member_name) for member_name in dir(wrapped)]:
        if callable(member):
            if hasattr(member, '__api_path__') \
                    and hasattr(member, '__api_method__') \
                    and hasattr(member, '__api_versions__'):
                for api_version in member.__api_versions__:
                    version = endpoints.get(api_version, {})
                    path = version.get(member.__api_path__, {})
                    path[member.__api_method__] = member
                    version[member.__api_path__] = path
                    endpoints[api_version] = version
    return endpoints


def api(name, versions, broker_urls=('nats://127.0.0.1:4222',)):
    def wrapper(cls):

        class Api(object):
            _app = Sanic(name=name)
            _loop = asyncio.get_event_loop()
            _broker_urls = broker_urls
            _nc = NATS()

            def __init__(self):
                cls.loop = self._loop
                cls.get_remote_service = self.get_remote_service
                wrapped = cls()
                self.endpoints = parse_wrapped_endpoints(wrapped)
                for version in versions:
                    for path, methods in self.endpoints.get('*', {}).items():
                        for method, handler in methods.items():
                            self._app.add_route(handler, '/' + version + path, methods=[method])
                    for path, methods in self.endpoints.get(version, {}).items():
                        for method, handler in methods.items():
                            self._app.add_route(handler, '/' + version + path, methods=[method])

            async def _connect(self):
                return await self._nc.connect(io_loop=self._loop, servers=self._broker_urls, verbose=True)

            def start(self):
                print('\n'.join(['{} {}'.format(*(list(route.methods)[0], path))
                                 for path, route in self._app.router.routes_all.items()]))
                server = self._app.create_server(host='0.0.0.0', port=8000)
                asyncio.ensure_future(self._connect())
                asyncio.ensure_future(server)
                self._loop.run_forever()
                self._loop.close()

            def stop(self):
                pending = asyncio.Task.all_tasks(self._loop)
                for task in pending:
                    task.cancel()
                    with suppress(asyncio.CancelledError):
                        self._loop.run_until_complete(task)
                self._loop.close()

            def get_remote_service(self, service_name, version):
                return RemoteService(name=service_name, version=version, nc=self._nc)

        return Api

    return wrapper
