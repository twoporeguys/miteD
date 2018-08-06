import asyncio
from miteD.service.client import RemoteService
from contextlib import suppress
from nats.aio.client import Client as NatsClient


async def main(loop):
    nc = NatsClient()
    await nc.connect(io_loop=loop, servers=['nats://127.0.0.1:4222'], verbose=True)
    client_1_0 = RemoteService(name='test', version='1.0', nc=nc)
    client_1_1 = RemoteService(name='test', version='1.1', nc=nc)
    client_2_0 = RemoteService(name='test', version='2.0', nc=nc)
    print(await client_1_0.ping())
    print(await client_1_1.ping())
    print(await client_2_0.ping())
    print(await client_2_0.hello('world'))
    print(await client_2_0.add(12, 54))

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    group = asyncio.gather(*asyncio.Task.all_tasks(), return_exceptions=True)
    group.cancel()
    loop.run_until_complete(group)
    loop.close()
