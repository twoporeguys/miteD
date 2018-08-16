import logging
import asyncio
from miteD.service.service import rpc_service, rpc_method
from nats.aio.client import Client as NatsClient
from miteD.service.client import RemoteService
from miteD.service.errors import MiteDRPCError


NATS_URI = 'nats://127.0.0.1:4222'


@rpc_service(
    name='notifications_producer',
    versions=['1.0'],
    broker_urls=[NATS_URI],
    notification_topics=['errors', 'updates'],
)
class NotificationsProducer:
    """
    To enable sending notifications add 'notification_topics' field to 'rpc_service' decorator
    as above.

    In this example NotificationsProducer will register for publishing to 2 channels:
      - 'notification.service.notifications_producer.errors'
      - 'notification.service.notifications_producer.updates'

    To send notification from method (does not need to be rpc_method) use:
        await self.notify.<topic_name>(<contents>)
    as in examples below
    """
    @rpc_method()
    async def do_stuff_and_notify(self, *args):
        logging.debug("NotifcationsProducer: Doing stuff...")
        await asyncio.sleep(0.5)
        msg = {'msg': "Stuff got updated"}
        await self.notify.updates(msg=msg)
        msg = {'msg': "Got some errors"}
        await self.notify.errors(msg)
        logging.debug("NotifcationsProducer: Doing stuff...")
        return "Stuff done"

    @rpc_method()
    async def do_more_stuff_and_notify(self, *args):
        logging.debug("NotifcationsProducer: Doing even more stuff...")
        for i in range(5):
            await asyncio.sleep(0.5)
            msg = {'msg': "Stuff {} got updated".format(i)}
            await self.notify.updates(msg=msg)

        logging.debug("NotifcationsProducer: Even more stuff done...")
        return "Even more stuff done"


async def main(loop):
    await asyncio.sleep(1)
    nc = NatsClient()
    await nc.connect(io_loop=loop, servers=[NATS_URI], verbose=True)
    remote = RemoteService(name='notifications_producer', version='1.0', nc=nc)
    logging.debug("main: calling remote procedure")
    try:
        print(await remote.do_stuff_and_notify())
        print(await remote.do_more_stuff_and_notify())
    except MiteDRPCError as err:
        logging.error(err)

    logging.debug("main: exiting")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    service = NotificationsProducer()
    loop = asyncio.get_event_loop()
    task = loop.create_task(main(loop))

    try:
        logging.info("Starting NotificationsProducer")
        service.start()
    except KeyboardInterrupt:
        logging.info("Stopping NotificationsProducer")
        service.stop()
