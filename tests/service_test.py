import asyncio
import json
from unittest import TestCase
from unittest.mock import MagicMock, call as themagiccall
from nats.aio.client import Client as NATS

from miteD.service.service import rpc_service, rpc_method


class ServiceTest(TestCase):
    def test_given_a_small_amount_of_data_when_calling_method_it_should_return_all_data(self):
        TEST_STRING = "FOO BAR BAZ"
        nats_mock = NATS()
        nats_mock.publish = async_mock()
        @rpc_service(name='foo', versions=['1.0'])
        class Service:
            @rpc_method()
            async def my_method(self):
                return TEST_STRING
        service = Service(nats_mock)
        loop = asyncio.get_event_loop()

        loop.run_until_complete(service.handle_message(FakeMessage('rpc.service.foo.1_0.my_method')))
        call_list = [
            themagiccall('foo', json.dumps({"status": 200, "body": json.dumps(TEST_STRING)}).encode()),
            themagiccall('foo', json.dumps({"status": 200, "body": ""}).encode())
        ]
        nats_mock.publish.mock.assert_has_calls(call_list)

    def test_sending_small_amount_of_data_and_receiving_it_in_chunking_followed_by_large_data_sending_and_receiving_in_chunks(self):
        TEST_STRING = "FOO BAR BAR" * 65536
        SERIALIZED_TEST_STRING = json.dumps(TEST_STRING)
        nats_mock = NATS()
        nats_mock.publish = async_mock()
        chunk_len = 5

        @rpc_service(name='foo', versions=['1.0'], chunking_size=chunk_len)
        class Service:
            @rpc_method()
            async def my_method(self):
                return TEST_STRING

        service = Service(nats_mock)
        loop = asyncio.get_event_loop()

        loop.run_until_complete(service.handle_message(FakeMessage('rpc.service.foo.1_0.my_method')))

        call_list = []
        while SERIALIZED_TEST_STRING:
            call_list.append(themagiccall('foo', json.dumps({"status": 200, "body": SERIALIZED_TEST_STRING[:chunk_len]}).encode()))
            SERIALIZED_TEST_STRING = SERIALIZED_TEST_STRING[chunk_len:]
        call_list.append(themagiccall('foo', json.dumps({"status": 200, "body": ""}).encode()))
        nats_mock.publish.mock.assert_has_calls(call_list)


class FakeMessage:
    def __init__(self, subject):
        self.subject = subject
        self.data = '{}'.encode()
        self.reply = 'foo'

def async_mock(*args, **kwargs):
    m = MagicMock(*args, **kwargs)
    async def mock_coro(*args, **kwargs):
        return m(*args, **kwargs)
    mock_coro.mock = m
    return mock_coro
