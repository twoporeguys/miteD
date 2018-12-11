from unittest import TestCase
from miteD.middleware import types
from sanic import response


class JSONTest(TestCase):
    def test_should_set_response_type_to_json(self):
        @types.json
        def foo():
            pass

        self.assertEqual(foo.__response_type__, response.json)


class TEXTTest(TestCase):
    def test_should_set_response_type_to_text(self):
        @types.text
        def foo():
            pass

        self.assertEqual(foo.__response_type__, response.text)


class RAWTest(TestCase):
    def test_should_set_response_type_to_raw(self):
        @types.raw
        def foo():
            pass

        self.assertEqual(foo.__response_type__, response.raw)


class HTMLTest(TestCase):
    def test_should_set_response_type_to_html(self):
        @types.html
        def foo():
            pass

        self.assertEqual(foo.__response_type__, response.html)


class FILETest(TestCase):
    def test_should_set_response_type_to_file(self):
        @types.file
        def foo():
            pass

        self.assertEqual(foo.__response_type__, response.file)
