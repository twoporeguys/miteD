import asyncio
import json
from unittest import TestCase
from unittest.mock import MagicMock
from nats.aio.client import Client as NATS
from miteD.service.client import RemoteService
from miteD.service.errors import MiteDRPCError


class ServiceClientTest(TestCase):
    def test_call_to_server_with_no_reply_triggers_timeout(self):
        loop = asyncio.get_event_loop()
        nats_mock = NATS()
        nats_mock.subscribe = async_mock()
        nats_mock.publish_request = async_mock()
        nats_mock.unsubscribe = async_mock()
        remote_service = RemoteService('foo', '1.0', nats_mock)

        with self.assertRaises(MiteDRPCError) as context:
            loop.run_until_complete(remote_service.get_all_data())
            self.assertEqual(504, context.exception.status)
            nats_mock.publish_request.mock.assert_called_once()
            nats_mock.subscribe.mock.assert_called_once()
            nats_mock.unsubscribe.mock.assert_called_once()


    def test_multiple_calls_to_server_with_large_data_blocks(self):
        loop = asyncio.get_event_loop()
        expected_result = {'name': 'Suraj', 'surname': 'Ravichandran'}
        nats_mock = NATS()
        nats_mock.publish_request = async_mock()
        nats_mock.unsubscribe = async_mock()

        callback_future = asyncio.Future()
        async def dummy_subscribe(*_, **kwargs):
            nonlocal callback_future
            callback_future.set_result(kwargs['cb'])

        nats_mock.subscribe = dummy_subscribe

        async def first_send_to_callback():
            callback = await asyncio.wait_for(callback_future, 1)
            await callback(FakeResponse(json.dumps('FOOOO')))
            await callback(FakeResponse(''))


        async def send_to_callback():
            chunk_size = 5
            serialized_result = json.dumps(expected_result)
            callback = await asyncio.wait_for(callback_future, 1)
            while serialized_result[:chunk_size]:
                await callback(FakeResponse(serialized_result[:chunk_size]))
                serialized_result = serialized_result[chunk_size:]
            await callback(FakeResponse(''))

        remote_service = RemoteService('foo', '1.0', nats_mock)
        loop.run_until_complete(asyncio.gather(remote_service.get_all_data(), first_send_to_callback()))
        callback_future = asyncio.Future()
        results = loop.run_until_complete(asyncio.gather(remote_service.get_all_data(), send_to_callback()))
        self.assertEqual(expected_result, results[0])



class FakeResponse:
    def __init__(self, data):
        self.data = json.dumps({'status': 200, 'body': data}).encode()

def async_mock(*args, **kwargs):
    m = MagicMock(*args, **kwargs)
    async def mock_coro(*args, **kwargs):
        return m(*args, **kwargs)
    mock_coro.mock = m
    return mock_coro
