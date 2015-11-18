from unittest import TestCase
from conductr_cli import bundle_shorthand
from conductr_cli.exceptions import MalformedBundleUriError


class TestParse(TestCase):
    def test_full_address(self):
        uri = 'urn:x-bundle:typesafe/bundle/reactive-maps-frontend:v1-023f9da22'
        expected_result = ('urn:x-bundle:',
                           'typesafe', 'bundle', 'reactive-maps-frontend',
                           'v1', '023f9da22')
        result = bundle_shorthand.parse(uri)
        self.assertEqual(expected_result, result)

    def test_no_urn(self):
        uri = 'typesafe/bundle/reactive-maps-frontend:v1-023f9da22'
        expected_result = ('urn:x-bundle:',
                           'typesafe', 'bundle', 'reactive-maps-frontend',
                           'v1', '023f9da22')
        result = bundle_shorthand.parse(uri)
        self.assertEqual(expected_result, result)

    def test_no_org(self):
        uri = 'bundle/reactive-maps-frontend:v1-023f9da22'
        expected_result = ('urn:x-bundle:',
                           'typesafe', 'bundle', 'reactive-maps-frontend',
                           'v1', '023f9da22')
        result = bundle_shorthand.parse(uri)
        self.assertEqual(expected_result, result)

    def test_no_repos(self):
        uri = 'reactive-maps-frontend:v1-023f9da22'
        expected_result = ('urn:x-bundle:',
                           'typesafe', 'bundle', 'reactive-maps-frontend',
                           'v1', '023f9da22')
        result = bundle_shorthand.parse(uri)
        self.assertEqual(expected_result, result)

    def test_no_digest(self):
        uri = 'reactive-maps-frontend:v1'
        expected_result = ('urn:x-bundle:', 'typesafe', 'bundle', 'reactive-maps-frontend', 'v1', None)
        result = bundle_shorthand.parse(uri)
        self.assertEqual(expected_result, result)

    def test_bundle_name_only(self):
        uri = 'reactive-maps-frontend'
        expected_result = ('urn:x-bundle:', 'typesafe', 'bundle', 'reactive-maps-frontend', None, None)
        result = bundle_shorthand.parse(uri)
        self.assertEqual(expected_result, result)


class TestParseWithMalformedExpression(TestCase):
    def test_unsupported_urn(self):
        uri = 'urn:x-bananas:typesafe/bundle/reactive-maps-frontend:v1-023f9da22'
        self.assertRaises(MalformedBundleUriError, bundle_shorthand.parse, uri)

    def test_invalid_parts(self):
        uri = 'urn:x-bundle:typesafe/bundle/this/is/not/a/valid/path/reactive-maps-frontend:v1-023f9da22'
        self.assertRaises(MalformedBundleUriError, bundle_shorthand.parse, uri)

    def test_file_path_should_be_invalid(self):
        uri = '/home/user/workspace/my-project/target/bundle/my-project-v1-023f9da22.zip'
        self.assertRaises(MalformedBundleUriError, bundle_shorthand.parse, uri)

    def test_http_url_should_be_invalid(self):
        uri = 'http://some-url.com/dist/bundle/my-project-v1-023f9da22.zip'
        self.assertRaises(MalformedBundleUriError, bundle_shorthand.parse, uri)
