import logging

from miteD.service.service import rpc_service, notification_handler

"""
When multiple replicas of a service exist each notification should be propagated to single intance only.
To showcase that behavior run multiple instances of this script and then run the producer.
Logs for each instance of NotificationsConsumerTypeA will be distinguished by object id: Consumer-TypeA-<id>
"""

@rpc_service(
    name='notifications_consumer_type_A',
    versions=['1.0'],
    broker_urls=['nats://127.0.0.1:4222'],
)
class NotificationsConsumerTypeA:
    """
    Listen on channel "notification.service.notifications_producer.updates"
    """
    @notification_handler(
        layer='service',
        producer='notifications_producer',
        topic='updates',
    )
    async def updates_handler(self, channel, msg):
        logging.debug("Consumer-TypeA-{}: updates_handler: got notification from channel: {} msg = '{}'".format(
            id(self),
            channel,
            msg,
        ))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    service = NotificationsConsumerTypeA()

    try:
        logging.info("Starting consumer")
        service.start()
    except KeyboardInterrupt:
        logging.info("Stopping consumer")
        service.stop()
