import asyncio
import json
import requests
import os
import logging

from nats.aio.client import Client as NATS
from sanic import Sanic, response

from miteD.mixin.notifications import NotificationsMixin
from miteD.service.errors import MiteDRPCError
from miteD.service.client import RemoteService

from miteD.middleware.methods import is_api_method
from miteD.utils import get_members_if


TTL_CHECK_IN_INTERVAL = os.getenv("TTL_CHECK_IN_INTERVAL", 15)
# This is how often a service should pass it's TTL check

TTL_TIMEOUT_INTERVAL = os.getenv("TTL_TIMEOUT_INTERVAL", "60s")
# This determines how long the monitoring service waits before classifying a service as degraded
# in the absence of a passing TTL check.

CONSUL_ADDRESS = os.getenv("CONSUL_ADDRESS", "http://consul:8500")
# This is routing to the consul cluster, in our case, handled by the consul k8 service.

KEEP_DEGRADED_SERVICE = os.getenv("KEEP_DEGRADED_SERVICE", "3m")
# Determines how long consul will keep a degraded service registered.

RETRY_TTL_PASS_OR_REGISTRY = os.getenv("RETRY_TTL_PASS_OR_REGISTRY", 3)
# Specifies how many times a service should try to pass TTL checks
# OR REGISTER with Consul when receiving errors from http request.


def api(
        name,
        versions,
        broker_urls=('nats://127.0.0.1:4222',),
        notification_topics=None,
        host='0.0.0.0',
        port=8000,
):
    def wrapper(cls):

        class Api(NotificationsMixin):
            _layer = 'middleware'
            _loop = asyncio.get_event_loop()
            _name = name
            _broker_urls = broker_urls
            _notification_topics = notification_topics or []
            _nc = NATS()

            def __init__(self):
                self._logger = logging.getLogger('mited.Middleware({})'.format(self._name))
                self._add_notify(cls)
                self.registered_with_consul = False
                self.consul_connection_attempts = RETRY_TTL_PASS_OR_REGISTRY
                cls.loop = self._loop
                cls.get_remote_service = self.get_remote_service
                cls.generate_endpoint_docs = self.generate_endpoint_docs
                self.notification_handlers = self.get_notification_handlers(cls)

            def start(self):
                self._load_app()
                self._logger.info('\n'.join(['{} {}'.format(*(list(route.methods)[0], path))
                                 for path, route in self._app.router.routes_all.items()]))

                self._loop.create_task(self._start())
                self._loop.run_forever()
                self._loop.close()

            def stop(self):
                self._logger.info('Stopping...')
                group = asyncio.gather(*asyncio.Task.all_tasks(), return_exceptions=True)
                group.cancel()
                self._loop.run_until_complete(group)
                self._loop.close()
                self._deregister_with_consul()

            async def _start(self):
                self._logger.info('Connecting to %s', self._broker_urls)
                await self._app.create_server(host=host, port=port)
                await self._nc.connect(io_loop=self._loop, servers=self._broker_urls, verbose=True, name=self._name)
                await self._pass_TTL_check()
                await self._start_notification_handlers()

            def get_remote_service(self, service_name, version):
                self._logger.debug('Remote service: %s %s', service_name, version)
                return RemoteService(name=service_name, version=version, nc=self._nc)

            def _register_with_consul(self):
                self.consul_id = os.getenv("HOSTNAME")
                # This is also the pod name

                api_data = {
                  "Name": self.consul_id,
                  "ID": self.consul_id,
                  "Address": f"api/{name}/{versions[0]}",
                  "Tags": [
                      "api",
                      str(versions[0]),
                      name
                  ],
                  "Service": {
                    "ID": self.consul_id,
                    "Service": f"{name}-{versions[0]}"
                  },
                  "Check": {
                      "CheckID": f"{self.consul_id}-TTLCheck",
                      "DeregisterCriticalServiceAfter": KEEP_DEGRADED_SERVICE,
                      "TTL": TTL_TIMEOUT_INTERVAL
                  }
                }

                try:
                    r = requests.put(
                        CONSUL_ADDRESS + "/v1/agent/service/register",
                        data=json.dumps(api_data)
                    )
                except requests.exceptions.RequestException:
                    self._logger.warning('Error whilst trying to register with consul', exc_info=True)
                    self.consul_connection_attempts -= 1
                else:
                    if r.ok:
                        self.registered_with_consul = True
                        # Reset this now that we have registered with consul
                        # so that we have `RETRY_TTL_PASS_OR_REGISTRY` times attempts for
                        # purely the TTL ping as well
                        self.consul_connection_attempts = RETRY_TTL_PASS_OR_REGISTRY

            def _deregister_with_consul(self):
                requests.put(CONSUL_ADDRESS + f"/v1/agent/service/deregister/{self.consul_id}")

            async def _pass_TTL_check(self):
                while True and self.consul_connection_attempts:
                    try:
                        if self.registered_with_consul:
                            requests.put(f"{CONSUL_ADDRESS}/v1/agent/check/pass/{self.consul_id}-TTLCheck")
                        else:
                            self._register_with_consul()
                        await asyncio.sleep(TTL_CHECK_IN_INTERVAL)
                    except requests.exceptions.RequestException:
                        self.consul_connection_attempts -= 1

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
                for member in get_members_if(is_api_method, wrapped):
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
                        logging.debug(result)
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
                                msg = 'Api path/method = {}/{}'.format(member.__api_path__, member.__api_method__)
                                self._logger.exception(msg)
                return paths

        return Api

    return wrapper


def redirect(target, status=302, headers=None, content_type='text/html'):
    return response.redirect(target, status=status, headers=headers, content_type=content_type)
