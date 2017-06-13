from unittest import TestCase
from unittest.mock import patch, MagicMock, Mock
from conductr_cli.test.cli_test_case import CliTestCase, as_warn, strip_margin, create_mock_logger
from conductr_cli.exceptions import BundleResolutionError, ContinuousDeliveryError
from conductr_cli import logging_setup, resolver
from conductr_cli.resolvers import bintray_resolver, docker_resolver, docker_offline_resolver, uri_resolver, \
    offline_resolver, stdin_resolver, s3_resolver
from conductr_cli.resolvers.schemes import SCHEME_HTTP, SCHEME_BUNDLE
from pyhocon import ConfigFactory


class TestResolver(CliTestCase):

    def test_resolve_bundle_success(self):
        custom_settings = Mock()

        first_resolver_mock = Mock(name='first_resolver')
        first_resolver_mock.__name__ = 'first_resolver'
        first_resolver_mock.load_bundle_from_cache = MagicMock(return_value=(False, None, None, None))
        first_resolver_mock.resolve_bundle = MagicMock(return_value=(False, None, None, None))
        first_resolver_mock.supported_schemes = MagicMock(return_value=[SCHEME_BUNDLE])

        second_resolver_mock = Mock(name='second_resolver')
        second_resolver_mock.__name__ = 'second_resolver'
        second_resolver_mock.load_bundle_from_cache = MagicMock(return_value=(False, None, None, None))
        second_resolver_mock.resolve_bundle = MagicMock(return_value=(True, 'bundle_name', 'mock bundle_file', None))
        # Mock the second resolver doesn't provide is_supported_uri by raising AttributeError
        second_resolver_mock.supported_schemes = MagicMock(side_effect=AttributeError('has no attribute '
                                                                                      '\'supported_schemes\''))

        third_resolver_mock = Mock(name='third_resolver')
        third_resolver_mock.__name__ = 'first_resolver'
        third_resolver_mock.load_bundle_from_cache = MagicMock()
        third_resolver_mock.resolve_bundle = MagicMock()
        third_resolver_mock.supported_schemes = MagicMock(return_value=[SCHEME_HTTP])

        resolver_chain_mock = MagicMock(return_value=[first_resolver_mock, second_resolver_mock, third_resolver_mock])

        detect_schemes_mock = MagicMock(return_value=[SCHEME_BUNDLE])

        stdout = MagicMock()

        with patch('conductr_cli.resolver.resolver_chain', resolver_chain_mock), \
                patch('conductr_cli.resolvers.resolvers_util.detect_schemes', detect_schemes_mock):
            logging_setup.configure_logging(MagicMock(**{}), stdout)
            bundle_name, bundle_file = resolver.resolve_bundle(custom_settings, '/some-cache-dir', '/some-bundle-path')
            self.assertEqual('bundle_name', bundle_name)
            self.assertEqual('mock bundle_file', bundle_file)

        resolver_chain_mock.assert_called_with(custom_settings, False)

        detect_schemes_mock.assert_called_once_with('/some-bundle-path')

        first_resolver_mock.supported_schemes.assert_called_once_with()
        first_resolver_mock.load_bundle_from_cache.assert_called_once_with('/some-cache-dir', '/some-bundle-path')
        first_resolver_mock.resolve_bundle.assert_called_once_with('/some-cache-dir', '/some-bundle-path')

        second_resolver_mock.supported_schemes.assert_called_once_with()
        second_resolver_mock.load_bundle_from_cache.assert_called_once_with('/some-cache-dir', '/some-bundle-path')
        second_resolver_mock.resolve_bundle.assert_called_with('/some-cache-dir', '/some-bundle-path')

        third_resolver_mock.supported_schemes.assert_called_once_with()
        third_resolver_mock.load_bundle_from_cache.assert_not_called()
        third_resolver_mock.resolve_bundle.assert_not_called()

        expected_output = strip_margin(
            as_warn("""|Warning: The resolver second_resolver does not provide `supported_schemes()` method.
                       |Resolving bundle using [first_resolver, second_resolver]
                       |"""))
        self.assertEqual(expected_output, self.output(stdout))

    def test_resolve_bundle_success_with_some_resolver_returning_errors(self):
        custom_settings = Mock()

        first_resolver_mock = Mock()
        first_resolver_mock.__name__ = 'first_resolver'
        first_resolver_load_bundle_from_cache_error = MagicMock(name='first_resolver_load_bundle_from_cache_error')
        first_resolver_mock.load_bundle_from_cache = MagicMock(
            return_value=(False, None, None, first_resolver_load_bundle_from_cache_error))
        first_resolver_mock.resolve_bundle = MagicMock(return_value=(False, None, None, None))
        first_resolver_mock.supported_schemes = MagicMock(return_value=[SCHEME_BUNDLE])

        second_resolver_mock = Mock()
        second_resolver_mock.__name__ = 'second_resolver'
        second_resolver_load_bundle_from_cache_error = MagicMock(name='second_resolver_load_bundle_from_cache_error')
        second_resolver_mock.load_bundle_from_cache = MagicMock(
            return_value=(False, None, None, second_resolver_load_bundle_from_cache_error))
        second_resolver_mock.resolve_bundle = MagicMock(return_value=(True, 'bundle_name', 'mock bundle_file', None))
        second_resolver_mock.supported_schemes = MagicMock(return_value=[SCHEME_HTTP])

        resolver_chain_mock = MagicMock(return_value=[first_resolver_mock, second_resolver_mock])

        detect_schemes_mock = MagicMock(return_value=[SCHEME_BUNDLE, SCHEME_HTTP])

        with patch('conductr_cli.resolver.resolver_chain', resolver_chain_mock), \
                patch('conductr_cli.resolvers.resolvers_util.detect_schemes', detect_schemes_mock):
            bundle_name, bundle_file = resolver.resolve_bundle(custom_settings, '/some-cache-dir', '/some-bundle-path')
            self.assertEqual('bundle_name', bundle_name)
            self.assertEqual('mock bundle_file', bundle_file)

        resolver_chain_mock.assert_called_with(custom_settings, False)
        detect_schemes_mock.assert_called_once_with('/some-bundle-path')

        first_resolver_mock.supported_schemes.assert_called_once_with()
        first_resolver_mock.load_bundle_from_cache.assert_called_once_with('/some-cache-dir', '/some-bundle-path')
        first_resolver_mock.resolve_bundle.assert_called_once_with('/some-cache-dir', '/some-bundle-path')

        second_resolver_mock.supported_schemes.assert_called_once_with()
        second_resolver_mock.load_bundle_from_cache.assert_called_once_with('/some-cache-dir', '/some-bundle-path')
        second_resolver_mock.resolve_bundle.assert_called_once_with('/some-cache-dir', '/some-bundle-path')

    def test_resolve_bundle_not_found(self):
        custom_settings = Mock()

        first_resolver_mock = Mock()
        first_resolver_mock.__name__ = 'first_resolver'
        first_resolver_mock.load_bundle_from_cache = MagicMock(return_value=(False, None, None, None))
        first_resolver_mock.resolve_bundle = MagicMock(return_value=(False, None, None, None))
        first_resolver_mock.supported_schemes = MagicMock(return_value=[SCHEME_BUNDLE])

        resolver_chain_mock = MagicMock(return_value=[first_resolver_mock])

        detect_schemes_mock = MagicMock(return_value=[SCHEME_BUNDLE, SCHEME_HTTP])

        with patch('conductr_cli.resolver.resolver_chain', resolver_chain_mock), \
                patch('conductr_cli.resolvers.resolvers_util.detect_schemes', detect_schemes_mock), \
                self.assertRaises(BundleResolutionError) as e:
            resolver.resolve_bundle(custom_settings, '/some-cache-dir', '/some-bundle-path')

        self.assertEqual([], e.exception.cache_resolution_errors)
        self.assertEqual([], e.exception.bundle_resolution_errors)

        resolver_chain_mock.assert_called_with(custom_settings, False)
        detect_schemes_mock.assert_called_once_with('/some-bundle-path')

        first_resolver_mock.supported_schemes.assert_called_once_with()
        first_resolver_mock.load_bundle_from_cache.assert_called_once_with('/some-cache-dir', '/some-bundle-path')
        first_resolver_mock.resolve_bundle.assert_called_once_with('/some-cache-dir', '/some-bundle-path')

    def test_resolve_bundle_error(self):
        custom_settings = Mock()

        first_resolver_mock = Mock()
        first_resolver_mock.__name__ = 'first_resolver'
        first_resolver_load_bundle_from_cache_error = MagicMock(name='first_resolver_load_bundle_from_cache_error')
        first_resolver_mock.load_bundle_from_cache = MagicMock(
            return_value=(False, None, None, first_resolver_load_bundle_from_cache_error))
        first_resolver_mock.resolve_bundle = MagicMock(return_value=(False, None, None, None))
        first_resolver_mock.supported_schemes = MagicMock(return_value=[SCHEME_BUNDLE])

        second_resolver_mock = Mock()
        second_resolver_mock.__name__ = 'second_resolver'
        second_resolver_load_bundle_from_cache_error = MagicMock(name='second_resolver_load_bundle_from_cache_error')
        second_resolver_mock.load_bundle_from_cache = MagicMock(
            return_value=(False, None, None, second_resolver_load_bundle_from_cache_error))
        second_resolver_resolve_bundle_error = MagicMock(name='second_resolver_resolve_bundle_error')
        second_resolver_mock.resolve_bundle = MagicMock(
            return_value=(False, None, None, second_resolver_resolve_bundle_error))
        second_resolver_mock.supported_schemes = MagicMock(return_value=[SCHEME_BUNDLE])

        resolver_chain_mock = MagicMock(return_value=[first_resolver_mock, second_resolver_mock])

        detect_schemes_mock = MagicMock(return_value=[SCHEME_BUNDLE, SCHEME_HTTP])

        with patch('conductr_cli.resolver.resolver_chain', resolver_chain_mock), \
                patch('conductr_cli.resolvers.resolvers_util.detect_schemes', detect_schemes_mock), \
                self.assertRaises(BundleResolutionError) as e:
            resolver.resolve_bundle(custom_settings, '/some-cache-dir', '/some-bundle-path')

        self.assertEqual([
            (first_resolver_mock, first_resolver_load_bundle_from_cache_error),
            (second_resolver_mock, second_resolver_load_bundle_from_cache_error),
        ], e.exception.cache_resolution_errors)

        self.assertEqual([
            (second_resolver_mock, second_resolver_resolve_bundle_error),
        ], e.exception.bundle_resolution_errors)

        resolver_chain_mock.assert_called_with(custom_settings, False)

        detect_schemes_mock.assert_called_once_with('/some-bundle-path')

        first_resolver_mock.supported_schemes.assert_called_once_with()
        first_resolver_mock.load_bundle_from_cache.assert_called_once_with('/some-cache-dir', '/some-bundle-path')
        first_resolver_mock.resolve_bundle.assert_called_once_with('/some-cache-dir', '/some-bundle-path')

        second_resolver_mock.supported_schemes.assert_called_once_with()
        second_resolver_mock.load_bundle_from_cache.assert_called_once_with('/some-cache-dir', '/some-bundle-path')
        second_resolver_mock.resolve_bundle.assert_called_once_with('/some-cache-dir', '/some-bundle-path')

    def test_resolve_bundle_from_cache(self):
        custom_settings = Mock()

        first_resolver_mock = Mock()
        first_resolver_mock.__name__ = 'first_resolver'
        first_resolver_mock.load_bundle_from_cache = MagicMock(return_value=(True, 'bundle_name', 'mock bundle_file', None))
        first_resolver_mock.resolve_bundle = MagicMock()
        first_resolver_mock.supported_schemes = MagicMock(return_value=[SCHEME_BUNDLE])

        resolver_chain_mock = MagicMock(return_value=[first_resolver_mock])

        detect_schemes_mock = MagicMock(return_value=[SCHEME_BUNDLE, SCHEME_HTTP])

        stdout = MagicMock()
        with patch('conductr_cli.resolver.resolver_chain', resolver_chain_mock), \
                patch('conductr_cli.resolvers.resolvers_util.detect_schemes', detect_schemes_mock):
            logging_setup.configure_logging(MagicMock(**{}), stdout)
            bundle_name, bundle_file = resolver.resolve_bundle(custom_settings, '/some-cache-dir',
                                                               '/some-bundle-path')
            self.assertEqual('bundle_name', bundle_name)
            self.assertEqual('mock bundle_file', bundle_file)

        resolver_chain_mock.assert_called_with(custom_settings, False)
        detect_schemes_mock.assert_called_with('/some-bundle-path')

        first_resolver_mock.supported_schemes.assert_called_once_with()
        first_resolver_mock.load_bundle_from_cache.assert_called_once_with('/some-cache-dir', '/some-bundle-path')
        first_resolver_mock.resolve_bundle.assert_not_called()

        self.assertEqual('Resolving bundle using [first_resolver]\n', self.output(stdout))

    def test_resolve_bundle_no_suitable_resolver(self):
        custom_settings = Mock()

        first_resolver_mock = Mock()
        first_resolver_mock.__name__ = 'first_resolver'
        first_resolver_mock.load_bundle_from_cache = MagicMock()
        first_resolver_mock.resolve_bundle = MagicMock()
        first_resolver_mock.supported_schemes = MagicMock(return_value=[SCHEME_BUNDLE])

        resolver_chain_mock = MagicMock(return_value=[first_resolver_mock])

        detect_schemes_mock = MagicMock(return_value=[SCHEME_HTTP])

        stdout = MagicMock()
        with patch('conductr_cli.resolver.resolver_chain', resolver_chain_mock), \
                patch('conductr_cli.resolvers.resolvers_util.detect_schemes', detect_schemes_mock), \
                self.assertRaises(BundleResolutionError) as e:
            logging_setup.configure_logging(MagicMock(**{}), stdout)
            resolver.resolve_bundle(custom_settings, '/some-cache-dir', '/some-bundle-path')

        self.assertEqual([], e.exception.cache_resolution_errors)
        self.assertEqual([], e.exception.bundle_resolution_errors)

        resolver_chain_mock.assert_called_with(custom_settings, False)

        detect_schemes_mock.assert_called_once_with('/some-bundle-path')

        first_resolver_mock.supported_schemes.assert_called_once_with()
        first_resolver_mock.load_bundle_from_cache.assert_not_called()
        first_resolver_mock.resolve_bundle.assert_not_called()

        self.assertEqual('', self.output(stdout))

    def test_resolve_bundle_configuration_success(self):
        custom_settings = Mock()

        first_resolver_mock = Mock()
        first_resolver_mock.__name__ = 'first_resolver'
        first_resolver_mock.load_bundle_configuration_from_cache = MagicMock(return_value=(False, None, None, None))
        first_resolver_mock.resolve_bundle_configuration = MagicMock(return_value=(False, None, None, None))
        first_resolver_mock.supported_schemes = MagicMock(return_value=[SCHEME_BUNDLE])

        second_resolver_mock = Mock()
        second_resolver_mock.__name__ = 'second_resolver'
        second_resolver_mock.load_bundle_configuration_from_cache = MagicMock(return_value=(False, None, None, None))
        second_resolver_mock.resolve_bundle_configuration = MagicMock(return_value=(True, 'bundle_name',
                                                                                    'mock bundle_file', None))
        # Mock the second resolver doesn't provide is_supported_uri by raising AttributeError
        second_resolver_mock.supported_schemes = MagicMock(side_effect=AttributeError('has no attribute '
                                                                                      '\'supported_schemes\''))

        third_resolver_mock = Mock(name='third_resolver')
        third_resolver_mock.__name__ = 'third_resolver'
        third_resolver_mock.load_bundle_from_cache = MagicMock()
        third_resolver_mock.resolve_bundle = MagicMock()
        third_resolver_mock.supported_schemes = MagicMock(return_value=[SCHEME_HTTP])

        resolver_chain_mock = MagicMock(return_value=[first_resolver_mock, second_resolver_mock, third_resolver_mock])

        detect_schemes_mock = MagicMock(return_value=[SCHEME_BUNDLE])

        stdout = MagicMock()
        with patch('conductr_cli.resolver.resolver_chain', resolver_chain_mock), \
                patch('conductr_cli.resolvers.resolvers_util.detect_schemes', detect_schemes_mock):
            logging_setup.configure_logging(MagicMock(**{}), stdout)
            bundle_name, bundle_file = resolver.resolve_bundle_configuration(
                custom_settings, '/some-cache-dir', '/some-bundle-path')
            self.assertEqual('bundle_name', bundle_name)
            self.assertEqual('mock bundle_file', bundle_file)

        resolver_chain_mock.assert_called_with(custom_settings, False)
        detect_schemes_mock.assert_called_with('/some-bundle-path')

        first_resolver_mock.supported_schemes.assert_called_once_with()
        first_resolver_mock.load_bundle_configuration_from_cache.assert_called_once_with('/some-cache-dir',
                                                                                         '/some-bundle-path')
        first_resolver_mock.resolve_bundle_configuration.assert_called_once_with('/some-cache-dir', '/some-bundle-path')

        second_resolver_mock.supported_schemes.assert_called_once_with()
        second_resolver_mock.load_bundle_configuration_from_cache.assert_called_once_with('/some-cache-dir',
                                                                                          '/some-bundle-path')
        second_resolver_mock.resolve_bundle_configuration.assert_called_once_with('/some-cache-dir', '/some-bundle-path')

        third_resolver_mock.supported_schemes.assert_called_once_with()
        third_resolver_mock.load_bundle_configuration_from_cache.assert_not_called()
        third_resolver_mock.resolve_bundle_configuration.assert_not_called()

        expected_output = strip_margin(
            as_warn("""|Warning: The resolver second_resolver does not provide `supported_schemes()` method.
                       |Resolving bundle configuration using [first_resolver, second_resolver]
                       |"""))
        self.assertEqual(expected_output, self.output(stdout))

    def test_resolve_bundle_configuration_failure(self):
        custom_settings = Mock()

        first_resolver_mock = Mock()
        first_resolver_mock.__name__ = 'first_resolver'
        first_resolver_mock.load_bundle_configuration_from_cache = MagicMock(return_value=(False, None, None, None))
        first_resolver_mock.resolve_bundle_configuration = MagicMock(return_value=(False, None, None, None))
        first_resolver_mock.supported_schemes = MagicMock(return_value=[SCHEME_BUNDLE])

        resolver_chain_mock = MagicMock(return_value=[first_resolver_mock])

        detect_schemes_mock = MagicMock(return_value=[SCHEME_BUNDLE])

        with patch('conductr_cli.resolver.resolver_chain', resolver_chain_mock), \
                patch('conductr_cli.resolvers.resolvers_util.detect_schemes', detect_schemes_mock), \
                self.assertRaises(BundleResolutionError) as e:
            resolver.resolve_bundle_configuration(custom_settings, '/some-cache-dir', '/some-bundle-path')

        self.assertEqual([], e.exception.cache_resolution_errors)
        self.assertEqual([], e.exception.bundle_resolution_errors)

        resolver_chain_mock.assert_called_with(custom_settings, False)
        detect_schemes_mock.assert_called_with('/some-bundle-path')

        first_resolver_mock.supported_schemes.assert_called_once_with()
        first_resolver_mock.load_bundle_configuration_from_cache.assert_called_once_with('/some-cache-dir',
                                                                                         '/some-bundle-path')
        first_resolver_mock.resolve_bundle_configuration.assert_called_once_with('/some-cache-dir', '/some-bundle-path')

    def test_resolve_bundle_configuration_no_suitable_resolver(self):
        custom_settings = Mock()

        first_resolver_mock = Mock()
        first_resolver_mock.__name__ = 'first_resolver'
        first_resolver_mock.load_bundle_configuration_from_cache = MagicMock()
        first_resolver_mock.resolve_bundle_configuration = MagicMock()
        first_resolver_mock.supported_schemes = MagicMock(return_value=[SCHEME_BUNDLE])

        resolver_chain_mock = MagicMock(return_value=[first_resolver_mock])

        detect_schemes_mock = MagicMock(return_value=[SCHEME_HTTP])

        with patch('conductr_cli.resolver.resolver_chain', resolver_chain_mock), \
                patch('conductr_cli.resolvers.resolvers_util.detect_schemes', detect_schemes_mock), \
                self.assertRaises(BundleResolutionError) as e:
            resolver.resolve_bundle_configuration(custom_settings, '/some-cache-dir', '/some-bundle-path')

        self.assertEqual([], e.exception.cache_resolution_errors)
        self.assertEqual([], e.exception.bundle_resolution_errors)

        resolver_chain_mock.assert_called_with(custom_settings, False)
        detect_schemes_mock.assert_called_with('/some-bundle-path')

        first_resolver_mock.supported_schemes.assert_called_once_with()
        first_resolver_mock.load_bundle_configuration_from_cache.assert_not_called()
        first_resolver_mock.resolve_bundle_configuration.assert_not_called()

    def test_resolve_bundle_configuration_from_cache(self):
        custom_settings = Mock()

        first_resolver_mock = Mock()
        first_resolver_mock.__name__ = 'first_resolver'
        first_resolver_mock.load_bundle_configuration_from_cache = MagicMock(return_value=(True, 'bundle_name',
                                                                                           'mock bundle_file', None))
        first_resolver_mock.resolve_bundle_configuration = MagicMock()
        first_resolver_mock.supported_schemes = MagicMock(return_value=[SCHEME_BUNDLE])

        resolver_chain_mock = MagicMock(return_value=[first_resolver_mock])

        detect_schemes_mock = MagicMock(return_value=[SCHEME_BUNDLE])

        with patch('conductr_cli.resolver.resolver_chain', resolver_chain_mock), \
                patch('conductr_cli.resolvers.resolvers_util.detect_schemes', detect_schemes_mock):
            bundle_name, bundle_file = resolver.resolve_bundle_configuration(custom_settings, '/some-cache-dir',
                                                                             '/some-bundle-path')
            self.assertEqual('bundle_name', bundle_name)
            self.assertEqual('mock bundle_file', bundle_file)

        resolver_chain_mock.assert_called_with(custom_settings, False)
        detect_schemes_mock.assert_called_with('/some-bundle-path')

        first_resolver_mock.supported_schemes.assert_called_once_with()
        first_resolver_mock.load_bundle_configuration_from_cache.assert_called_once_with('/some-cache-dir',
                                                                                         '/some-bundle-path')
        first_resolver_mock.resolve_bundle_configuration.assert_not_called()


class TestResolverResolveBundleVersion(CliTestCase):
    def test_resolve_bundle_version_success(self):
        custom_settings = Mock()

        first_resolver_mock = Mock()
        first_resolver_mock.__name__ = 'first_resolver'
        first_resolver_mock.resolve_bundle_version = MagicMock(return_value=(None, None))
        first_resolver_mock.supported_schemes = MagicMock(return_value=[SCHEME_BUNDLE])

        second_resolver_mock = Mock()
        second_resolver_mock.__name__ = 'second_resolver'
        resolved_version = {'test': 'only'}
        second_resolver_mock.resolve_bundle_version = MagicMock(return_value=(resolved_version, None))
        second_resolver_mock.supported_schemes = MagicMock(return_value=[SCHEME_HTTP])

        resolver_chain_mock = MagicMock(return_value=[first_resolver_mock, second_resolver_mock])

        detect_schemes_mock = MagicMock(return_value=[SCHEME_BUNDLE, SCHEME_HTTP])

        stdout = MagicMock()

        with patch('conductr_cli.resolver.resolver_chain', resolver_chain_mock), \
                patch('conductr_cli.resolvers.resolvers_util.detect_schemes', detect_schemes_mock):
            logging_setup.configure_logging(MagicMock(**{}), stdout)
            result = resolver.resolve_bundle_version(custom_settings, 'bundle')
            self.assertEqual(resolved_version, result)

        resolver_chain_mock.assert_called_with(custom_settings, False)
        detect_schemes_mock.assert_called_once_with('bundle')

        first_resolver_mock.supported_schemes.assert_called_with()
        first_resolver_mock.resolve_bundle_version.assert_called_with('bundle')

        second_resolver_mock.supported_schemes.assert_called_with()
        second_resolver_mock.resolve_bundle_version.assert_called_with('bundle')

        expected_output = strip_margin("""|Resolving bundle version using [first_resolver, second_resolver]
                                          |""")
        self.assertEqual(expected_output, self.output(stdout))

    def test_resolve_bundle_version_success_offline(self):
        custom_settings = Mock()

        first_resolver_mock = Mock()
        first_resolver_mock.__name__ = 'first_resolver'
        first_resolver_mock.resolve_bundle_version = MagicMock(return_value=(None, None))
        first_resolver_mock.supported_schemes = MagicMock(return_value=[SCHEME_BUNDLE])

        second_resolver_mock = Mock()
        second_resolver_mock.__name__ = 'second_resolver'
        resolved_version = {'test': 'only'}
        second_resolver_mock.resolve_bundle_version = MagicMock(return_value=(resolved_version, None))
        # Mock the second resolver doesn't provide is_supported_uri by raising AttributeError
        second_resolver_mock.supported_schemes = MagicMock(side_effect=AttributeError('has no attribute '
                                                                                      '\'supported_schemes\''))

        resolver_chain_mock = MagicMock(return_value=[first_resolver_mock, second_resolver_mock])

        detect_schemes_mock = MagicMock(return_value=[SCHEME_BUNDLE, SCHEME_HTTP])

        stdout = MagicMock()

        with patch('conductr_cli.resolver.resolver_chain', resolver_chain_mock), \
                patch('conductr_cli.resolvers.resolvers_util.detect_schemes', detect_schemes_mock):
            logging_setup.configure_logging(MagicMock(**{}), stdout)
            result = resolver.resolve_bundle_version(custom_settings, 'bundle', offline_mode=True)
            self.assertEqual(resolved_version, result)

        resolver_chain_mock.assert_called_with(custom_settings, True)

        detect_schemes_mock.assert_called_once_with('bundle')

        first_resolver_mock.supported_schemes.assert_called_once_with()
        first_resolver_mock.resolve_bundle_version.assert_called_once_with('bundle')

        second_resolver_mock.supported_schemes.assert_called_once_with()
        second_resolver_mock.resolve_bundle_version.assert_called_once_with('bundle')

        expected_output = strip_margin(
            as_warn("""|Warning: The resolver second_resolver does not provide `supported_schemes()` method.
                       |Resolving bundle version using [first_resolver, second_resolver]
                       |"""))
        self.assertEqual(expected_output, self.output(stdout))

    def test_resolve_bundle_version_failure(self):
        custom_settings = Mock()

        first_resolver_mock = Mock()
        first_resolver_mock.__name__ = 'first_resolver'
        first_resolver_mock.resolve_bundle_version = MagicMock(return_value=(None, None))
        first_resolver_mock.supported_schemes = MagicMock(return_value=[SCHEME_BUNDLE])

        resolver_chain_mock = MagicMock(return_value=[first_resolver_mock])

        detect_schemes_mock = MagicMock(return_value=[SCHEME_BUNDLE, SCHEME_HTTP])

        stdout = MagicMock()

        with patch('conductr_cli.resolver.resolver_chain', resolver_chain_mock), \
                patch('conductr_cli.resolvers.resolvers_util.detect_schemes', detect_schemes_mock), \
                self.assertRaises(BundleResolutionError) as e:
            logging_setup.configure_logging(MagicMock(**{}), stdout)
            resolver.resolve_bundle_version(custom_settings, 'bundle')

        self.assertEqual([], e.exception.cache_resolution_errors)
        self.assertEqual([], e.exception.bundle_resolution_errors)

        resolver_chain_mock.assert_called_with(custom_settings, False)
        detect_schemes_mock.assert_called_once_with('bundle')

        first_resolver_mock.supported_schemes.assert_called_once_with()
        first_resolver_mock.resolve_bundle_version.assert_called_once_with('bundle')

        expected_output = strip_margin("""|Resolving bundle version using [first_resolver]
                                          |""")
        self.assertEqual(expected_output, self.output(stdout))

    def test_resolve_bundle_version_no_suitable_resolver(self):
        custom_settings = Mock()

        first_resolver_mock = Mock()
        first_resolver_mock.__name__ = 'first_resolver'
        first_resolver_mock.resolve_bundle_version = MagicMock()
        first_resolver_mock.supported_schemes = MagicMock(return_value=[SCHEME_BUNDLE])

        resolver_chain_mock = MagicMock(return_value=[first_resolver_mock])

        detect_schemes_mock = MagicMock(return_value=[SCHEME_HTTP])

        stdout = MagicMock()

        with patch('conductr_cli.resolver.resolver_chain', resolver_chain_mock), \
                patch('conductr_cli.resolvers.resolvers_util.detect_schemes', detect_schemes_mock), \
                self.assertRaises(BundleResolutionError) as e:
            logging_setup.configure_logging(MagicMock(**{}), stdout)
            resolver.resolve_bundle_version(custom_settings, 'bundle')

        self.assertEqual([], e.exception.cache_resolution_errors)
        self.assertEqual([], e.exception.bundle_resolution_errors)

        resolver_chain_mock.assert_called_with(custom_settings, False)

        detect_schemes_mock.assert_called_with('bundle')

        first_resolver_mock.supported_schemes.assert_called_once_with()
        first_resolver_mock.resolve_bundle_version.assert_not_called()

        self.assertEqual('', self.output(stdout))


class TestResolverContinuousDeliveryUri(TestCase):
    resolved_version = {
        'test': 'only'
    }

    def test_success(self):
        custom_settings = Mock()

        first_resolver_mock = Mock()
        first_resolver_mock.continuous_delivery_uri = MagicMock(return_value=None)

        resolved_cd_url = 'http://test'

        second_resolver_mock = Mock()
        second_resolver_mock.continuous_delivery_uri = MagicMock(return_value=resolved_cd_url)

        resolver_chain_mock = MagicMock(return_value=[first_resolver_mock, second_resolver_mock])

        with patch('conductr_cli.resolver.resolver_chain', resolver_chain_mock):
            result = resolver.continuous_delivery_uri(custom_settings, self.resolved_version)
            self.assertEqual(resolved_cd_url, result)

        resolver_chain_mock.assert_called_with(custom_settings, False)
        first_resolver_mock.continuous_delivery_uri.assert_called_with(self.resolved_version)
        second_resolver_mock.continuous_delivery_uri.assert_called_with(self.resolved_version)

    def test_success_offline(self):
        custom_settings = Mock()

        first_resolver_mock = Mock()
        first_resolver_mock.continuous_delivery_uri = MagicMock(return_value=None)

        resolved_cd_url = 'http://test'

        second_resolver_mock = Mock()
        second_resolver_mock.continuous_delivery_uri = MagicMock(return_value=resolved_cd_url)

        resolver_chain_mock = MagicMock(return_value=[first_resolver_mock, second_resolver_mock])

        with patch('conductr_cli.resolver.resolver_chain', resolver_chain_mock):
            result = resolver.continuous_delivery_uri(custom_settings, self.resolved_version, offline_mode=True)
            self.assertEqual(resolved_cd_url, result)

        resolver_chain_mock.assert_called_with(custom_settings, True)
        first_resolver_mock.continuous_delivery_uri.assert_called_with(self.resolved_version)
        second_resolver_mock.continuous_delivery_uri.assert_called_with(self.resolved_version)

    def test_not_found(self):
        custom_settings = Mock()

        first_resolver_mock = Mock()
        first_resolver_mock.continuous_delivery_uri = MagicMock(return_value=None)

        second_resolver_mock = Mock()
        second_resolver_mock.continuous_delivery_uri = MagicMock(return_value=None)

        resolver_chain_mock = MagicMock(return_value=[first_resolver_mock, second_resolver_mock])

        with patch('conductr_cli.resolver.resolver_chain', resolver_chain_mock):
            self.assertRaises(ContinuousDeliveryError, resolver.continuous_delivery_uri, custom_settings,
                              self.resolved_version)

        resolver_chain_mock.assert_called_with(custom_settings, False)
        first_resolver_mock.continuous_delivery_uri.assert_called_with(self.resolved_version)
        second_resolver_mock.continuous_delivery_uri.assert_called_with(self.resolved_version)


class TestResolverChain(TestCase):
    def test_custom_resolver_chain(self):
        custom_settings = ConfigFactory.parse_string(
            strip_margin("""|resolvers = [
                            |   conductr_cli.resolvers.uri_resolver
                            |]
                            |""")
        )

        get_logger_mock, log_mock = create_mock_logger()

        with patch('logging.getLogger', get_logger_mock):
            result = resolver.resolver_chain(custom_settings, False)
            expected_result = [uri_resolver]
            self.assertEqual(expected_result, result)

        get_logger_mock.assert_called_with('conductr_cli.resolver')
        log_mock.info.assert_called_with('Using custom bundle resolver chain [\'conductr_cli.resolvers.uri_resolver\']')

    def test_none_input(self):
        result = resolver.resolver_chain(None, False)
        expected_result = [stdin_resolver, uri_resolver, bintray_resolver, docker_resolver, s3_resolver]
        self.assertEqual(expected_result, result)

    def test_custom_settings_no_resolver_config(self):
        custom_settings = ConfigFactory.parse_string(
            strip_margin("""|dummy = foo
                            |""")
        )
        result = resolver.resolver_chain(custom_settings, False)
        expected_result = [stdin_resolver, uri_resolver, bintray_resolver, docker_resolver, s3_resolver]
        self.assertEqual(expected_result, result)

    def test_offline_mode(self):
        result = resolver.resolver_chain(None, True)
        expected_result = [stdin_resolver, offline_resolver, docker_offline_resolver]
        self.assertEqual(expected_result, result)
