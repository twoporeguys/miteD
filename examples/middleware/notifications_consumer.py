import logging

from miteD.middleware.api import api
from miteD import notification_handler


@api(
    name='middleware-consumes-notifications',
    versions=['1.0'],
    broker_urls=['nats://127.0.0.1:4222']
)
class MiddlewareConsumesNotifications:
    @notification_handler(
        layer='middleware',
        producer='middleware-produces-notifications',
        topic='updates',
    )
    def updates_handler(self, channel, msg):
        logging.info("updates_handler: got channel/msg = {}/{}".format(channel, msg))

    @notification_handler(
        layer='service',
        producer='notifications_producer',
        topic='errors',
    )
    def errors_handler(self, channel, msg):
        logging.info("errors_handler: got channel/msg = {}/{}".format(channel, msg))


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)
    test = MiddlewareConsumesNotifications()
    try:
        test.start()
    except KeyboardInterrupt:
        test.stop()
