from unittest import TestCase
from conductr_cli.test.cli_test_case import strip_margin
from conductr_cli.resolvers import bintray_resolver
from conductr_cli.resolvers.schemes import SCHEME_BUNDLE
from conductr_cli.exceptions import MalformedBundleUriError, BintrayResolutionError, MalformedBintrayCredentialsError, \
    BintrayCredentialsNotFoundError
from requests.exceptions import HTTPError, ConnectionError
import io
import os
from unittest.mock import call, patch, MagicMock, Mock


class TestResolveBundle(TestCase):
    bintray_auth = ('realm', 'username', 'password')
    bintray_no_auth = (None, None, None)

    def test_bintray_version_found(self):
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_auth)
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(return_value={
            'org': 'typesafe',
            'repo': 'bundle',
            'package_name': 'bundle-name',
            'tag': 'v1',
            'digest': 'digest',
            'version': 'v1-digest',
            'path': 'download.zip',
            'download_url': 'https://dl.bintray.com/typesafe/bundle/download.zip'
        })
        resolve_bundle_mock = MagicMock(return_value=(True, 'bundle-name', 'mock bundle file', None))

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.uri_resolver.resolve_file', resolve_bundle_mock):
            result = bintray_resolver.resolve_bundle('/cache-dir', 'bundle-name:v1')
            self.assertEqual((True, 'bundle-name', 'mock bundle file', None), result)

        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_auth, 'typesafe', 'bundle', 'bundle-name',
                                                        'v1', 'digest')
        resolve_bundle_mock.assert_called_with('/cache-dir', 'https://dl.bintray.com/typesafe/bundle/download.zip',
                                               self.bintray_auth, False)

    def test_bintray_version_not_found(self):
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_auth)
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(return_value=None)

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            result = bintray_resolver.resolve_bundle('/cache-dir', 'bundle-name:v1')
            self.assertEqual((False, None, None, None), result)

        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_auth, 'typesafe', 'bundle', 'bundle-name',
                                                        'v1', 'digest')

    def test_failure_malformed_bundle_uri(self):
        error = MalformedBundleUriError('test only')
        parse_bundle_mock = MagicMock(side_effect=error)

        with patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock):
            result = bintray_resolver.resolve_bundle('/cache-dir', 'bundle-name:v1')
            self.assertEqual((False, None, None, error), result)

        parse_bundle_mock.assert_called_with('bundle-name:v1')

    def test_failure_http_error_repo_not_found(self):
        exists_mock = MagicMock(return_value=False)
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_no_auth)
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        error = HTTPError(response=MagicMock(text='Repo bundle was not found', status_code=404))
        bintray_resolve_version_mock = MagicMock(side_effect=error)

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            self.assertEqual(bintray_resolver.resolve_bundle('/cache-dir', 'bundle-name:v1'),
                             (False, None, None, error))

        exists_mock.assert_not_called()
        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        bintray_resolve_version_mock.assert_called_with(self.bintray_no_auth, 'typesafe', 'bundle',
                                                        'bundle-name', 'v1', 'digest')

    def test_failure_http_error(self):
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_auth)
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        error = HTTPError(response=MagicMock(text='', status_code=404))
        bintray_resolve_version_mock = MagicMock(side_effect=error)

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            result = bintray_resolver.resolve_bundle('/cache-dir', 'bundle-name:v1')
            self.assertEqual((False, None, None, error), result)

        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_auth, 'typesafe', 'bundle', 'bundle-name',
                                                        'v1', 'digest')

    def test_connection_error(self):
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_auth)
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        error = ConnectionError('test only')
        bintray_resolve_version_mock = MagicMock(side_effect=error)

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            result = bintray_resolver.resolve_bundle('/cache-dir', 'bundle-name:v1')
            self.assertEqual((False, None, None, error), result)

        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_auth, 'typesafe', 'bundle', 'bundle-name',
                                                        'v1', 'digest')


class TestResolveBundleConfiguration(TestCase):
    bintray_auth = ('realm', 'username', 'password')
    bintray_no_auth = (None, None, None)

    def test_bintray_version_found(self):
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_auth)
        parse_bundle_configuration_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle-configuration',
                                                                  'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(return_value={
            'org': 'typesafe',
            'repo': 'bundle-configuration',
            'package_name': 'bundle-name',
            'tag': 'v1',
            'digest': 'digest',
            'path': 'download.zip',
            'download_url': 'https://dl.bintray.com/typesafe/bundle-configuration/download.zip'
        })
        resolve_bundle_mock = MagicMock(return_value=(True, 'bundle-name', 'mock bundle file', None))

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle_configuration', parse_bundle_configuration_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.uri_resolver.resolve_file', resolve_bundle_mock):
            result = bintray_resolver.resolve_bundle_configuration('/cache-dir', 'bundle-name:v1')
            self.assertEqual((True, 'bundle-name', 'mock bundle file', None), result)

        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_configuration_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_auth, 'typesafe', 'bundle-configuration',
                                                        'bundle-name', 'v1', 'digest')
        resolve_bundle_mock.assert_called_with('/cache-dir',
                                               'https://dl.bintray.com/typesafe/bundle-configuration/download.zip',
                                               self.bintray_auth,
                                               False)

    def test_bintray_version_not_found(self):
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_auth)
        parse_bundle_configuration_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle-configuration',
                                                                  'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(return_value=None)

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle_configuration', parse_bundle_configuration_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            result = bintray_resolver.resolve_bundle_configuration('/cache-dir', 'bundle-name:v1')
            self.assertEqual((False, None, None, None), result)

        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_configuration_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_auth, 'typesafe', 'bundle-configuration',
                                                        'bundle-name', 'v1', 'digest')

    def test_failure_malformed_bundle_uri(self):
        error = MalformedBundleUriError('test only')
        parse_bundle_configuration_mock = MagicMock(side_effect=error)

        with patch('conductr_cli.bundle_shorthand.parse_bundle_configuration', parse_bundle_configuration_mock):
            result = bintray_resolver.resolve_bundle_configuration('/cache-dir', 'bundle-name:v1')
            self.assertEqual((False, None, None, error), result)

        parse_bundle_configuration_mock.assert_called_with('bundle-name:v1')

    def test_failure_http_error_repo_not_found(self):
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_no_auth)
        parse_bundle_configuration_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle-configuration',
                                                                  'bundle-name', 'v1', 'digest'))
        error = HTTPError(response=MagicMock(text='Repo bundle-configuration was not found', status_code=404))
        bintray_resolve_version_mock = MagicMock(side_effect=error)

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle_configuration', parse_bundle_configuration_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            self.assertEqual(bintray_resolver.resolve_bundle_configuration('/cache-dir', 'bundle-name:v1'),
                             (False, None, None, error))

        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_configuration_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_no_auth, 'typesafe', 'bundle-configuration',
                                                        'bundle-name', 'v1', 'digest')

    def test_failure_http_error(self):
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_auth)
        parse_bundle_configuration_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle-configuration',
                                                                  'bundle-name', 'v1', 'digest'))
        error = HTTPError(response=MagicMock(text='', status_code=404))
        bintray_resolve_version_mock = MagicMock(side_effect=error)

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle_configuration', parse_bundle_configuration_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            result = bintray_resolver.resolve_bundle_configuration('/cache-dir', 'bundle-name:v1')
            self.assertEqual((False, None, None, error), result)

        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_configuration_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_auth, 'typesafe', 'bundle-configuration',
                                                        'bundle-name', 'v1', 'digest')

    def test_failure_connection_error(self):
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_auth)
        parse_bundle_configuration_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle-configuration',
                                                                  'bundle-name', 'v1', 'digest'))
        error = ConnectionError('test only')
        bintray_resolve_version_mock = MagicMock(side_effect=error)

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle_configuration', parse_bundle_configuration_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            result = bintray_resolver.resolve_bundle_configuration('/cache-dir', 'bundle-name:v1')
            self.assertEqual((False, None, None, error), result)

        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_configuration_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_auth, 'typesafe', 'bundle-configuration',
                                                        'bundle-name', 'v1', 'digest')


class TestLoadBundleFromCache(TestCase):
    bintray_auth = ('realm', 'username', 'password')
    bintray_no_auth = (None, None, None)

    def test_file(self):
        exists_mock = MagicMock(return_value=True)
        isfile_mock = MagicMock(return_value=True)
        parse_bundle_mock = MagicMock()

        with patch('os.path.exists', exists_mock), \
                patch('os.path.isfile', isfile_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock):
            result = bintray_resolver.load_bundle_from_cache('/cache-dir', '/tmp/bundle.zip')
            self.assertEqual((False, None, None, None), result)

        exists_mock.assert_called_with('/tmp/bundle.zip')
        parse_bundle_mock.assert_not_called()

    def test_file_exists_but_no_conf_do_bintray(self):
        exists_mock = MagicMock(return_value=True)
        isfile_mock = MagicMock(return_value=False)
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(return_value=None)
        credentials_mock = MagicMock()

        with patch('os.path.exists', exists_mock), \
                patch('os.path.isfile', isfile_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', credentials_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            result = bintray_resolver.resolve_bundle('/cache-dir', 'bundle')
            self.assertEqual((False, None, None, None), result)

        credentials_mock.assert_called_with(raise_error=False)

    def test_bundle(self):
        exists_mock = MagicMock(return_value=False)
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_auth)
        bintray_resolve_version_mock = MagicMock(return_value=None)

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            bintray_resolver.load_bundle_from_cache(
                '/cache-dir', '/tmp/bundle')

        exists_mock.assert_called_once_with('/tmp/bundle')

    def test_bintray_version_found(self):
        exists_mock = MagicMock(return_value=False)
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_auth)
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(return_value={
            'org': 'typesafe',
            'repo': 'bundle',
            'package_name': 'bundle-name',
            'tag': 'v1',
            'digest': 'digest',
            'path': 'download.zip',
            'download_url': 'https://dl.bintray.com/typesafe/bundle/download.zip'
        })
        load_bundle_from_cache_mock = MagicMock(return_value=(True, 'bundle-name', 'mock bundle file', None))

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.uri_resolver.load_bundle_from_cache',
                      load_bundle_from_cache_mock):
            result = bintray_resolver.load_bundle_from_cache('/cache-dir', 'bundle-name:v1')
            self.assertEqual((True, 'bundle-name', 'mock bundle file', None), result)

        exists_mock.assert_not_called()
        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_auth, 'typesafe', 'bundle', 'bundle-name',
                                                        'v1', 'digest')
        load_bundle_from_cache_mock.assert_called_with('/cache-dir',
                                                       'https://dl.bintray.com/typesafe/bundle/download.zip')

    def test_bintray_version_not_found(self):
        exists_mock = MagicMock(return_value=False)
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_auth)
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(return_value=None)

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            result = bintray_resolver.load_bundle_from_cache('/cache-dir', 'bundle-name:v1')
            self.assertEqual((False, None, None, None), result)

        exists_mock.assert_not_called()
        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_auth, 'typesafe', 'bundle', 'bundle-name',
                                                        'v1', 'digest')

    def test_failure_malformed_bundle_uri(self):
        exists_mock = MagicMock(return_value=False)
        error = MalformedBundleUriError('test only')
        parse_bundle_mock = MagicMock(side_effect=error)

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock):
            result = bintray_resolver.load_bundle_from_cache('/cache-dir', 'bundle-name:v1')
            self.assertEqual((False, None, None, error), result)

        exists_mock.assert_not_called()
        parse_bundle_mock.assert_called_with('bundle-name:v1')

    def test_failure_http_error_repo_not_found(self):
        exists_mock = MagicMock(return_value=False)
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_no_auth)
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        error = HTTPError(response=MagicMock(text='Repo bundle was not found', status_code=404))
        bintray_resolve_version_mock = MagicMock(side_effect=error)

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            self.assertEqual(bintray_resolver.load_bundle_from_cache('/cache-dir', 'bundle-name:v1'),
                             (False, None, None, error))

        exists_mock.assert_not_called()
        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_no_auth, 'typesafe', 'bundle',
                                                        'bundle-name', 'v1', 'digest')

    def test_failure_http_error(self):
        exists_mock = MagicMock(return_value=False)
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_auth)
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        error = HTTPError(response=MagicMock(text='', status_code=404))
        bintray_resolve_version_mock = MagicMock(side_effect=error)

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            result = bintray_resolver.load_bundle_from_cache('/cache-dir', 'bundle-name:v1')
            self.assertEqual((False, None, None, error), result)

        exists_mock.assert_not_called()
        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_auth, 'typesafe', 'bundle', 'bundle-name',
                                                        'v1', 'digest')

    def test_failure_connection_error(self):
        exists_mock = MagicMock(return_value=False)
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_auth)
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        error = ConnectionError('test only')
        bintray_resolve_version_mock = MagicMock(side_effect=error)

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            result = bintray_resolver.load_bundle_from_cache('/cache-dir', 'bundle-name:v1')
            self.assertEqual((False, None, None, error), result)

        exists_mock.assert_not_called()
        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_auth, 'typesafe', 'bundle', 'bundle-name',
                                                        'v1', 'digest')


class TestLoadBundleConfigurationFromCache(TestCase):
    bintray_auth = ('realm', 'username', 'password')
    bintray_no_auth = (None, None, None)

    def test_file(self):
        exists_mock = MagicMock(return_value=True)
        isfile_mock = MagicMock(return_value=True)
        parse_bundle_configuration_mock = MagicMock()

        with patch('os.path.exists', exists_mock), \
                patch('os.path.isfile', isfile_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle_configuration', parse_bundle_configuration_mock):
            result = bintray_resolver.load_bundle_configuration_from_cache('/cache-dir', '/tmp/bundle.zip')
            self.assertEqual((False, None, None, None), result)

        exists_mock.assert_called_with('/tmp/bundle.zip')
        parse_bundle_configuration_mock.assert_not_called()

    def test_bintray_version_found(self):
        exists_mock = MagicMock(return_value=False)
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_auth)
        parse_bundle_configuration_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle-configuration',
                                                                  'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(return_value={
            'org': 'typesafe',
            'repo': 'bundle-configuration',
            'package_name': 'bundle-name',
            'tag': 'v1',
            'digest': 'digest',
            'path': 'download.zip',
            'download_url': 'https://dl.bintray.com/typesafe/bundle-configuration/download.zip'
        })
        load_bundle_from_cache_mock = MagicMock(return_value=(True, 'bundle-name', 'mock bundle file', None))

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle_configuration', parse_bundle_configuration_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.uri_resolver.load_bundle_from_cache',
                      load_bundle_from_cache_mock):
            result = bintray_resolver.load_bundle_configuration_from_cache('/cache-dir', 'bundle-name:v1')
            self.assertEqual((True, 'bundle-name', 'mock bundle file', None), result)

        exists_mock.assert_not_called()
        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_configuration_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_auth, 'typesafe', 'bundle-configuration',
                                                        'bundle-name', 'v1', 'digest')
        load_bundle_from_cache_mock.assert_called_with('/cache-dir',
                                                       'https://dl.bintray.com/typesafe/bundle-configuration/download.zip')

    def test_bintray_version_not_found(self):
        exists_mock = MagicMock(return_value=False)
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_auth)
        parse_bundle_configuration_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle-configuration',
                                                                  'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(return_value=None)

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle_configuration', parse_bundle_configuration_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            result = bintray_resolver.load_bundle_configuration_from_cache('/cache-dir', 'bundle-name:v1')
            self.assertEqual((False, None, None, None), result)

        exists_mock.assert_not_called()
        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_configuration_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_auth, 'typesafe', 'bundle-configuration',
                                                        'bundle-name', 'v1', 'digest')

    def test_failure_malformed_bundle_uri(self):
        exists_mock = MagicMock(return_value=False)
        error = MalformedBundleUriError('test only')
        parse_bundle_mock = MagicMock(side_effect=error)

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock):
            result = bintray_resolver.load_bundle_from_cache('/cache-dir', 'bundle-name:v1')
            self.assertEqual((False, None, None, error), result)

        exists_mock.assert_not_called()
        parse_bundle_mock.assert_called_with('bundle-name:v1')

    def test_failure_http_error_repo_not_found(self):
        exists_mock = MagicMock(return_value=False)
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_no_auth)
        parse_bundle_configuration_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle-configuration',
                                                                  'bundle-name', 'v1', 'digest'))
        error = HTTPError(response=MagicMock(text='Repo bundle-configuration was not found', status_code=404))
        bintray_resolve_version_mock = MagicMock(side_effect=error)

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle_configuration', parse_bundle_configuration_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            self.assertEqual(
                bintray_resolver.load_bundle_configuration_from_cache('/cache-dir', 'bundle-name:v1'),
                (False, None, None, error)
            )

        exists_mock.assert_not_called()
        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_configuration_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_no_auth, 'typesafe', 'bundle-configuration',
                                                        'bundle-name', 'v1', 'digest')

    def test_failure_http_error(self):
        exists_mock = MagicMock(return_value=False)
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_auth)
        parse_bundle_configuration_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle-configuration',
                                                    'bundle-name', 'v1', 'digest'))
        error = HTTPError(response=MagicMock(text='', status_code=404))
        bintray_resolve_version_mock = MagicMock(side_effect=error)

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle_configuration', parse_bundle_configuration_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            result = bintray_resolver.load_bundle_configuration_from_cache('/cache-dir', 'bundle-name:v1')
            self.assertEqual((False, None, None, error), result)

        exists_mock.assert_not_called()
        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_configuration_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_auth, 'typesafe', 'bundle-configuration',
                                                        'bundle-name', 'v1', 'digest')

    def test_failure_connection_error(self):
        exists_mock = MagicMock(return_value=False)
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_auth)
        parse_bundle_configuration_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle-configuration',
                                                                  'bundle-name', 'v1', 'digest'))
        error = ConnectionError('test only')
        bintray_resolve_version_mock = MagicMock(side_effect=error)

        with patch('os.path.exists', exists_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle_configuration', parse_bundle_configuration_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            result = bintray_resolver.load_bundle_configuration_from_cache('/cache-dir', 'bundle-name:v1')
            self.assertEqual((False, None, None, error), result)

        exists_mock.assert_not_called()
        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_configuration_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_auth, 'typesafe', 'bundle-configuration',
                                                        'bundle-name', 'v1', 'digest')


class TestBintrayResolveVersion(TestCase):
    bintray_auth = ('Bintray', 'username', 'password')

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
            result = bintray_resolver.bintray_resolve_version(self.bintray_auth,
                                                              'typesafe', 'bundle', 'reactive-maps-frontend',
                                                              'v1', '023f9da22')
            self.assertEqual(result, {
                'org': 'typesafe',
                'repo': 'bundle',
                'package_name': 'reactive-maps-frontend',
                'tag': 'v1',
                'digest': '023f9da22',
                'version': 'v1-023f9da22',
                'path': 'download/path.zip',
                'download_url': 'https://dl.bintray.com/typesafe/bundle/download/path.zip',
                'resolver': bintray_resolver.__name__
            })

        get_json_mock.assert_called_with(
            self.bintray_auth,
            'https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend/versions/v1-023f9da22/files')

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
            self.assertRaises(BintrayResolutionError, bintray_resolver.bintray_resolve_version, self.bintray_auth,
                              'typesafe', 'bundle', 'reactive-maps-frontend', 'v1', '023f9da22')

        get_json_mock.assert_called_with(
            self.bintray_auth,
            'https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend/versions/v1-023f9da22/files')

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
            self.assertRaises(BintrayResolutionError, bintray_resolver.bintray_resolve_version, self.bintray_auth,
                              'typesafe', 'bundle', 'reactive-maps-frontend', 'v1', '023f9da22')

        get_json_mock.assert_called_with(
            self.bintray_auth,
            'https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend/versions/v1-023f9da22/files')


class TestBintrayResolveVersionLatest(TestCase):
    bintray_auth = ('Bintray', 'username', 'password')

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
            result = bintray_resolver.bintray_resolve_version(self.bintray_auth,
                                                              'typesafe', 'bundle', 'reactive-maps-frontend',
                                                              None, None)
            self.assertEqual(result, {
                'org': 'typesafe',
                'repo': 'bundle',
                'package_name': 'reactive-maps-frontend',
                'tag': 'v1',
                'digest': '023f9da22',
                'version': 'v1-023f9da22',
                'path': 'download/path.zip',
                'download_url': 'https://dl.bintray.com/typesafe/bundle/download/path.zip',
                'resolver': bintray_resolver.__name__
            })

        self.assertEqual(
            get_json_mock.call_args_list,
            [
                call(self.bintray_auth,
                     'https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend'),
                call(self.bintray_auth,
                     'https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend/versions/v1-023f9da22/files')
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
            result = bintray_resolver.bintray_resolve_version(self.bintray_auth,
                                                              'typesafe', 'bundle', 'reactive-maps-frontend',
                                                              None, None)
            self.assertEqual(result, {
                'org': 'typesafe',
                'repo': 'bundle',
                'package_name': 'reactive-maps-frontend',
                'tag': 'v10',
                'digest': '023f9da22',
                'version': 'v10-023f9da22',
                'path': 'download/path.zip',
                'download_url': 'https://dl.bintray.com/typesafe/bundle/download/path.zip',
                'resolver': bintray_resolver.__name__
            })

        self.assertEqual(
            get_json_mock.call_args_list,
            [
                call(self.bintray_auth,
                     'https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend'),
                call(self.bintray_auth,
                     'https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend/attributes?names=latest-v10'),
                call(self.bintray_auth,
                     'https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend/versions/v10-023f9da22/files')
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
            self.assertRaises(BintrayResolutionError, bintray_resolver.bintray_resolve_version, self.bintray_auth,
                              'typesafe', 'bundle', 'reactive-maps-frontend', None, None)

        get_json_mock.assert_called_with(self.bintray_auth,
                                         'https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend')

    def test_failure_latest_version_malformed(self):
        package_endpoint_response = {
            'latest_version': 'IAMBROKEN'
        }
        get_json_mock = MagicMock(return_value=package_endpoint_response)

        with patch('conductr_cli.resolvers.bintray_resolver.get_json', get_json_mock):
            self.assertRaises(BintrayResolutionError, bintray_resolver.bintray_resolve_version, self.bintray_auth,
                              'typesafe', 'bundle', 'reactive-maps-frontend', None, None)

        get_json_mock.assert_called_with(self.bintray_auth,
                                         'https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend')


class TestBintrayResolveVersionLatestCompatibilityVersion(TestCase):
    bintray_auth = ('Bintray', 'username', 'password')

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
            result = bintray_resolver.bintray_resolve_version(self.bintray_auth, 'typesafe', 'bundle',
                                                              'reactive-maps-frontend', 'v1')
            self.assertEqual(result, {
                'org': 'typesafe',
                'repo': 'bundle',
                'package_name': 'reactive-maps-frontend',
                'tag': 'v1',
                'digest': '023f9da22',
                'version': 'v1-023f9da22',
                'path': 'download/path.zip',
                'download_url': 'https://dl.bintray.com/typesafe/bundle/download/path.zip',
                'resolver': bintray_resolver.__name__
            })

        self.assertEqual(
            get_json_mock.call_args_list,
            [
                call(self.bintray_auth,
                     'https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend/attributes?names=latest-v1'),
                call(self.bintray_auth,
                     'https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend/versions/v1-023f9da22/files')
            ]
        )

    def test_no_version(self):
        bintray_attributes_endpoint_response = {
        }
        get_json_mock = MagicMock(return_value=bintray_attributes_endpoint_response)

        with patch('conductr_cli.resolvers.bintray_resolver.get_json', get_json_mock):
            result = bintray_resolver.bintray_resolve_version(self.bintray_auth, 'typesafe', 'bundle',
                                                              'reactive-maps-frontend', 'v1')
            self.assertIsNone(result)

        get_json_mock.assert_called_with(
            self.bintray_auth,
            'https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend/attributes?names=latest-v1')


class TestResolveBundleVersion(TestCase):
    bintray_auth = ('realm', 'username', 'password')

    def test_resolved_version_found(self):
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_auth)
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        resolved_version = {
            'org': 'typesafe',
            'repo': 'bundle',
            'package_name': 'bundle-name',
            'tag': 'v1',
            'digest': 'digest',
            'version': 'v1-digest',
            'path': 'path/to/download.zip'
        }
        bintray_resolve_version_mock = MagicMock(return_value=resolved_version)

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            result = bintray_resolver.resolve_bundle_version('bundle-name:v1')
            self.assertEqual((resolved_version, None), result)

        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_auth, 'typesafe', 'bundle', 'bundle-name',
                                                        tag='v1', digest='digest')

    def test_resolved_version_not_found(self):
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_auth)
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_resolve_version_mock = MagicMock(return_value=None)

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            result = bintray_resolver.resolve_bundle_version('bundle-name:v1')
            self.assertEqual((None, None), result)

        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_auth, 'typesafe', 'bundle', 'bundle-name',
                                                        tag='v1', digest='digest')

    def test_malformed_bundle_uri_error(self):
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_auth)
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        error = MalformedBundleUriError('test')
        bintray_resolve_version_mock = MagicMock(side_effect=error)

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            result = bintray_resolver.resolve_bundle_version('bundle-name:v1')
            self.assertEqual((None, error), result)

        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_auth, 'typesafe', 'bundle', 'bundle-name',
                                                        tag='v1', digest='digest')

    def test_http_error(self):
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_auth)
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        error = HTTPError('test')
        bintray_resolve_version_mock = MagicMock(side_effect=error)

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            result = bintray_resolver.resolve_bundle_version('bundle-name:v1')
            self.assertEqual((None, error), result)

        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_auth, 'typesafe', 'bundle', 'bundle-name',
                                                        tag='v1', digest='digest')

    def test_connection_error(self):
        load_bintray_credentials_mock = MagicMock(return_value=self.bintray_auth)
        parse_bundle_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        error = ConnectionError('test')
        bintray_resolve_version_mock = MagicMock(side_effect=error)

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse_bundle', parse_bundle_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_resolve_version', bintray_resolve_version_mock):
            result = bintray_resolver.resolve_bundle_version('bundle-name:v1')
            self.assertEqual((None, error), result)

        load_bintray_credentials_mock.assert_called_with(raise_error=False)
        parse_bundle_mock.assert_called_with('bundle-name:v1')
        bintray_resolve_version_mock.assert_called_with(self.bintray_auth, 'typesafe', 'bundle', 'bundle-name',
                                                        tag='v1', digest='digest')


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
            realm, username, password = bintray_resolver.load_bintray_credentials()
            self.assertEqual('Bintray', realm)
            self.assertEqual('user1', username)
            self.assertEqual('sec=ret', password)

        exists_mock.assert_called_with('{}/.lightbend/commercial.credentials'.format(os.path.expanduser('~')))
        open_mock.assert_called_with('{}/.lightbend/commercial.credentials'.format(os.path.expanduser('~')), 'r')

    def test_success_whitespace(self):
        bintray_credential_file = \
            ' user = user1  \n' \
            ' password = sec=ret \n' \
            '# Some comment'

        exists_mock = MagicMock(return_value=True)
        open_mock = MagicMock(return_value=io.StringIO(bintray_credential_file))

        with patch('os.path.exists', exists_mock), \
                patch('builtins.open', open_mock):
            realm, username, password = bintray_resolver.load_bintray_credentials()
            self.assertEqual('Bintray', realm)
            self.assertEqual('user1', username)
            self.assertEqual('sec=ret', password)

        exists_mock.assert_called_with('{}/.lightbend/commercial.credentials'.format(os.path.expanduser('~')))
        open_mock.assert_called_with('{}/.lightbend/commercial.credentials'.format(os.path.expanduser('~')), 'r')

    def test_success_multiple_realms(self):
        bintray_credential_file = (
            'realm = Bintray\n'
            'user = user1\n'
            'password = sec=ret\n'
            'realm = Bintray API Realm\n'
            'user = user2\n'
            'password = sec=ret2\n'
        )

        exists_mock = MagicMock(return_value=True)
        open_mock = MagicMock(return_value=io.StringIO(bintray_credential_file))

        with patch('os.path.exists', exists_mock), \
                patch('builtins.open', open_mock):
            realm, username, password = bintray_resolver.load_bintray_credentials()
            self.assertEqual('Bintray', realm)
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
    auth = ('realm', 'username', 'password')

    def test_get_json(self):
        response_mock = Mock()
        response_raise_for_status_mock = MagicMock()
        response_mock.raise_for_status = response_raise_for_status_mock
        response_mock.text = '[1,2,3]'

        requests_get_mock = MagicMock(return_value=response_mock)
        with patch('requests.get', requests_get_mock):
            result = bintray_resolver.get_json(self.auth, 'http://site.com')
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
            result = bintray_resolver.get_json(None, 'http://site.com')
            self.assertEqual([1, 2, 3], result)

        requests_get_mock.assert_called_with('http://site.com')
        response_raise_for_status_mock.assert_called_with()

    def test_get_json_missing_username(self):
        response_mock = Mock()
        response_raise_for_status_mock = MagicMock()
        response_mock.raise_for_status = response_raise_for_status_mock
        response_mock.text = '[1,2,3]'

        requests_get_mock = MagicMock(return_value=response_mock)
        with patch('requests.get', requests_get_mock):
            result = bintray_resolver.get_json(('realm', None, 'password'), 'http://site.com')
            self.assertEqual([1, 2, 3], result)

        requests_get_mock.assert_called_with('http://site.com')
        response_raise_for_status_mock.assert_called_with()

    def test_get_json_missing_password(self):
        response_mock = Mock()
        response_raise_for_status_mock = MagicMock()
        response_mock.raise_for_status = response_raise_for_status_mock
        response_mock.text = '[1,2,3]'

        requests_get_mock = MagicMock(return_value=response_mock)
        with patch('requests.get', requests_get_mock):
            result = bintray_resolver.get_json(('realm', 'username', None), 'http://site.com')
            self.assertEqual([1, 2, 3], result)

        requests_get_mock.assert_called_with('http://site.com')
        response_raise_for_status_mock.assert_called_with()


class TestSupportedSchemes(TestCase):
    def test_supported_schemes(self):
        self.assertEqual([SCHEME_BUNDLE], bintray_resolver.supported_schemes())
