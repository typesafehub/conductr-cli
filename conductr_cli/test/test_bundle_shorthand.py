from unittest import TestCase
from conductr_cli import bundle_shorthand
from conductr_cli.exceptions import MalformedBundleUriError


class TestParseBundle(TestCase):
    def test_full_address(self):
        uri = 'urn:x-bundle:typesafe/bundle/reactive-maps-frontend:1.0.0-023f9da22'
        expected_result = ('urn:x-bundle:',
                           'typesafe', 'bundle', 'reactive-maps-frontend',
                           '1.0.0', '023f9da22')
        result = bundle_shorthand.parse_bundle(uri)
        self.assertEqual(expected_result, result)

    def test_no_urn(self):
        uri = 'typesafe/bundle/reactive-maps-frontend:1.0.0-023f9da22'
        expected_result = ('urn:x-bundle:',
                           'typesafe', 'bundle', 'reactive-maps-frontend',
                           '1.0.0', '023f9da22')
        result = bundle_shorthand.parse_bundle(uri)
        self.assertEqual(expected_result, result)

    def test_no_org(self):
        uri = 'bundle/reactive-maps-frontend:1.0.0-023f9da22'
        expected_result = ('urn:x-bundle:',
                           'typesafe', 'bundle', 'reactive-maps-frontend',
                           '1.0.0', '023f9da22')
        result = bundle_shorthand.parse_bundle(uri)
        self.assertEqual(expected_result, result)

    def test_no_repos(self):
        uri = 'reactive-maps-frontend:1.0.0-023f9da22'
        expected_result = ('urn:x-bundle:',
                           'typesafe', 'bundle', 'reactive-maps-frontend',
                           '1.0.0', '023f9da22')
        result = bundle_shorthand.parse_bundle(uri)
        self.assertEqual(expected_result, result)

    def test_no_repos_and_tag_with_hyphens(self):
        uri = 'reactive-maps-frontend:my-tag-with-hyphens-023f9da22'
        expected_result = ('urn:x-bundle:',
                           'typesafe', 'bundle', 'reactive-maps-frontend',
                           'my-tag-with-hyphens', '023f9da22')
        result = bundle_shorthand.parse_bundle(uri)
        self.assertEqual(expected_result, result)

    def test_no_digest(self):
        uri = 'reactive-maps-frontend:1.0.0'
        expected_result = ('urn:x-bundle:', 'typesafe', 'bundle', 'reactive-maps-frontend', '1.0.0', None)
        result = bundle_shorthand.parse_bundle(uri)
        self.assertEqual(expected_result, result)

    def test_bundle_name_only(self):
        uri = 'reactive-maps-frontend'
        expected_result = ('urn:x-bundle:', 'typesafe', 'bundle', 'reactive-maps-frontend', None, None)
        result = bundle_shorthand.parse_bundle(uri)
        self.assertEqual(expected_result, result)


class TestParseBundleWithMalformedExpression(TestCase):
    def test_unsupported_urn(self):
        uri = 'urn:x-bananas:typesafe/bundle/reactive-maps-frontend:1.0.0-023f9da22'
        self.assertRaises(MalformedBundleUriError, bundle_shorthand.parse_bundle, uri)

    def test_invalid_parts(self):
        uri = 'urn:x-bundle:typesafe/bundle/this/is/not/a/valid/path/reactive-maps-frontend:1.0.0-023f9da22'
        self.assertRaises(MalformedBundleUriError, bundle_shorthand.parse_bundle, uri)

    def test_file_path_should_be_invalid(self):
        uri = '/home/user/workspace/my-project/target/bundle/my-project-1.0.0-023f9da22.zip'
        self.assertRaises(MalformedBundleUriError, bundle_shorthand.parse_bundle, uri)

    def test_http_url_should_be_invalid(self):
        uri = 'http://some-url.com/dist/bundle/my-project-1.0.0-023f9da22.zip'
        self.assertRaises(MalformedBundleUriError, bundle_shorthand.parse_bundle, uri)

    def test_empty_parts_should_be_invalid(self):
        uri = 'typesafe//conductr-haproxy-dev-mode:1.0.0-023f9da22'
        self.assertRaises(MalformedBundleUriError, bundle_shorthand.parse_bundle, uri)

    def test_empty_string_should_be_invalid(self):
        self.assertRaises(MalformedBundleUriError, bundle_shorthand.parse_bundle, '')
        self.assertRaises(MalformedBundleUriError, bundle_shorthand.parse_bundle, ' ')


class TestParseBundleConfiguration(TestCase):
    def test_full_address(self):
        uri = 'urn:x-bundle:typesafe/bundle-configuration/conductr-haproxy-dev-mode:1.0.0-023f9da22'
        expected_result = ('urn:x-bundle:',
                           'typesafe', 'bundle-configuration', 'conductr-haproxy-dev-mode',
                           '1.0.0', '023f9da22')
        result = bundle_shorthand.parse_bundle_configuration(uri)
        self.assertEqual(expected_result, result)

    def test_no_urn(self):
        uri = 'typesafe/bundle-configuration/conductr-haproxy-dev-mode:1.0.0-023f9da22'
        expected_result = ('urn:x-bundle:',
                           'typesafe', 'bundle-configuration', 'conductr-haproxy-dev-mode',
                           '1.0.0', '023f9da22')
        result = bundle_shorthand.parse_bundle_configuration(uri)
        self.assertEqual(expected_result, result)

    def test_no_org(self):
        uri = 'bundle-configuration/conductr-haproxy-dev-mode:1.0.0-023f9da22'
        expected_result = ('urn:x-bundle:',
                           'typesafe', 'bundle-configuration', 'conductr-haproxy-dev-mode',
                           '1.0.0', '023f9da22')
        result = bundle_shorthand.parse_bundle_configuration(uri)
        self.assertEqual(expected_result, result)

    def test_no_repos(self):
        uri = 'conductr-haproxy-dev-mode:1.0.0-023f9da22'
        expected_result = ('urn:x-bundle:',
                           'typesafe', 'bundle-configuration', 'conductr-haproxy-dev-mode',
                           '1.0.0', '023f9da22')
        result = bundle_shorthand.parse_bundle_configuration(uri)
        self.assertEqual(expected_result, result)

    def test_no_digest(self):
        uri = 'conductr-haproxy-dev-mode:1.0.0'
        expected_result = ('urn:x-bundle:', 'typesafe', 'bundle-configuration',
                           'conductr-haproxy-dev-mode', '1.0.0', None)
        result = bundle_shorthand.parse_bundle_configuration(uri)
        self.assertEqual(expected_result, result)

    def test_bundle_name_only(self):
        uri = 'conductr-haproxy-dev-mode'
        expected_result = ('urn:x-bundle:', 'typesafe', 'bundle-configuration', 'conductr-haproxy-dev-mode', None, None)
        result = bundle_shorthand.parse_bundle_configuration(uri)
        self.assertEqual(expected_result, result)


class TestParseBundleConfigurationWithMalformedExpression(TestCase):
    def test_unsupported_urn(self):
        uri = 'urn:x-bananas:typesafe/bundle-configuration/conductr-haproxy-dev-mode:1.0.0-023f9da22'
        self.assertRaises(MalformedBundleUriError, bundle_shorthand.parse_bundle_configuration, uri)

    def test_invalid_parts(self):
        uri = 'urn:x-bundle:typesafe/bundle-configuration/this/is/not/a/valid/path/conductr-haproxy-dev-mode:1.0.0-023f9da22'
        self.assertRaises(MalformedBundleUriError, bundle_shorthand.parse_bundle_configuration, uri)

    def test_file_path_should_be_invalid(self):
        uri = '/home/user/workspace/my-project/target/configuration/my-project-1.0.0-023f9da22.zip'
        self.assertRaises(MalformedBundleUriError, bundle_shorthand.parse_bundle_configuration, uri)

    def test_http_url_should_be_invalid(self):
        uri = 'http://some-url.com/dist/bundle-configuration/my-project-1.0.0-023f9da22.zip'
        self.assertRaises(MalformedBundleUriError, bundle_shorthand.parse_bundle_configuration, uri)

    def test_empty_parts_should_be_invalid(self):
        uri = 'typesafe//conductr-haproxy-dev-mode:1.0.0-023f9da22'
        self.assertRaises(MalformedBundleUriError, bundle_shorthand.parse_bundle_configuration, uri)

    def test_empty_string_should_be_invalid(self):
        self.assertRaises(MalformedBundleUriError, bundle_shorthand.parse_bundle_configuration, '')
        self.assertRaises(MalformedBundleUriError, bundle_shorthand.parse_bundle_configuration, '  ')
