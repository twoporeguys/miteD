import logging

from miteD.service.service import rpc_service, notification_handler


@rpc_service(
    name='notifications_consumer',
    versions=['1.0'],
    broker_urls=['nats://127.0.0.1:4222'],
)
class NotificationsConsumer:
    """
    To define notifications handler use 'notification_handler' decorator as in examples below.
    """

    """
    Listen on channel "notification.service.notifications_producer.1_0.updates"
    """
    @notification_handler(
        layer='service',
        name='notifications_producer',
        versions=['1.0'],
        topic='updates',
    )
    async def updates_handler(self, channel, msg):
        logging.debug("updates_handler: got notification from channel: {} msg = '{}'".format(channel, msg))
        raise RuntimeError('dddup')

    """
    Listen on channel "notification.service.notifications_producer.1_0.errors"
    """
    @notification_handler(
        layer='service',
        name='notifications_producer',
        versions=['1.0'],
        topic='errors',
    )
    async def errors_handler(self, channel, msg):
        logging.debug("errors_handler: got notification from channel: {} msg = '{}'".format(channel, msg))

    """
    Wildcard subscription
    Listen on channel "notification.*.*.*.errors"
    """
    @notification_handler(
        layer='*',
        name='*',
        versions=['*'],
        topic='updates',
    )
    async def wildcard_handler(self, channel, msg):
        logging.debug("wildcard_updates_handler: got notification from channel: {} msg = '{}'".format(channel, msg))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    service = NotificationsConsumer()

    try:
        logging.info("Starting NotificationsConsumer")
        service.start()
    except KeyboardInterrupt:
        logging.info("Stopping NotificationsConsumer")
        service.stop()
