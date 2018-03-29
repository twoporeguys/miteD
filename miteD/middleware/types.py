from asyncio import iscoroutine

from sanic import response

from miteD.service.errors import MiteDRPCError


async def _build_response(result):
    try:
        if isinstance(result, tuple):
            body = iscoroutine(result[0]) and await result[0] or result[0]
            rest = result[1:]
        else:
            body = iscoroutine(result) and await result or result
            rest = ()
        return body, rest
    except MiteDRPCError as err:
        return err.message, (err.status,)


def json(fn):
    async def wrapper(*args, **kwargs):
        body, rest = await _build_response(fn(*args, **kwargs))
        return response.json(*(body, *rest))

    return wrapper


def text(fn):
    async def wrapper(*args, **kwargs):
        body, rest = await _build_response(fn(*args, **kwargs))
        return response.text(*(body, *rest))

    return wrapper


def raw(fn):
    async def wrapper(*args, **kwargs):
        body, rest = await _build_response(fn(*args, **kwargs))
        return response.raw(*(body, *rest))

    return wrapper
