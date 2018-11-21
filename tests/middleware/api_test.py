import unittest
from miteD.middleware.api import api
from miteD.service.client import RemoteService


class ApiTest(unittest.TestCase):
    def test_should_return_a_wrapped_class(self):
        @api(name="foo", versions=["1.0"])
        class Foo:
            pass

        instance = Foo()

        self.assertIsInstance(instance, Foo)
        self.assertTrue(hasattr(instance, "_layer"))

    def test_should_have_a_get_remote_service_method(self):
        @api(name="foo", versions=["1.0"])
        class Foo:
            pass

        instance = Foo()

        self.assertTrue(hasattr(instance, "get_remote_service"))
        self.assertTrue(callable(instance.get_remote_service))

    def test_should_return_a_RemoteService_instance(self):
        @api(name="foo", versions=["1.0"])
        class Foo:
            pass

        instance = Foo()
        remote_service = instance.get_remote_service("bar", "42")

        self.assertIsInstance(remote_service, RemoteService)

