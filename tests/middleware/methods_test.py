from unittest import TestCase
from miteD.middleware import methods


class GETTest(TestCase):
    def test_should_flag_as_api_method(self):
        @methods.get("")
        def foo():
            pass

        self.assertTrue(foo.__is_api_method__)

    def test_should_set_api_path(self):
        @methods.get("/my-foo")
        def foo():
            pass

        self.assertEqual(foo.__api_path__, "/my-foo")

    def test_should_set_api_method_to_GET(self):
        @methods.get("")
        def foo():
            pass

        self.assertEqual(foo.__api_method__, "GET")

    def test_should_set_api_name(self):
        @methods.get("", name="bar")
        def foo():
            pass

        self.assertEqual(foo.__api_name__, "bar")

    def test_should_default_api_name_to_path(self):
        @methods.get("baz")
        def foo():
            pass

        self.assertEqual(foo.__api_name__, "baz")

    def test_should_set_api_versions(self):
        @methods.get("", versions=["1", "2"])
        def foo():
            pass

        self.assertEqual(foo.__api_versions__, ["1", "2"])

    def test_should_default_api_versions_to_star(self):
        @methods.get("")
        def foo():
            pass

        self.assertEqual(foo.__api_versions__, ["*"])


class POSTTest(TestCase):
    def test_should_flag_as_api_method(self):
        @methods.post("")
        def foo():
            pass

        self.assertTrue(foo.__is_api_method__)

    def test_should_set_api_path(self):
        @methods.post("/my-foo")
        def foo():
            pass

        self.assertEqual(foo.__api_path__, "/my-foo")

    def test_should_set_api_method_to_POST(self):
        @methods.post("")
        def foo():
            pass

        self.assertEqual(foo.__api_method__, "POST")

    def test_should_set_api_name(self):
        @methods.post("", name="bar")
        def foo():
            pass

        self.assertEqual(foo.__api_name__, "bar")

    def test_should_default_api_name_to_path(self):
        @methods.post("baz")
        def foo():
            pass

        self.assertEqual(foo.__api_name__, "baz")

    def test_should_set_api_versions(self):
        @methods.post("", versions=["1", "2"])
        def foo():
            pass

        self.assertEqual(foo.__api_versions__, ["1", "2"])

    def test_should_default_api_versions_to_star(self):
        @methods.post("")
        def foo():
            pass

        self.assertEqual(foo.__api_versions__, ["*"])


class PUTTest(TestCase):
    def test_should_flag_as_api_method(self):
        @methods.put("")
        def foo():
            pass

        self.assertTrue(foo.__is_api_method__)

    def test_should_set_api_path(self):
        @methods.put("/my-foo")
        def foo():
            pass

        self.assertEqual(foo.__api_path__, "/my-foo")

    def test_should_set_api_method_to_PUT(self):
        @methods.put("")
        def foo():
            pass

        self.assertEqual(foo.__api_method__, "PUT")

    def test_should_set_api_name(self):
        @methods.put("", name="bar")
        def foo():
            pass

        self.assertEqual(foo.__api_name__, "bar")

    def test_should_default_api_name_to_path(self):
        @methods.put("baz")
        def foo():
            pass

        self.assertEqual(foo.__api_name__, "baz")

    def test_should_set_api_versions(self):
        @methods.put("", versions=["1", "2"])
        def foo():
            pass

        self.assertEqual(foo.__api_versions__, ["1", "2"])

    def test_should_default_api_versions_to_star(self):
        @methods.put("")
        def foo():
            pass

        self.assertEqual(foo.__api_versions__, ["*"])


class DELETETest(TestCase):
    def test_should_flag_as_api_method(self):
        @methods.delete("")
        def foo():
            pass

        self.assertTrue(foo.__is_api_method__)

    def test_should_set_api_path(self):
        @methods.delete("/my-foo")
        def foo():
            pass

        self.assertEqual(foo.__api_path__, "/my-foo")

    def test_should_set_api_method_to_DELETE(self):
        @methods.delete("")
        def foo():
            pass

        self.assertEqual(foo.__api_method__, "DELETE")

    def test_should_set_api_name(self):
        @methods.delete("", name="bar")
        def foo():
            pass

        self.assertEqual(foo.__api_name__, "bar")

    def test_should_default_api_name_to_path(self):
        @methods.delete("baz")
        def foo():
            pass

        self.assertEqual(foo.__api_name__, "baz")

    def test_should_set_api_versions(self):
        @methods.delete("", versions=["1", "2"])
        def foo():
            pass

        self.assertEqual(foo.__api_versions__, ["1", "2"])

    def test_should_default_api_versions_to_star(self):
        @methods.delete("")
        def foo():
            pass

        self.assertEqual(foo.__api_versions__, ["*"])

