from sanic import response


def json(fn):
    fn.__response_type__ = response.json
    return fn


def text(fn):
    fn.__response_type__ = response.text
    return fn


def raw(fn):
    fn.__response_type__ = response.raw
    return fn


def html(fn):
    fn.__response_type__ = response.html
    return fn

