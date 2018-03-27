from json import loads, dumps
from nats.aio.client import Client as NATS


class RemoteService:
    def __init__(self, name, version, loop, broker_urls=('nats://127.0.0.1:4222',)):
        self._nc = NATS()
        self._loop = loop
        self._brokers_url = broker_urls
        self._name = name
        self._version = version.replace('.', '_')
        self._proxy_cache = {}
        self._prefix = '{}.{}'.format(self._name, self._version)

    def __getattr__(self, item):
        if item not in self._proxy_cache.keys():
            method_path = '{}.{}'.format(self._prefix, item)

            async def proxy(*args):
                await self._connect()
                reply = await self._nc.timed_request(method_path, dumps(args).encode(), timeout=3.0)
                return loads(reply.data.decode())
            self._proxy_cache[item] = proxy
        return self._proxy_cache.get(item)

    async def _connect(self):
        if not self._nc.is_connected and not self._nc.is_connecting and not self._nc.is_reconnecting:
            print('[miteD.RS] Connect {} {} on {}'.format(self._name,
                                                                                   self._version,
                                                                                   self._brokers_url
                                                                                   ))
            await self._nc.connect(io_loop=self._loop, servers=self._brokers_url, verbose=True)
