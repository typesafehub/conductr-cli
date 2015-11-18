from unittest import TestCase
from conductr_cli.exceptions import BundleResolutionError
from conductr_cli import resolver
from conductr_cli.resolvers import bintray_resolver, uri_resolver

try:
    from unittest.mock import patch, MagicMock, Mock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock, Mock


class TestResolver(TestCase):
    def test_resolver_chain(self):
        expected_resolver_chain = [uri_resolver, bintray_resolver]
        self.assertEqual(expected_resolver_chain, resolver.all_resolvers())

    def test_resolve_bundle_success(self):
        first_resolver_mock = Mock()
        first_resolver_mock.load_from_cache = MagicMock(return_value=(False, None, None))
        first_resolver_mock.resolve_bundle = MagicMock(return_value=(False, None, None))

        second_resolver_mock = Mock()
        second_resolver_mock.load_from_cache = MagicMock(return_value=(False, None, None))
        second_resolver_mock.resolve_bundle = MagicMock(return_value=(True, 'bundle_name', 'mock bundle_file'))

        all_resolvers_mock = MagicMock(return_value=[first_resolver_mock, second_resolver_mock])

        with patch('conductr_cli.resolver.all_resolvers', all_resolvers_mock):
            bundle_name, bundle_file = resolver.resolve_bundle('/some-cache-dir', '/some-bundle-path')
            self.assertEqual('bundle_name', bundle_name)
            self.assertEqual('mock bundle_file', bundle_file)

        first_resolver_mock.load_from_cache('/some-cache-dir', '/some-bundle-path')
        first_resolver_mock.resolve_bundle.assert_called_with('/some-cache-dir', '/some-bundle-path')

        second_resolver_mock.load_from_cache('/some-cache-dir', '/some-bundle-path')
        second_resolver_mock.resolve_bundle.assert_called_with('/some-cache-dir', '/some-bundle-path')

    def test_resolve_bundle_failure(self):
        first_resolver_mock = Mock()
        first_resolver_mock.load_from_cache = MagicMock(return_value=(False, None, None))
        first_resolver_mock.resolve_bundle = MagicMock(return_value=(False, None, None))

        all_resolvers_mock = MagicMock(return_value=[first_resolver_mock])
        with patch('conductr_cli.resolver.all_resolvers', all_resolvers_mock):
            self.assertRaises(BundleResolutionError, resolver.resolve_bundle, '/some-cache-dir', '/some-bundle-path')

        first_resolver_mock.load_from_cache('/some-cache-dir', '/some-bundle-path')
        first_resolver_mock.resolve_bundle.assert_called_with('/some-cache-dir', '/some-bundle-path')

    def test_resolve_bundle_from_cache(self):
        first_resolver_mock = Mock()
        first_resolver_mock.load_from_cache = MagicMock(return_value=(True, 'bundle_name', 'mock bundle_file'))

        all_resolvers_mock = MagicMock(return_value=[first_resolver_mock])
        with patch('conductr_cli.resolver.all_resolvers', all_resolvers_mock):
            bundle_name, bundle_file = resolver.resolve_bundle('/some-cache-dir', '/some-bundle-path')
            self.assertEqual('bundle_name', bundle_name)
            self.assertEqual('mock bundle_file', bundle_file)

        first_resolver_mock.load_from_cache('/some-cache-dir', '/some-bundle-path')
