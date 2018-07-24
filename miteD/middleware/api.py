import asyncio
import json
import requests
import uuid
import os
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
                cls.generate_endpoint_docs = self.generate_endpoint_docs

            async def _connect(self):
                return await self._nc.connect(io_loop=self._loop, servers=self._broker_urls, verbose=True)

            def start(self):
                self._load_app()
                print('\n'.join(['{} {}'.format(*(list(route.methods)[0], path))
                                 for path, route in self._app.router.routes_all.items()]))
                server = self._app.create_server(host='0.0.0.0', port=8000)
                asyncio.ensure_future(self._connect())
                asyncio.ensure_future(server)
                self._register_with_consul()
                self._loop.call_later(5, self._add_TTL_check_to_loop())
                self._loop.run_forever()
                self._loop.close()

            def stop(self):
                pending = asyncio.Task.all_tasks(self._loop)
                for task in pending:
                    task.cancel()
                    with suppress(asyncio.CancelledError):
                        self._loop.run_until_complete(task)
                self._loop.close()
                self._deregister_with_consul()

            def get_remote_service(self, service_name, version):
                return RemoteService(name=service_name, version=version, nc=self._nc)

            def _register_with_consul(self):
                self.consul_id = os.getenv("HOSTNAME")
                # This is also the pod name

                api_data = {
                  # "dc1" is the default but there's 'no' way to know this without env variable in the yaml.
                  "Datacenter": "dc1",
                  "ID": self.consul_id,
                  "Address": f"api/{name}/{versions}",
                  "Service": {
                    "ID": self.consul_id,
                    "Service": "chip-api",
                    "Tags": [
                      "api",
                      f"{versions}",
                      f"{name}"
                    ]
                  },
                  "Check": {
                      "ID": f"{self.consul_id}-TTLCheck",
                      "DeregisterCriticalServiceAfter": "10m",
                      "TTL": "30s",
                  }
                }

                requests.put(
                    "consul:8500/v1/catalog/register",
                    data=api_data
                )

            def _deregister_with_consul(self):
                requests.put(f"consul:8500/agent/service/deregister/{self.consul_id}")

            @asyncio.coroutine
            def _pass_TTL_check(self):
                while True:
                    requests.put(f"consul;:8500//agent/check/pass/{self.consul_id}-TTLCheck")
                    yield from asyncio.sleep(15)

            def _add_TTL_check_to_loop(self):
                return asyncio.Task(self._pass_TTL_check())

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

            def generate_endpoint_docs(self):
                """
                This method is called by a document generating script and yields swagger style (JSON) API documentation
                for the non-schema portion of swagger. Information about the schemas is accesed at the service level in the validators
                library.
                """
                open_api_version = {"openapi": "3.0.0"}

                class_doc_string = json.loads(cls.__doc__)
                info = {"info": {
                            "title": class_doc_string["title"],
                            "description": class_doc_string["description"],
                            "version": class_doc_string["version"],
                            "contact": {
                                 "name": class_doc_string["contact"]["name"],
                                 "email": class_doc_string["contact"]["email"]
                                        },
                            }}
                servers = {"servers":
                                [
                                    {
                                     "url": f"https://x1-stg.twoporeguys.com/api/{name}/{str(versions[0])}/>",
                                     "description": "Staging middleware endpoints."
                                    },
                                    {
                                      "url": f"https://stg.twoporeguys.com/api/{name}/{str(versions[0])}>/",
                                      "description": "Production server."
                                    },
                                    {
                                     "url": f"<local-reverse-proxy>/api/{name}/{str(versions[0])}>/",
                                     "description": "Local server though Minikube."
                                     }
                                ]
                            }

                external_docs = {
                    "externalDocs": {
                        "description": "The rendered OpenAPI/Swagger for this api.",
                        "url": f"devdocs.twoporeguys.com/x1/{name}.html"
                    }
                }
                swagger_dict = {
                    **open_api_version,
                    **class_doc_string,
                    **info,
                    **servers,
                    **external_docs,
                    **{"paths": self._doc_paths()}
                }

                return swagger_dict

            def _doc_paths(self):
                """" Helper method for finding endpoint in miteD."""
                paths = {}
                wrapped = cls
                for member in [getattr(wrapped, member_name) for member_name in dir(wrapped)]:
                    if callable(member):
                        if hasattr(member, '__api_path__'):
                            try:
                                if member.__api_path__ in paths.keys():
                                    paths[member.__api_path__][member.__api_method__] = json.loads(member.__doc__)
                                else:
                                    paths[member.__api_path__] = {member.__api_method__: json.loads(member.__doc__)}
                            except Exception as e:
                                print(member.__api_path__)
                                print(member.__api_method__)
                                print(e)
                return paths

        return Api

    return wrapper


def redirect(target, status=302, headers=None, content_type='text/html'):
    return response.redirect(target, status=status, headers=headers, content_type=content_type)
