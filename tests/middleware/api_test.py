from unittest import TestCase
from miteD.middleware.api import api
from miteD.exception.inconsistent_version_exception import InconsistentVersionException
from miteD.middleware.methods import get
from miteD.service.client import RemoteService


class ApiTest(TestCase):
    def test_should_return_a_wrapped_object(self):
        @api(name="foo", versions=["1.0"])
        class Foo:
            pass

        instance = Foo()

        self.assertIsInstance(instance, Foo)
        self.assertTrue(hasattr(instance, "_layer"))
        self.assertEqual(instance._layer, "middleware")

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

    def test_should_have_default_endpoints(self):
        @api(name="foo", versions=["1.0"], broker_urls=[])
        class Foo:
            pass

        instance = Foo()

        self.assertTrue(hasattr(instance, "endpoints"))
        self.assertIn("*", instance.endpoints)
        self.assertEqual(instance.endpoints["*"], {})

    def test_should_add_declared_endpoint(self):
        @api(name="foo", versions=["1.0"], broker_urls=[])
        class Foo:
            @get("/bar")
            def bar(self):
                pass

        instance = Foo()

        self.assertIn("/bar", instance.endpoints["*"])
        self.assertIn("GET", instance.endpoints["*"]["/bar"])

    def test_should_not_create_non_default_version(self):
        @api(name="foo", versions=["1.0"], broker_urls=[])
        class Foo:
            @get("/bar")
            def bar(self):
                pass

        instance = Foo()

        self.assertEqual(len(instance.endpoints), 1)
        self.assertEqual(list(instance.endpoints.keys()), ["*"])

    def test_should_create_specific_version(self):
        @api(name="foo", versions=["1.0"], broker_urls=[])
        class Foo:
            @get("/bar", versions=["1.0"])
            def bar(self):
                pass

        instance = Foo()

        self.assertEqual(len(instance.endpoints), 2)
        self.assertEqual(list(instance.endpoints.keys()), ["*", "1.0"])

    def test_should_only_register_to_specific_version(self):
        @api(name="foo", versions=["1.0"], broker_urls=[])
        class Foo:
            @get("/bar", versions=["1.0"])
            def bar(self):
                pass

        instance = Foo()

        self.assertIn("/bar", instance.endpoints["1.0"])
        self.assertNotIn("/bar", instance.endpoints["*"])

    def test_should_not_allow_inconsistent_versions(self):
        @api(name="foo", versions=["1.0"], broker_urls=[])
        class Foo:
            @get("/bar", versions=["1.1"])
            def bar(self):
                pass

        with self.assertRaises(InconsistentVersionException):
            Foo()

