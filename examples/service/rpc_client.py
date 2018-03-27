import asyncio
from miteD.service.client import RemoteService
from contextlib import suppress


async def main(_loop):
    client_1_0 = RemoteService(name='test', version='1.0', loop=_loop)
    client_1_1 = RemoteService(name='test', version='1.1', loop=_loop)
    client_2_0 = RemoteService(name='test', version='2.0', loop=_loop)
    print(await client_1_0.ping())
    print(await client_1_0.ping())
    print(await client_2_0.ping())
    print(await client_1_1.ping())
    print(await client_2_0.hello('world'))
    print(await client_2_0.add(12, 54))

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    pending = asyncio.Task.all_tasks(loop)
    for task in pending:
        task.cancel()
        with suppress(asyncio.CancelledError):
            loop.run_until_complete(task)
    loop.close()
