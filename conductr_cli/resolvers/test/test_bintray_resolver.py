from unittest import TestCase
from conductr_cli.test.cli_test_case import strip_margin
from conductr_cli.resolvers import bintray_resolver
from conductr_cli.exceptions import MalformedBundleUriError, BintrayResolutionError
from requests.exceptions import HTTPError
import io
import os

try:
    from unittest.mock import call, patch, MagicMock, Mock  # 3.3 and beyond
except ImportError:
    from mock import call, patch, MagicMock, Mock


class TestResolveBundle(TestCase):
    def test_bintray_version_found(self):
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_download_url_mock = MagicMock(return_value='https://dl.bintray.com/download.zip')
        resolve_bundle_mock = MagicMock(return_value=(True, 'bundle-name', 'mock bundle file'))

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse', parse_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_download_url', bintray_download_url_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.uri_resolver.resolve_bundle', resolve_bundle_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.resolve_bundle('/cache-dir', 'bundle-name:v1')
            self.assertTrue(is_resolved)
            self.assertEqual('bundle-name', bundle_name)
            self.assertEqual('mock bundle file', bundle_file)

        load_bintray_credentials_mock.assert_called_with()
        parse_mock.assert_called_with('bundle-name:v1')
        bintray_download_url_mock.assert_called_with('username', 'password', 'typesafe', 'bundle', 'bundle-name', 'v1',
                                                     'digest')
        resolve_bundle_mock.assert_called_with('/cache-dir', 'https://dl.bintray.com/download.zip',
                                               ('Bintray', 'username', 'password'))

    def test_bintray_version_not_found(self):
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_download_url_mock = MagicMock(return_value=None)

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse', parse_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_download_url', bintray_download_url_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.resolve_bundle('/cache-dir', 'bundle-name:v1')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        load_bintray_credentials_mock.assert_called_with()
        parse_mock.assert_called_with('bundle-name:v1')
        bintray_download_url_mock.assert_called_with('username', 'password', 'typesafe', 'bundle', 'bundle-name', 'v1',
                                                     'digest')

    def test_failure_malformed_bundle_uri(self):
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_mock = MagicMock(side_effect=MalformedBundleUriError('test only'))

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse', parse_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.resolve_bundle('/cache-dir', 'bundle-name:v1')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        load_bintray_credentials_mock.assert_called_with()
        parse_mock.assert_called_with('bundle-name:v1')

    def test_failure_http_error(self):
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_download_url_mock = MagicMock(side_effect=HTTPError('test only'))

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse', parse_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_download_url', bintray_download_url_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.resolve_bundle('/cache-dir', 'bundle-name:v1')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        load_bintray_credentials_mock.assert_called_with()
        parse_mock.assert_called_with('bundle-name:v1')
        bintray_download_url_mock.assert_called_with('username', 'password', 'typesafe', 'bundle', 'bundle-name', 'v1',
                                                     'digest')


class TestLoadFromCache(TestCase):
    def test_bintray_version_found(self):
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_download_url_mock = MagicMock(return_value='https://dl.bintray.com/download.zip')
        load_from_cache_mock = MagicMock(return_value=(True, 'bundle-name', 'mock bundle file'))

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse', parse_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_download_url', bintray_download_url_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.uri_resolver.load_from_cache', load_from_cache_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.load_from_cache('/cache-dir', 'bundle-name:v1')
            self.assertTrue(is_resolved)
            self.assertEqual('bundle-name', bundle_name)
            self.assertEqual('mock bundle file', bundle_file)

        load_bintray_credentials_mock.assert_called_with()
        parse_mock.assert_called_with('bundle-name:v1')
        bintray_download_url_mock.assert_called_with('username', 'password', 'typesafe', 'bundle', 'bundle-name', 'v1',
                                                     'digest')
        load_from_cache_mock.assert_called_with('/cache-dir', 'https://dl.bintray.com/download.zip')

    def test_bintray_version_not_found(self):
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_download_url_mock = MagicMock(return_value=None)

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse', parse_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_download_url', bintray_download_url_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.load_from_cache('/cache-dir', 'bundle-name:v1')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        load_bintray_credentials_mock.assert_called_with()
        parse_mock.assert_called_with('bundle-name:v1')
        bintray_download_url_mock.assert_called_with('username', 'password', 'typesafe', 'bundle', 'bundle-name', 'v1',
                                                     'digest')

    def test_failure_malformed_bundle_uri(self):
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_mock = MagicMock(side_effect=MalformedBundleUriError('test only'))

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse', parse_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.load_from_cache('/cache-dir', 'bundle-name:v1')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        load_bintray_credentials_mock.assert_called_with()
        parse_mock.assert_called_with('bundle-name:v1')

    def test_failure_http_error(self):
        load_bintray_credentials_mock = MagicMock(return_value=('username', 'password'))
        parse_mock = MagicMock(return_value=('urn:x-bundle:', 'typesafe', 'bundle', 'bundle-name', 'v1', 'digest'))
        bintray_download_url_mock = MagicMock(side_effect=HTTPError('test only'))

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', load_bintray_credentials_mock), \
                patch('conductr_cli.bundle_shorthand.parse', parse_mock), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_download_url', bintray_download_url_mock):
            is_resolved, bundle_name, bundle_file = bintray_resolver.load_from_cache('/cache-dir', 'bundle-name:v1')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        load_bintray_credentials_mock.assert_called_with()
        parse_mock.assert_called_with('bundle-name:v1')
        bintray_download_url_mock.assert_called_with('username', 'password', 'typesafe', 'bundle', 'bundle-name', 'v1',
                                                     'digest')


class TestBintrayDownloadUrl(TestCase):
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
            result = bintray_resolver.bintray_download_url('username', 'password',
                                                           'typesafe', 'bundle', 'reactive-maps-frontend',
                                                           'v1', '023f9da22')
            self.assertEqual('https://dl.bintray.com/typesafe/bundle/download/path.zip', result)

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
            self.assertRaises(BintrayResolutionError, bintray_resolver.bintray_download_url, 'username', 'password',
                              'typesafe', 'bundle', 'reactive-maps-frontend', 'v1', '023f9da22')

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
            self.assertRaises(BintrayResolutionError, bintray_resolver.bintray_download_url, 'username', 'password',
                              'typesafe', 'bundle', 'reactive-maps-frontend', 'v1', '023f9da22')

        get_json_mock.assert_called_with(
            'https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend/versions/v1-023f9da22/files',
            'username', 'password')


class TestBintrayDownloadUrlLatest(TestCase):
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
            result = bintray_resolver.bintray_download_url('username', 'password',
                                                           'typesafe', 'bundle', 'reactive-maps-frontend', None, None)
            self.assertEqual('https://dl.bintray.com/typesafe/bundle/download/path.zip', result)

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
            result = bintray_resolver.bintray_download_url('username', 'password',
                                                           'typesafe', 'bundle', 'reactive-maps-frontend', None, None)
            self.assertEqual('https://dl.bintray.com/typesafe/bundle/download/path.zip', result)

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
            self.assertRaises(BintrayResolutionError, bintray_resolver.bintray_download_url, 'username', 'password',
                              'typesafe', 'bundle', 'reactive-maps-frontend', None, None)

        get_json_mock.assert_called_with('https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend',
                                         'username', 'password')

    def test_failure_latest_version_malformed(self):
        package_endpoint_response = {
            'latest_version': 'IAMBROKEN'
        }
        get_json_mock = MagicMock(return_value=package_endpoint_response)

        with patch('conductr_cli.resolvers.bintray_resolver.get_json', get_json_mock):
            self.assertRaises(BintrayResolutionError, bintray_resolver.bintray_download_url, 'username', 'password',
                              'typesafe', 'bundle', 'reactive-maps-frontend', None, None)

        get_json_mock.assert_called_with('https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend',
                                         'username', 'password')


class TestBintrayDownloadUrlLatestCompatibilityVersion(TestCase):
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
            result = bintray_resolver.bintray_download_url('username', 'password', 'typesafe', 'bundle',
                                                           'reactive-maps-frontend', 'v1', None)
            self.assertEqual('https://dl.bintray.com/typesafe/bundle/download/path.zip', result)

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
            result = bintray_resolver.bintray_download_url('username', 'password', 'typesafe', 'bundle',
                                                           'reactive-maps-frontend', 'v1', None)
            self.assertIsNone(result)

        get_json_mock.assert_called_with('https://api.bintray.com/packages/typesafe/bundle/reactive-maps-frontend/attributes?names=latest-v1',
                                         'username', 'password')


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

        exists_mock.assert_called_with('{}/.bintray/.credentials'.format(os.path.expanduser('~')))
        open_mock.assert_called_with('{}/.bintray/.credentials'.format(os.path.expanduser('~')), 'r')

    def test_credential_file_not_having_username_password(self):
        bintray_credential_file = strip_margin(
            """|dummy = yes
               |""")

        exists_mock = MagicMock(return_value=True)
        open_mock = MagicMock(return_value=io.StringIO(bintray_credential_file))

        with patch('os.path.exists', exists_mock), \
                patch('builtins.open', open_mock):
            username, password = bintray_resolver.load_bintray_credentials()
            self.assertIsNone(username)
            self.assertIsNone(password)

        exists_mock.assert_called_with('{}/.bintray/.credentials'.format(os.path.expanduser('~')))
        open_mock.assert_called_with('{}/.bintray/.credentials'.format(os.path.expanduser('~')), 'r')

    def test_missing_credential_file(self):
        exists_mock = MagicMock(return_value=False)

        with patch('os.path.exists', exists_mock):
            username, password = bintray_resolver.load_bintray_credentials()
            self.assertIsNone(username)
            self.assertIsNone(password)

        exists_mock.assert_called_with('{}/.bintray/.credentials'.format(os.path.expanduser('~')))


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
