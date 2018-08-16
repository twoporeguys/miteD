import logging
import requests
import asyncio

from miteD.middleware.api import api
from miteD.middleware.methods import get
from miteD.middleware.types import json


@api(
    name='middleware-produces-notifications',
    versions=['1.0'],
    broker_urls=['nats://127.0.0.1:4222'],
    notification_topics=['updates'],
    port=8001,
)
class MiddlewareProducesNotifications:
    @get(path='/')
    @json
    async def root(self, request):
        msg = 'Update notification from {}'.format(self.__class__.__name__)
        await self.notify.updates(msg)
        return 'ROOT', 200


def do_request():
    r = requests.get('http://127.0.0.1:8001/1.0/')
    logging.info('Request returned: {}'.format(r.json()))


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    test = MiddlewareProducesNotifications()
    loop.run_in_executor(None, do_request)
    try:
        test.start()
    except KeyboardInterrupt:
        test.stop()
