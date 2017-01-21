from unittest import TestCase
from conductr_cli.test.cli_test_case import strip_margin
from conductr_cli.resolvers import bintray_resolver
from conductr_cli.exceptions import MalformedBundleUriError, BintrayResolutionError, MalformedBintrayCredentialsError, \
    BintrayCredentialsNotFoundError
from requests.exceptions import HTTPError, ConnectionError
import io
import os
from unittest.mock import call, patch, MagicMock, Mock


class TestResolveBundle(TestCase):
    def test_bintray_version_found(self):
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(return_value={
            'org': 'typesafe',
            'repo': 'bundle',
            'package_name': 'bundle-name',
            'compatibility_version': 'v1',
            'digest': 'digest',
            'version': 'v1-digest',
            'path': 'download.zip'
        })
        resolve_bundle_mock = MagicMock(return_value=(True, 'bundle-name', 'mock bundle file'))

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.uri_resolver.resolve_file', resolve_bundle_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.resolve_bundle('/cache-dir', 'bundle-name:v1')
            self.assertTrue(is_resolved)
            self.assertEqual('bundle-name', bundle_name)
            self.assertEqual('mock bundle file', bundle_file)

        load_bintray_credentials_mock.assert_called_with()
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with('username', 'password', 'typesafe', 'bundle', 'bundle-name',
                                                        None, 'v1', 'digest')
        resolve_bundle_mock.assert_called_with('/cache-dir', 'https://dl.bintray.com/typesafe/bundle/download.zip',
                                               ('Bintray', 'username', 'password'))

    def test_bintray_version_not_found(self):
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(return_value=None)

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.resolve_bundle('/cache-dir', 'bundle-name:v1')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        load_bintray_credentials_mock.assert_called_with()
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with('username', 'password', 'typesafe', 'bundle', 'bundle-name',
                                                        None, 'v1', 'digest')

    def test_failure_malformed_bundle_uri(self):
        parse_bundle_mock = MagicMock(side_effect=MalformedBundleUriError('test only'))

        with patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.resolve_bundle('/cache-dir', 'bundle-name:v1')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        parse_bundle_mock.assert_called_with('bundle-name:v1')

    def test_failure_http_error(self):
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(side_effect=HTTPError('test only'))

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.resolve_bundle('/cache-dir', 'bundle-name:v1')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        load_bintray_credentials_mock.assert_called_with()
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with('username', 'password', 'typesafe', 'bundle', 'bundle-name',
                                                        None, 'v1', 'digest')

    def test_connection_error(self):
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(side_effect=ConnectionError('test only'))

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.resolve_bundle('/cache-dir', 'bundle-name:v1')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        load_bintray_credentials_mock.assert_called_with()
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with('username', 'password', 'typesafe', 'bundle', 'bundle-name',
                                                        None, 'v1', 'digest')


class TestResolveBundleConfiguration(TestCase):
    def test_bintray_version_found(self):
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_bundle_configuration_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle-configuration',
                                                                  'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(return_value={
            'org': 'typesafe',
            'repo': 'bundle-configuration',
            'package_name': 'bundle-name',
            'compatibility_version': 'v1',
            'digest': 'digest',
            'path': 'download.zip'
        })
        resolve_bundle_mock = MagicMock(return_value=(True, 'bundle-name', 'mock bundle file'))

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle_configuration', parse_bundle_configuration_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.uri_resolver.resolve_file', resolve_bundle_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.resolve_bundle_configuration(
                '/cache-dir', 'bundle-name:v1')
            self.assertTrue(is_resolved)
            self.assertEqual('bundle-name', bundle_name)
            self.assertEqual('mock bundle file', bundle_file)

        load_bintray_credentials_mock.assert_called_with()
        parse_bundle_configuration_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with('username', 'password', 'typesafe', 'bundle-configuration',
                                                        'bundle-name', None, 'v1', 'digest')
        resolve_bundle_mock.assert_called_with('/cache-dir',
                                               'https://dl.bintray.com/typesafe/bundle-configuration/download.zip',
                                               ('Bintray', 'username', 'password'))

    def test_bintray_version_not_found(self):
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_bundle_configuration_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle-configuration',
                                                                  'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(return_value=None)

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle_configuration', parse_bundle_configuration_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.resolve_bundle_configuration(
                '/cache-dir', 'bundle-name:v1')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        load_bintray_credentials_mock.assert_called_with()
        parse_bundle_configuration_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with('username', 'password', 'typesafe', 'bundle-configuration',
                                                        'bundle-name', None, 'v1', 'digest')

    def test_failure_malformed_bundle_uri(self):
        parse_bundle_configuration_mock = MagicMock(side_effect=MalformedBundleUriError('test only'))

        with patch('conductr_cli.bundle_shorthand.parse_bundle_configuration', parse_bundle_configuration_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.resolve_bundle_configuration(
                '/cache-dir', 'bundle-name:v1')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        parse_bundle_configuration_mock.assert_called_with('bundle-name:v1')

    def test_failure_http_error(self):
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_bundle_configuration_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle-configuration',
                                                                  'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(side_effect=HTTPError('test only'))

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle_configuration', parse_bundle_configuration_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.resolve_bundle_configuration(
                '/cache-dir', 'bundle-name:v1')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        load_bintray_credentials_mock.assert_called_with()
        parse_bundle_configuration_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with('username', 'password', 'typesafe', 'bundle-configuration',
                                                        'bundle-name', None, 'v1', 'digest')

    def test_failure_connection_error(self):
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_bundle_configuration_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle-configuration',
                                                                  'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(side_effect=ConnectionError('test only'))

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle_configuration', parse_bundle_configuration_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.resolve_bundle_configuration(
                '/cache-dir', 'bundle-name:v1')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        load_bintray_credentials_mock.assert_called_with()
        parse_bundle_configuration_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with('username', 'password', 'typesafe', 'bundle-configuration',
                                                        'bundle-name', None, 'v1', 'digest')


class TestLoadBundleFromCache(TestCase):
    def test_file(self):
        exists_mock = MagicMock(return_value=True)
        parse_bundle_mock = MagicMock()

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.load_bundle_from_cache(
                '/cache-dir', '/tmp/bundle.zip')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        exists_mock.assert_called_with('/tmp/bundle.zip')
        parse_bundle_mock.assert_not_called()

    def test_bundle(self):
        exists_mock = MagicMock(return_value=False)
        bintray_download_det_mock = MagicMock(return_value=(None, None))

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_download_details', bintray_download_det_mock):
            bintray_resolver.load_bundle_from_cache(
                '/cache-dir', '/tmp/bundle')

        exists_mock.assert_not_called()

    def test_bintray_version_found(self):
        exists_mock = MagicMock(return_value=False)
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(return_value={
            'org': 'typesafe',
            'repo': 'bundle',
            'package_name': 'bundle-name',
            'compatibility_version': 'v1',
            'digest': 'digest',
            'path': 'download.zip'
        })
        load_bundle_from_cache_mock = MagicMock(return_value=(True, 'bundle-name', 'mock bundle file'))

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.uri_resolver.load_bundle_from_cache',
                      load_bundle_from_cache_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.load_bundle_from_cache('/cache-dir',
                                                                                            'bundle-name:v1')
            self.assertTrue(is_resolved)
            self.assertEqual('bundle-name', bundle_name)
            self.assertEqual('mock bundle file', bundle_file)

        exists_mock.assert_not_called()
        load_bintray_credentials_mock.assert_called_with()
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with('username', 'password', 'typesafe', 'bundle', 'bundle-name',
                                                        None, 'v1', 'digest')
        load_bundle_from_cache_mock.assert_called_with('/cache-dir',
                                                       'https://dl.bintray.com/typesafe/bundle/download.zip',
                                                       False)

    def test_bintray_version_not_found(self):
        exists_mock = MagicMock(return_value=False)
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(return_value=None)

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.load_bundle_from_cache('/cache-dir',
                                                                                            'bundle-name:v1')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        exists_mock.assert_not_called()
        load_bintray_credentials_mock.assert_called_with()
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with('username', 'password', 'typesafe', 'bundle', 'bundle-name',
                                                        None, 'v1', 'digest')

    def test_failure_malformed_bundle_uri(self):
        exists_mock = MagicMock(return_value=False)
        parse_bundle_mock = MagicMock(side_effect=MalformedBundleUriError('test only'))

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.load_bundle_from_cache('/cache-dir',
                                                                                            'bundle-name:v1')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        exists_mock.assert_not_called()
        parse_bundle_mock.assert_called_with('bundle-name:v1')

    def test_failure_http_error(self):
        exists_mock = MagicMock(return_value=False)
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(side_effect=HTTPError('test only'))

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.load_bundle_from_cache('/cache-dir',
                                                                                            'bundle-name:v1')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        exists_mock.assert_not_called()
        load_bintray_credentials_mock.assert_called_with()
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with('username', 'password', 'typesafe', 'bundle', 'bundle-name',
                                                        None, 'v1', 'digest')

    def test_failure_connection_error(self):
        exists_mock = MagicMock(return_value=False)
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(side_effect=ConnectionError('test only'))

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.load_bundle_from_cache('/cache-dir',
                                                                                            'bundle-name:v1')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        exists_mock.assert_not_called()
        load_bintray_credentials_mock.assert_called_with()
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with('username', 'password', 'typesafe', 'bundle', 'bundle-name',
                                                        None, 'v1', 'digest')


class TestLoadBundleConfigurationFromCache(TestCase):
    def test_file(self):
        exists_mock = MagicMock(return_value=True)
        parse_bundle_configuration_mock = MagicMock()

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle_configuration', parse_bundle_configuration_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.load_bundle_configuration_from_cache(
                '/cache-dir', '/tmp/bundle.zip')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        exists_mock.assert_called_with('/tmp/bundle.zip')
        parse_bundle_configuration_mock.assert_not_called()

    def test_bintray_version_found(self):
        exists_mock = MagicMock(return_value=False)
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_bundle_configuration_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle-configuration',
                                                                  'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(return_value={
            'org': 'typesafe',
            'repo': 'bundle-configuration',
            'package_name': 'bundle-name',
            'compatibility_version': 'v1',
            'digest': 'digest',
            'path': 'download.zip'
        })
        load_bundle_from_cache_mock = MagicMock(return_value=(True, 'bundle-name', 'mock bundle file'))

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle_configuration', parse_bundle_configuration_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.uri_resolver.load_bundle_from_cache',
                      load_bundle_from_cache_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.load_bundle_configuration_from_cache(
                '/cache-dir', 'bundle-name:v1')
            self.assertTrue(is_resolved)
            self.assertEqual('bundle-name', bundle_name)
            self.assertEqual('mock bundle file', bundle_file)

        exists_mock.assert_not_called()
        load_bintray_credentials_mock.assert_called_with()
        parse_bundle_configuration_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with('username', 'password', 'typesafe', 'bundle-configuration',
                                                        'bundle-name', None, 'v1', 'digest')
        load_bundle_from_cache_mock.assert_called_with('/cache-dir',
                                                       'https://dl.bintray.com/typesafe/bundle-configuration/download.zip',
                                                       False)

    def test_bintray_version_not_found(self):
        exists_mock = MagicMock(return_value=False)
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_bundle_configuration_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle-configuration',
                                                                  'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(return_value=None)

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle_configuration', parse_bundle_configuration_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.load_bundle_configuration_from_cache(
                '/cache-dir', 'bundle-name:v1')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        exists_mock.assert_not_called()
        load_bintray_credentials_mock.assert_called_with()
        parse_bundle_configuration_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with('username', 'password', 'typesafe', 'bundle-configuration',
                                                        'bundle-name', None, 'v1', 'digest')

    def test_failure_malformed_bundle_uri(self):
        exists_mock = MagicMock(return_value=False)
        parse_bundle_mock = MagicMock(side_effect=MalformedBundleUriError('test only'))

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.load_bundle_from_cache('/cache-dir',
                                                                                            'bundle-name:v1')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        exists_mock.assert_not_called()
        parse_bundle_mock.assert_called_with('bundle-name:v1')

    def test_failure_http_error(self):
        exists_mock = MagicMock(return_value=False)
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_bundle_configuration_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle-configuration',
                                                    'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(side_effect=HTTPError('test only'))

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle_configuration', parse_bundle_configuration_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.load_bundle_configuration_from_cache(
                '/cache-dir', 'bundle-name:v1')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        exists_mock.assert_not_called()
        load_bintray_credentials_mock.assert_called_with()
        parse_bundle_configuration_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with('username', 'password', 'typesafe', 'bundle-configuration',
                                                        'bundle-name', None, 'v1', 'digest')

    def test_failure_connection_error(self):
        exists_mock = MagicMock(return_value=False)
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_bundle_configuration_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle-configuration',
                                                                  'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(side_effect=ConnectionError('test only'))

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle_configuration', parse_bundle_configuration_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.load_bundle_configuration_from_cache(
                '/cache-dir', 'bundle-name:v1')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        exists_mock.assert_not_called()
        load_bintray_credentials_mock.assert_called_with()
        parse_bundle_configuration_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with('username', 'password', 'typesafe', 'bundle-configuration',
                                                        'bundle-name', None, 'v1', 'digest')


class TestResolveConductrBinary(TestCase):
    def test_binary_found(self):
        bintray_resolve_version_mock = MagicMock(return_value={
            'org': 'org',
            'repo': 'repo',
            'package_name': 'package-name',
            'compatibility_version': None,
            'digest': None,
            'version': '1.0.0',
            'path': 'conductr-1.0.0.tgz'
        })
        resolve_file_mock = MagicMock(return_value=(True, 'conductr-1.0.0.tgz', '/cache-dir/conductr-1.0.0.tgz'))

        with patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.uri_resolver.resolve_file', resolve_file_mock):
            auth = 'Bintray', 'username', 'password'
            is_resolved, file_name, file_uri = bintray_resolver.bintray_download('/cache-dir', 'org', 'repo',
                                                                                 'package-name', auth, '1.0.0')
            self.assertTrue(is_resolved)
            self.assertEqual('conductr-1.0.0.tgz', file_name)
            self.assertEqual('/cache-dir/conductr-1.0.0.tgz', file_uri)

        bintray_resolve_version_mock.assert_called_with('username', 'password', 'org', 'repo', 'package-name',
                                                        '1.0.0', None, None)
        resolve_file_mock.assert_called_with('/cache-dir', 'https://dl.bintray.com/org/repo/conductr-1.0.0.tgz',
                                             ('Bintray', 'username', 'password'))

    def test_binary_not_found(self):
        bintray_resolve_version_mock = MagicMock(return_value=None)

        with patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            auth = 'Bintray', 'username', 'password'
            is_resolved, file_name, file_uri = bintray_resolver.bintray_download('/cache-dir', 'org', 'repo',
                                                                                 'package-name', auth, '100.0.0')
            self.assertFalse(is_resolved)
            self.assertIsNone(file_name)
            self.assertIsNone(file_uri)

        bintray_resolve_version_mock.assert_called_with('username', 'password', 'org', 'repo', 'package-name',
                                                        '100.0.0', None, None)

    def test_failure_http_error(self):
        bintray_resolve_version_mock = MagicMock(side_effect=HTTPError('test only'))

        with patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            auth = 'Bintray', 'username', 'password'
            self.assertRaises(HTTPError, bintray_resolver.bintray_download,
                              '/cache-dir', 'org', 'repo', 'package-name', auth, '1.0.0')

        bintray_resolve_version_mock.assert_called_with('username', 'password', 'org', 'repo', 'package-name',
                                                        '1.0.0', None, None)

    def test_failure_connection_error(self):
        bintray_resolve_version_mock = MagicMock(side_effect=ConnectionError('test only'))

        with patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            auth = 'Bintray', 'username', 'password'
            self.assertRaises(ConnectionError, bintray_resolver.bintray_download,
                              '/cache-dir', 'org', 'repo', 'package-name', auth, '1.0.0')

        bintray_resolve_version_mock.assert_called_with('username', 'password', 'org', 'repo', 'package-name',
                                                        '1.0.0', None, None)


class TestBintrayResolveVersion(TestCase):
    def test_success(self):
        bintray_files_endpoint_response = [
            {
                'owner': 'typesafe',
                'repo': 'bundle',
                'package': 'reactive-maps-frontend',
                'version': 'v1-023f9da22',
                'path': 'download/path.zip'
            }
        ]
        get_json_mock = MagicMock(return_value=bintray_files_endpoint_response)

        with patch('conductr_cli.resolvers.bintray_resolver.get_json', get_json_mock):
            result = bintray_resolver.bintray_resolve_version('username', 'password',
                                                              'typesafe', 'bundle', 'reactive-maps-frontend',
                                                              None, 'v1', '023f9da22')
            self.assertEqual(result, {
                'org': 'typesafe',
                'repo': 'bundle',
                'package_name': 'reactive-maps-frontend',
                'compatibility_version': 'v1',
                'digest': '023f9da22',
                'version': 'v1-023f9da22',
                'path': 'download/path.zip',
                'resolver': bintray_resolver.__name__
            })

        get_json_mock.assert_called_with(
            'https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend/versions/v1-023f9da22/files',
            'username', 'password')

    def test_failure_version_not_found(self):
        bintray_files_endpoint_response = [
            {
                'owner': 'typesafe',
                'repo': 'bundle',
                'package': 'reactive-maps-frontend',
                'version': 'SOMETHING ELSE',
                'path': 'download/path.zip'
            }
        ]
        get_json_mock = MagicMock(return_value=bintray_files_endpoint_response)

        with patch('conductr_cli.resolvers.bintray_resolver.get_json', get_json_mock):
            self.assertRaises(BintrayResolutionError, bintray_resolver.bintray_resolve_version, 'username', 'password',
                              'typesafe', 'bundle', 'reactive-maps-frontend', None, 'v1', '023f9da22')

        get_json_mock.assert_called_with(
            'https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend/versions/v1-023f9da22/files',
            'username', 'password')

    def test_failure_multiple_versions_found(self):
        bintray_files_endpoint_response = [
            {
                'owner': 'typesafe',
                'repo': 'bundle',
                'package': 'reactive-maps-frontend',
                'version': 'v1-023f9da22',
                'path': 'download/path-1.zip'
            },
            {
                'owner': 'typesafe',
                'repo': 'bundle',
                'package': 'reactive-maps-frontend',
                'version': 'v1-023f9da22',
                'path': 'download/path-2.zip'
            }
        ]
        get_json_mock = MagicMock(return_value=bintray_files_endpoint_response)

        with patch('conductr_cli.resolvers.bintray_resolver.get_json', get_json_mock):
            self.assertRaises(BintrayResolutionError, bintray_resolver.bintray_resolve_version, 'username', 'password',
                              'typesafe', 'bundle', 'reactive-maps-frontend', None, 'v1', '023f9da22')

        get_json_mock.assert_called_with(
            'https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend/versions/v1-023f9da22/files',
            'username', 'password')


class TestBintrayResolveVersionLatest(TestCase):
    def test_success(self):
        package_endpoint_response = {
            'latest_version': 'v1-023f9da22'
        }
        bintray_files_endpoint_response = [
            {
                'owner': 'typesafe',
                'repo': 'bundle',
                'package': 'reactive-maps-frontend',
                'version': 'v1-023f9da22',
                'path': 'download/path.zip'
            }
        ]
        get_json_mock = MagicMock(side_effect=[package_endpoint_response, bintray_files_endpoint_response])

        with patch('conductr_cli.resolvers.bintray_resolver.get_json', get_json_mock):
            result = bintray_resolver.bintray_resolve_version('username', 'password',
                                                              'typesafe', 'bundle', 'reactive-maps-frontend',
                                                              None, None, None)
            self.assertEqual(result, {
                'org': 'typesafe',
                'repo': 'bundle',
                'package_name': 'reactive-maps-frontend',
                'compatibility_version': 'v1',
                'digest': '023f9da22',
                'version': 'v1-023f9da22',
                'path': 'download/path.zip',
                'resolver': bintray_resolver.__name__
            })

        self.assertEqual(
            get_json_mock.call_args_list,
            [
                call('https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend', 'username', 'password'),
                call('https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend/versions/v1-023f9da22/files',
                     'username', 'password')
            ]
        )

    def test_latest_version_from_attribute_names(self):
        package_endpoint_response = {
            'latest_version': '',
            'attribute_names': [
                'latest-v9',
                'latest-v10'
            ]
        }
        bintray_attributes_v10_endpoint_response = [
            {
                'name': 'latest-v10',
                'type': 'version',
                'values': [
                    'v10-023f9da22'
                ]
            }
        ]
        bintray_files_v10_endpoint_response = [
            {
                'owner': 'typesafe',
                'repo': 'bundle',
                'package': 'reactive-maps-frontend',
                'version': 'v10-023f9da22',
                'path': 'download/path.zip'
            }
        ]
        get_json_mock = MagicMock(side_effect=[package_endpoint_response, bintray_attributes_v10_endpoint_response,
                                               bintray_files_v10_endpoint_response])

        with patch('conductr_cli.resolvers.bintray_resolver.get_json', get_json_mock):
            result = bintray_resolver.bintray_resolve_version('username', 'password',
                                                              'typesafe', 'bundle', 'reactive-maps-frontend',
                                                              None, None, None)
            self.assertEqual(result, {
                'org': 'typesafe',
                'repo': 'bundle',
                'package_name': 'reactive-maps-frontend',
                'compatibility_version': 'v10',
                'digest': '023f9da22',
                'version': 'v10-023f9da22',
                'path': 'download/path.zip',
                'resolver': bintray_resolver.__name__
            })

        self.assertEqual(
            get_json_mock.call_args_list,
            [
                call('https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend', 'username', 'password'),
                call('https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend/attributes?names=latest-v10',
                     'username', 'password'),
                call('https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend/versions/v10-023f9da22/files',
                     'username', 'password')
            ]
        )

    def test_latest_version_from_attribute_names_not_found(self):
        package_endpoint_response = {
            'latest_version': '',
            'attribute_names': [
                'dummy'
            ]
        }
        get_json_mock = MagicMock(return_value=package_endpoint_response)

        with patch('conductr_cli.resolvers.bintray_resolver.get_json', get_json_mock):
            self.assertRaises(BintrayResolutionError, bintray_resolver.bintray_resolve_version, 'username', 'password',
                              'typesafe', 'bundle', 'reactive-maps-frontend', None, None, None)

        get_json_mock.assert_called_with('https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend',
                                         'username', 'password')

    def test_failure_latest_version_malformed(self):
        package_endpoint_response = {
            'latest_version': 'IAMBROKEN'
        }
        get_json_mock = MagicMock(return_value=package_endpoint_response)

        with patch('conductr_cli.resolvers.bintray_resolver.get_json', get_json_mock):
            self.assertRaises(BintrayResolutionError, bintray_resolver.bintray_resolve_version, 'username', 'password',
                              'typesafe', 'bundle', 'reactive-maps-frontend', None, None, None)

        get_json_mock.assert_called_with('https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend',
                                         'username', 'password')


class TestBintrayResolveVersionLatestCompatibilityVersion(TestCase):
    def test_success(self):
        bintray_attributes_endpoint_response = [
            {
                'name': 'latest-v1',
                'type': 'version',
                'values': [
                    'v1-023f9da22'
                ]
            }
        ]
        bintray_files_endpoint_response = [
            {
                'owner': 'typesafe',
                'repo': 'bundle',
                'package': 'reactive-maps-frontend',
                'version': 'v1-023f9da22',
                'path': 'download/path.zip'
            }
        ]
        get_json_mock = MagicMock(side_effect=[bintray_attributes_endpoint_response, bintray_files_endpoint_response])

        with patch('conductr_cli.resolvers.bintray_resolver.get_json', get_json_mock):
            result = bintray_resolver.bintray_resolve_version('username', 'password', 'typesafe', 'bundle',
                                                              'reactive-maps-frontend', None, 'v1', None)
            self.assertEqual(result, {
                'org': 'typesafe',
                'repo': 'bundle',
                'package_name': 'reactive-maps-frontend',
                'compatibility_version': 'v1',
                'digest': '023f9da22',
                'version': 'v1-023f9da22',
                'path': 'download/path.zip',
                'resolver': bintray_resolver.__name__
            })

        self.assertEqual(
            get_json_mock.call_args_list,
            [
                call('https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend/attributes?names=latest-v1',
                     'username', 'password'),
                call('https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend/versions/v1-023f9da22/files',
                     'username', 'password')
            ]
        )

    def test_no_version(self):
        bintray_attributes_endpoint_response = {
        }
        get_json_mock = MagicMock(return_value=bintray_attributes_endpoint_response)

        with patch('conductr_cli.resolvers.bintray_resolver.get_json', get_json_mock):
            result = bintray_resolver.bintray_resolve_version('username', 'password', 'typesafe', 'bundle',
                                                              'reactive-maps-frontend', None, 'v1', None)
            self.assertIsNone(result)

        get_json_mock.assert_called_with('https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend/attributes?names=latest-v1',
                                         'username', 'password')


class TestResolveBundleVersion(TestCase):
    def test_resolved_version_found(self):
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        resolved_version = {
            'org': 'typesafe',
            'repo': 'bundle',
            'package_name': 'bundle-name',
            'compatibility_version': 'v1',
            'digest': 'digest',
            'version': 'v1-digest',
            'path': 'path/to/download.zip'
        }
        bintray_resolve_version_mock = MagicMock(return_value=resolved_version)

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            result = bintray_resolver.resolve_bundle_version('bundle-name:v1')
            self.assertEqual(resolved_version, result)

        load_bintray_credentials_mock.assert_called_with()
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with('username', 'password', 'typesafe', 'bundle', 'bundle-name',
                                                        compatibility_version='v1', digest='digest')

    def test_resolved_version_not_found(self):
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(return_value=None)

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            result = bintray_resolver.resolve_bundle_version('bundle-name:v1')
            self.assertIsNone(result)

        load_bintray_credentials_mock.assert_called_with()
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with('username', 'password', 'typesafe', 'bundle', 'bundle-name',
                                                        compatibility_version='v1', digest='digest')

    def test_malformed_bundle_uri_error(self):
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(side_effect=MalformedBundleUriError('test'))

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            result = bintray_resolver.resolve_bundle_version('bundle-name:v1')
            self.assertIsNone(result)

        load_bintray_credentials_mock.assert_called_with()
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with('username', 'password', 'typesafe', 'bundle', 'bundle-name',
                                                        compatibility_version='v1', digest='digest')

    def test_http_error(self):
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(side_effect=HTTPError('test'))

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            result = bintray_resolver.resolve_bundle_version('bundle-name:v1')
            self.assertIsNone(result)

        load_bintray_credentials_mock.assert_called_with()
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with('username', 'password', 'typesafe', 'bundle', 'bundle-name',
                                                        compatibility_version='v1', digest='digest')


class TestContinuousDeliveryUri(TestCase):
    def test_return_uri(self):
        result = bintray_resolver.continuous_delivery_uri({
            'org': 'typesafe',
            'repo': 'bundle',
            'resolver': bintray_resolver.__name__
        })
        self.assertEqual(result, 'deployments/typesafe/bundle/typesafe')

    def test_return_none_if_input_is_from_different_resolver(self):
        self.assertIsNone(
            bintray_resolver.continuous_delivery_uri({
                'org': 'typesafe',
                'repo': 'bundle',
                'resolver': 'my-own-custom'
            })
        )

    def test_return_none_if_input_is_invalid(self):
        self.assertIsNone(
            bintray_resolver.continuous_delivery_uri({
                'repo': 'bundle',
                'resolver': bintray_resolver.__name__
            })
        )
        self.assertIsNone(
            bintray_resolver.continuous_delivery_uri({
                'org': 'typesafe',
                'resolver': bintray_resolver.__name__
            })
        )
        self.assertIsNone(
            bintray_resolver.continuous_delivery_uri({
                'org': 'typesafe',
                'repo': 'bundle'
            })
        )

    def test_return_none_if_input_is_none(self):
        self.assertIsNone(bintray_resolver.continuous_delivery_uri(None))


class TestLoadBintrayCredentials(TestCase):
    def test_success(self):
        bintray_credential_file = strip_margin(
            """|user = user1
               |password = sec=ret
               |# Some comment
               |""")

        exists_mock = MagicMock(return_value=True)
        open_mock = MagicMock(return_value=io.StringIO(bintray_credential_file))

        with patch('os.path.exists', exists_mock), \
                patch('builtins.open', open_mock):
            username, password = bintray_resolver.load_bintray_credentials()
            self.assertEqual('user1', username)
            self.assertEqual('sec=ret', password)

        exists_mock.assert_called_with('{}/.lightbend/commercial.credentials'.format(os.path.expanduser('~')))
        open_mock.assert_called_with('{}/.lightbend/commercial.credentials'.format(os.path.expanduser('~')), 'r')

    def test_credential_file_not_having_username_password(self):
        bintray_credential_file = strip_margin(
            """|dummy = yes
               |""")

        exists_mock = MagicMock(return_value=True)
        open_mock = MagicMock(return_value=io.StringIO(bintray_credential_file))

        with patch('os.path.exists', exists_mock), \
                patch('builtins.open', open_mock):
            self.assertRaises(MalformedBintrayCredentialsError, bintray_resolver.load_bintray_credentials)

        exists_mock.assert_called_with('{}/.lightbend/commercial.credentials'.format(os.path.expanduser('~')))
        open_mock.assert_called_with('{}/.lightbend/commercial.credentials'.format(os.path.expanduser('~')), 'r')

    def test_missing_credential_file(self):
        exists_mock = MagicMock(return_value=False)

        with patch('os.path.exists', exists_mock):
            self.assertRaises(BintrayCredentialsNotFoundError, bintray_resolver.load_bintray_credentials)

        exists_mock.assert_called_with('{}/.lightbend/commercial.credentials'.format(os.path.expanduser('~')))


class TestGetJson(TestCase):
    def test_get_json(self):
        response_mock = Mock()
        response_raise_for_status_mock = MagicMock()
        response_mock.raise_for_status = response_raise_for_status_mock
        response_mock.text = '[1,2,3]'

        requests_get_mock = MagicMock(return_value=response_mock)
        with patch('requests.get', requests_get_mock):
            result = bintray_resolver.get_json('http://site.com', 'username', 'password')
            self.assertEqual([1, 2, 3], result)

        requests_get_mock.assert_called_with('http://site.com', auth=('username', 'password'))
        response_raise_for_status_mock.assert_called_with()

    def test_get_json_no_credentials(self):
        response_mock = Mock()
        response_raise_for_status_mock = MagicMock()
        response_mock.raise_for_status = response_raise_for_status_mock
        response_mock.text = '[1,2,3]'

        requests_get_mock = MagicMock(return_value=response_mock)
        with patch('requests.get', requests_get_mock):
            result = bintray_resolver.get_json('http://site.com', None, None)
            self.assertEqual([1, 2, 3], result)

        requests_get_mock.assert_called_with('http://site.com')
        response_raise_for_status_mock.assert_called_with()
