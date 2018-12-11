from unittest import TestCase
from miteD.service.service import rpc_service, rpc_method
from miteD.exception.inconsistent_version_exception import InconsistentVersionException


class RpcServiceTest(TestCase):
    def test_should_return_a_wrapped_object(self):
        @rpc_service(name="foo", versions=["1", "2"])
        class Foo:
            pass

        instance = Foo()

        self.assertIsInstance(instance, Foo)
        self.assertTrue(hasattr(instance, "_layer"))
        self.assertEqual(instance._layer, "service")

    def test_should_have_default_endpoints(self):
        @rpc_service(name="foo", versions=["1", "2"])
        class Foo:
            pass

        instance = Foo()

        self.assertTrue(hasattr(instance, "endpoints"))
        self.assertIn("*", instance.endpoints)
        self.assertEqual(instance.endpoints["*"], {})

    def test_should_add_declared_endpoint(self):
        @rpc_service(name="foo", versions=["1", "2"])
        class Foo:
            @rpc_method("bar")
            def bar(self):
                pass

        instance = Foo()

        self.assertIn("bar", instance.endpoints["*"])

    def test_should_not_create_non_default_version(self):
        @rpc_service(name="foo", versions=["1", "2"])
        class Foo:
            @rpc_method("bar")
            def bar(self):
                pass

        instance = Foo()

        self.assertEqual(len(instance.endpoints), 1)
        self.assertEqual(list(instance.endpoints.keys()), ["*"])

    def test_should_create_specific_version(self):
        @rpc_service(name="foo", versions=["1", "2"])
        class Foo:
            @rpc_method("bar", versions=["1"])
            def bar(self):
                pass

        instance = Foo()

        self.assertEqual(len(instance.endpoints), 2)
        self.assertEqual(list(instance.endpoints.keys()), ["*", "1"])

    def test_should_only_register_to_specific_version(self):
        @rpc_service(name="foo", versions=["1", "2"])
        class Foo:
            @rpc_method("bar", versions=["1"])
            def bar(self):
                pass

        instance = Foo()

        self.assertIn("bar", instance.endpoints["1"])
        self.assertNotIn("bar", instance.endpoints["*"])

    def test_should_not_allow_inconsistent_versions(self):
        @rpc_service(name="foo", versions=["1", "2"])
        class Foo:
            @rpc_method("bar", versions=["3"])
            def bar(self):
                pass

        with self.assertRaises(InconsistentVersionException):
            Foo()
