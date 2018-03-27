def _add_route(fn, method, path, name, versions):
    fn.__api_path__ = path
    fn.__api_method__ = method
    fn.__api_name__ = name or path
    fn.__api_versions__ = versions or ['*']
    return fn


def get(path, versions=None, name=None):
    def wrapper(fn):
        return _add_route(fn, 'GET', path, name, versions)

    return wrapper


def post(path, versions=None, name=None):
    def wrapper(fn):
        return _add_route(fn, 'POST', path, name, versions)

    return wrapper


def put(path, versions=None, name=None):
    def wrapper(fn):
        return _add_route(fn, 'PUT', path, name, versions)

    return wrapper


def delete(path, versions=None, name=None):
    def wrapper(fn):
        return _add_route(fn, 'DELETE', path, name, versions)

    return wrapper
