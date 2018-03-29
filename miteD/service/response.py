from http import HTTPStatus


def _build_response(status, body):
    return {'status': status, 'body': body}


def _build_error(status):
    return _build_response(status.value, status.phrase)


def ok(reply=None):
    return _build_response(HTTPStatus.OK, reply)


def bad_request(*args):
    return _build_error(HTTPStatus.BAD_REQUEST)


def method_not_allowed(*args):
    return _build_error(HTTPStatus.METHOD_NOT_ALLOWED)


def not_found(*args):
    return _build_error(HTTPStatus.NOT_FOUND)


def internal_server_error(*args):
    return _build_error(HTTPStatus.INTERNAL_SERVER_ERROR)
