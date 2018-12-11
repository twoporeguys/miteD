import asyncio
from unittest import TestCase

from json import dumps
from nats.aio.errors import ErrTimeout

from miteD.service.client import RemoteService, MethodProxy
from miteD.service.errors import MiteDRPCError


class RemoteServiceTest(TestCase):
    def test_should_return_a_MethodProxy(self):
        service = RemoteService("foo", "1.0", None)

        method = service.bar

        self.assertIsInstance(method, MethodProxy)
        self.assertTrue(callable(method))


class MethodProxyTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.get_event_loop()

    @classmethod
    def tearDownClass(cls):
        cls.loop.close()

    def test_should_send_request_on_bus(self):
        nc_mock = NCMock(ReplyMock({}))
        proxy = MethodProxy(nc_mock, "foo.bar.baz")

        self.loop.run_until_complete(proxy())

        self.assertEqual(nc_mock.path, "foo.bar.baz")

    def test_should_return_reply_body(self):
        nc_mock = NCMock(ReplyMock({"foo": "bar"}))
        proxy = MethodProxy(nc_mock, "baz.1.qux")

        result = self.loop.run_until_complete(proxy())

        self.assertEqual(result, {"foo": "bar"})

    def test_should_raise_MiteDRPCError_504_on_timeout(self):
        def timeout():
            raise ErrTimeout()
        nc_mock = NCMock(timeout)
        proxy = MethodProxy(nc_mock, "baz.1.qux")

        with self.assertRaises(MiteDRPCError) as context_manager:
            self.loop.run_until_complete(proxy())

        self.assertEqual(context_manager.exception.status, 504)
        self.assertEqual(context_manager.exception.message, 'Call timeout for: "baz.1.qux"')

    def test_should_forward_MiteDRPCError(self):
        def errors():
            raise MiteDRPCError({"status": 123, "body": "FOO"})
        nc_mock = NCMock(errors)
        proxy = MethodProxy(nc_mock, "baz.1.qux")

        with self.assertRaises(MiteDRPCError) as context_manager:
            self.loop.run_until_complete(proxy())

        self.assertEqual(context_manager.exception.status, 123)
        self.assertEqual(context_manager.exception.message, "FOO")

    def test_should_raise_MiteDRPCError_with_non_200_replies(self):
        nc_mock = NCMock(ReplyMock("FOO", 400))
        proxy = MethodProxy(nc_mock, "baz.1.qux")

        with self.assertRaises(MiteDRPCError) as context_manager:
            self.loop.run_until_complete(proxy())

        self.assertEqual(context_manager.exception.status, 400)
        self.assertEqual(context_manager.exception.message, "FOO")


class NCMock:
    path = None
    args = None
    timeout = None

    def __init__(self, default_answer):
        self._default_answer = default_answer if callable(default_answer) else lambda *args: default_answer

    async def timed_request(self, path, args, timeout=0):
        self.path = path
        self.args = args
        self.timeout = timeout
        return self._default_answer()


class ReplyMock:
    def __init__(self, data, status=200):
        self.data = dumps({"body": data, "status": status}).encode()
