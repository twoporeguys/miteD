import asyncio
import json
from functools import wraps, partial

from ..utils import get_members_if


def is_notification_handler(method):
    return getattr(method, '__is_notification_handler__', False)


def notification_handler(layer='*', producer='*', topic='*'):
    def wrapper(fn):
        fn.__is_notification_handler__ = True
        fn.__notification_layer__ = layer
        fn.__notification_producer__ = producer
        fn.__notification_topic__ = topic

        @wraps(fn)
        async def translate(self, msg):
            subject = msg.subject
            data = json.loads(msg.data.decode())
            if asyncio.iscoroutinefunction(fn):
                return await fn(self, subject, data)
            else:
                return fn(self, subject, data)

        return translate
    return wrapper


class Notify():
    pass

class NotificationsMixin(object):
    async def _start_notification_handlers(self):
        coros = []
        for h in self.notification_handlers:
            subject, queue = self._get_notification_subject_and_queue(h)
            self._logger.info("Starting notifications handler '{}' for subject/queue: '{}'/'{}'".format(
                h.__name__, subject, queue
            ))
            coros.append(self._nc.subscribe(subject, queue=queue, cb=h))
        await asyncio.gather(*coros)

    def get_notification_handlers(self, cls):
        wrapped = cls()
        return get_members_if(is_notification_handler, wrapped)

    def _get_notification_subject_and_queue(self, handler):
        subject = 'notification.{}.{}.{}'.format(
            handler.__notification_layer__,
            handler.__notification_producer__,
            handler.__notification_topic__,
        )
        queue = '{}.{}'.format(
            subject,
            self._name
        )
        return subject, queue

    async def _send_notification(self, subject, msg):
        await self._nc.publish(subject, json.dumps(msg).encode())

    def _add_notify(self, cls):
        if not self._notification_topics:
            return
        notify = Notify()
        for topic, subject in self._get_notification_topic_and_subject_pairs():
            self._logger.info("Registering notifications topic/subject: '{}'/'{}'".format(topic, subject))
            setattr(notify, topic, partial(self._send_notification, subject))
        cls.notify = notify

    def _get_notification_topic_and_subject_pairs(self):
        res = []
        subject_stem = 'notification.{}.{}'.format(self._layer, self._name)
        for topic in self._notification_topics:
            res.append((topic, '{}.{}'.format(subject_stem, topic)))
        return res
