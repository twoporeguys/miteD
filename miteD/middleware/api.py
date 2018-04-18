import asyncio
from contextlib import suppress

from nats.aio.client import Client as NATS
from sanic import Sanic, response

from miteD.service.errors import MiteDRPCError
from miteD.service.client import RemoteService


def api(name, versions, broker_urls=('nats://127.0.0.1:4222',)):
    def wrapper(cls):

        class Api(object):
            _loop = asyncio.get_event_loop()
            _broker_urls = broker_urls
            _nc = NATS()

            def __init__(self):
                cls.loop = self._loop
                cls.get_remote_service = self.get_remote_service

            async def _connect(self):
                return await self._nc.connect(io_loop=self._loop, servers=self._broker_urls, verbose=True)

            def start(self):
                self._load_app()
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

            def _load_app(self):
                self.endpoints = {'*': {}}
                self._app = Sanic(name=name)
                self.parse_wrapped_endpoints()
                for version in versions:
                    for path, methods in self.endpoints.get('*', {}).items():
                        for method, handler in methods.items():
                            self._app.add_route(handler, '/' + version + path, methods=[method])
                    for path, methods in self.endpoints.get(version, {}).items():
                        for method, handler in methods.items():
                            self._app.add_route(handler, '/' + version + path, methods=[method])

            def parse_wrapped_endpoints(self):
                wrapped = cls()
                for member in [getattr(wrapped, member_name) for member_name in dir(wrapped)]:
                    if callable(member):
                        if hasattr(member, '__api_path__') \
                                and hasattr(member, '__api_method__') \
                                and hasattr(member, '__api_versions__'):
                            for api_version in member.__api_versions__:
                                version = self.endpoints.get(api_version, {})
                                path = version.get(member.__api_path__, {})
                                path[member.__api_method__] = self._type_response(member)
                                version[member.__api_path__] = path
                                self.endpoints[api_version] = version

            @staticmethod
            def _type_response(method):
                response_type = method.__response_type__ if hasattr(method, '__response_type__') else response.json

                async def typed_handler(*args, **kwargs):
                    result = method(*args, **kwargs)
                    try:
                        result = (await result) if asyncio.iscoroutine(result) else result
                        print(result)
                        if isinstance(result, tuple):
                            body = result[0]
                            rest = result[1:]
                        else:
                            body = result
                            rest = ()
                        return response_type(*(body, *rest))
                    except MiteDRPCError as err:
                        return err.message, (err.status,)
                return typed_handler

        return Api

    return wrapper


def redirect(target, status=302, headers=None, content_type='test/html'):
    return response.redirect(target, status=status, headers=headers, content_type=content_type)
