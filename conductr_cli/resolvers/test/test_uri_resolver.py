from unittest import TestCase
from urllib.error import URLError
from conductr_cli.resolvers import uri_resolver
from conductr_cli.resolvers.schemes import SCHEME_FILE, SCHEME_HTTP, SCHEME_HTTPS
from conductr_cli.test.cli_test_case import create_mock_logger
import os

from unittest.mock import call, patch, MagicMock


class TestResolveBundle(TestCase):
    def test_resolve_success(self):
        os_path_exists_mock = MagicMock(side_effect=[True, True])
        os_remove_mock = MagicMock()
        os_chmod_mock = MagicMock()
        file_move_mock = MagicMock()
        cache_path_mock = MagicMock(return_value='/bundle-cached-path')
        get_url_mock = MagicMock(return_value=('bundle-name', '/bundle-url-resolved'))
        urlretrieve_mock = MagicMock()

        get_logger_mock, log_mock = create_mock_logger()

        with patch('os.path.exists', os_path_exists_mock), \
                patch('os.remove', os_remove_mock), \
                patch('os.chmod', os_chmod_mock), \
                patch('shutil.move', file_move_mock), \
                patch('conductr_cli.resolvers.uri_resolver.cache_path', cache_path_mock), \
                patch('conductr_cli.resolvers.uri_resolver.get_url', get_url_mock), \
                patch('conductr_cli.resolvers.uri_resolver.urlretrieve', urlretrieve_mock), \
                patch('logging.getLogger', get_logger_mock):
            result = uri_resolver.resolve_bundle('/cache-dir', '/bundle-url')
            self.assertEqual((True, 'bundle-name', '/bundle-cached-path', None), result)

        self.assertEqual([
            call('/cache-dir'),
            call('/bundle-cached-path.tmp')
        ], os_path_exists_mock.call_args_list)
        cache_path_mock.assert_called_with('/cache-dir', '/bundle-url')
        get_url_mock.assert_called_with('/bundle-url')
        os_remove_mock.assert_called_with('/bundle-cached-path.tmp')
        urlretrieve_mock.assert_called_with('/bundle-url-resolved', '/bundle-cached-path.tmp')
        file_move_mock.assert_called_with('/bundle-cached-path.tmp', '/bundle-cached-path')

        get_logger_mock.assert_called_with('conductr_cli.resolvers.uri_resolver')
        log_mock.info.assert_called_with('Retrieving /bundle-url-resolved')

    def test_resolve_success_create_cache_dir(self):
        os_path_exists_mock = MagicMock(side_effect=[False, False])
        file_move_mock = MagicMock()
        os_chmod_mock = MagicMock()
        os_mkdirs_mock = MagicMock(return_value=())
        cache_path_mock = MagicMock(return_value='/bundle-cached-path')
        get_url_mock = MagicMock(return_value=('bundle-name', '/bundle-url-resolved'))
        urlretrieve_mock = MagicMock()

        get_logger_mock, log_mock = create_mock_logger()

        with patch('os.path.exists', os_path_exists_mock), \
                patch('os.makedirs', os_mkdirs_mock), \
                patch('os.chmod', os_chmod_mock), \
                patch('shutil.move', file_move_mock), \
                patch('conductr_cli.resolvers.uri_resolver.cache_path', cache_path_mock), \
                patch('conductr_cli.resolvers.uri_resolver.get_url', get_url_mock), \
                patch('conductr_cli.resolvers.uri_resolver.urlretrieve', urlretrieve_mock), \
                patch('logging.getLogger', get_logger_mock):
            result = uri_resolver.resolve_bundle('/cache-dir', '/bundle-url')
            self.assertEqual((True, 'bundle-name', '/bundle-cached-path', None), result)

        self.assertEqual([
            call('/cache-dir'),
            call('/bundle-cached-path.tmp')
        ], os_path_exists_mock.call_args_list)
        os_mkdirs_mock.assert_called_with('/cache-dir', mode=448)
        cache_path_mock.assert_called_with('/cache-dir', '/bundle-url')
        get_url_mock.assert_called_with('/bundle-url')
        urlretrieve_mock.assert_called_with('/bundle-url-resolved', '/bundle-cached-path.tmp')
        file_move_mock.assert_called_with('/bundle-cached-path.tmp', '/bundle-cached-path')

        get_logger_mock.assert_called_with('conductr_cli.resolvers.uri_resolver')
        log_mock.info.assert_called_with('Retrieving /bundle-url-resolved')

    def test_resolve_not_found(self):
        os_path_exists_mock = MagicMock(side_effect=[True, False])
        cache_path_mock = MagicMock(return_value='/bundle-cached-path')
        error = URLError('no_such.bundle')
        urlretrieve_mock = MagicMock(side_effect=error)
        get_url_mock = MagicMock(return_value=('bundle-name', '/bundle-url-resolved'))

        get_logger_mock, log_mock = create_mock_logger()

        with patch('os.path.exists', os_path_exists_mock), \
                patch('conductr_cli.resolvers.uri_resolver.cache_path', cache_path_mock), \
                patch('conductr_cli.resolvers.uri_resolver.get_url', get_url_mock), \
                patch('conductr_cli.resolvers.uri_resolver.urlretrieve', urlretrieve_mock), \
                patch('logging.getLogger', get_logger_mock):
            result = uri_resolver.resolve_bundle('/cache-dir', '/bundle-url')
            self.assertEqual((False, None, None, error), result)

        self.assertEqual([
            call('/cache-dir'),
            call('/bundle-cached-path.tmp')
        ], os_path_exists_mock.call_args_list)
        cache_path_mock.assert_called_with('/cache-dir', '/bundle-url')
        get_url_mock.assert_called_with('/bundle-url')
        urlretrieve_mock.assert_called_with('/bundle-url-resolved', '/bundle-cached-path.tmp')

        get_logger_mock.assert_called_with('conductr_cli.resolvers.uri_resolver')
        log_mock.info.assert_called_with('Retrieving /bundle-url-resolved')


class TestResolveBundleConfiguration(TestCase):
    def test_resolve_success(self):
        os_path_exists_mock = MagicMock(side_effect=[True, True])
        os_remove_mock = MagicMock()
        os_chmod_mock = MagicMock()
        file_move_mock = MagicMock()
        cache_path_mock = MagicMock(return_value='/bundle-cached-path')
        get_url_mock = MagicMock(return_value=('bundle-name', '/bundle-url-resolved'))
        urlretrieve_mock = MagicMock()

        get_logger_mock, log_mock = create_mock_logger()

        with patch('os.path.exists', os_path_exists_mock), \
                patch('os.remove', os_remove_mock), \
                patch('os.chmod', os_chmod_mock), \
                patch('shutil.move', file_move_mock), \
                patch('conductr_cli.resolvers.uri_resolver.cache_path', cache_path_mock), \
                patch('conductr_cli.resolvers.uri_resolver.get_url', get_url_mock), \
                patch('conductr_cli.resolvers.uri_resolver.urlretrieve', urlretrieve_mock), \
                patch('logging.getLogger', get_logger_mock):
            result = uri_resolver.resolve_bundle_configuration('/cache-dir', '/bundle-url')
            self.assertEqual((True, 'bundle-name', '/bundle-cached-path', None), result)

        self.assertEqual([
            call('/cache-dir'),
            call('/bundle-cached-path.tmp')
        ], os_path_exists_mock.call_args_list)
        cache_path_mock.assert_called_with('/cache-dir', '/bundle-url')
        get_url_mock.assert_called_with('/bundle-url')
        os_remove_mock.assert_called_with('/bundle-cached-path.tmp')
        urlretrieve_mock.assert_called_with('/bundle-url-resolved', '/bundle-cached-path.tmp')
        file_move_mock.assert_called_with('/bundle-cached-path.tmp', '/bundle-cached-path')

        get_logger_mock.assert_called_with('conductr_cli.resolvers.uri_resolver')
        log_mock.info.assert_called_with('Retrieving /bundle-url-resolved')

    def test_resolve_success_create_cache_dir(self):
        os_path_exists_mock = MagicMock(side_effect=[False, False])
        file_move_mock = MagicMock()
        os_chmod_mock = MagicMock()
        os_mkdirs_mock = MagicMock(return_value=())
        cache_path_mock = MagicMock(return_value='/bundle-cached-path')
        get_url_mock = MagicMock(return_value=('bundle-name', '/bundle-url-resolved'))
        urlretrieve_mock = MagicMock()

        get_logger_mock, log_mock = create_mock_logger()

        with patch('os.path.exists', os_path_exists_mock), \
                patch('os.makedirs', os_mkdirs_mock), \
                patch('os.chmod', os_chmod_mock), \
                patch('shutil.move', file_move_mock), \
                patch('conductr_cli.resolvers.uri_resolver.cache_path', cache_path_mock), \
                patch('conductr_cli.resolvers.uri_resolver.get_url', get_url_mock), \
                patch('conductr_cli.resolvers.uri_resolver.urlretrieve', urlretrieve_mock), \
                patch('logging.getLogger', get_logger_mock):
            result = uri_resolver.resolve_bundle_configuration('/cache-dir', '/bundle-url')
            self.assertEqual((True, 'bundle-name', '/bundle-cached-path', None), result)

        self.assertEqual([
            call('/cache-dir'),
            call('/bundle-cached-path.tmp')
        ], os_path_exists_mock.call_args_list)
        os_mkdirs_mock.assert_called_with('/cache-dir', mode=448)
        cache_path_mock.assert_called_with('/cache-dir', '/bundle-url')
        get_url_mock.assert_called_with('/bundle-url')
        urlretrieve_mock.assert_called_with('/bundle-url-resolved', '/bundle-cached-path.tmp')
        file_move_mock.assert_called_with('/bundle-cached-path.tmp', '/bundle-cached-path')

        get_logger_mock.assert_called_with('conductr_cli.resolvers.uri_resolver')
        log_mock.info.assert_called_with('Retrieving /bundle-url-resolved')

    def test_resolve_not_found(self):
        os_path_exists_mock = MagicMock(side_effect=[True, False])
        cache_path_mock = MagicMock(return_value='/bundle-cached-path')
        error = URLError('no_such.bundle')
        urlretrieve_mock = MagicMock(side_effect=error)
        get_url_mock = MagicMock(return_value=('bundle-name', '/bundle-url-resolved'))

        get_logger_mock, log_mock = create_mock_logger()

        with patch('os.path.exists', os_path_exists_mock), \
                patch('conductr_cli.resolvers.uri_resolver.cache_path', cache_path_mock), \
                patch('conductr_cli.resolvers.uri_resolver.get_url', get_url_mock), \
                patch('conductr_cli.resolvers.uri_resolver.urlretrieve', urlretrieve_mock), \
                patch('logging.getLogger', get_logger_mock):
            result = uri_resolver.resolve_bundle_configuration('/cache-dir', '/bundle-url')
            self.assertEqual((False, None, None, error), result)

        self.assertEqual([
            call('/cache-dir'),
            call('/bundle-cached-path.tmp')
        ], os_path_exists_mock.call_args_list)
        cache_path_mock.assert_called_with('/cache-dir', '/bundle-url')
        get_url_mock.assert_called_with('/bundle-url')
        urlretrieve_mock.assert_called_with('/bundle-url-resolved', '/bundle-cached-path.tmp')

        get_logger_mock.assert_called_with('conductr_cli.resolvers.uri_resolver')
        log_mock.info.assert_called_with('Retrieving /bundle-url-resolved')


class TestResolveConductrBinary(TestCase):
    def test_resolve_success(self):
        os_path_exists_mock = MagicMock(side_effect=[True, True])
        os_remove_mock = MagicMock()
        os_chmod_mock = MagicMock()
        file_move_mock = MagicMock()
        cache_path_mock = MagicMock(return_value='/images/conductr-1.0.0.tgz')
        get_url_mock = MagicMock(return_value=('conductr-1.0.0.tgz', 'conductr-binary-uri'))
        urlretrieve_mock = MagicMock()

        get_logger_mock, log_mock = create_mock_logger()

        with patch('os.path.exists', os_path_exists_mock), \
                patch('os.remove', os_remove_mock), \
                patch('os.chmod', os_chmod_mock), \
                patch('shutil.move', file_move_mock), \
                patch('conductr_cli.resolvers.uri_resolver.cache_path', cache_path_mock), \
                patch('conductr_cli.resolvers.uri_resolver.get_url', get_url_mock), \
                patch('conductr_cli.resolvers.uri_resolver.urlretrieve', urlretrieve_mock), \
                patch('logging.getLogger', get_logger_mock):
            result = uri_resolver.resolve_file('/images', 'conductr-binary-uri')
            self.assertEqual((True, 'conductr-1.0.0.tgz', '/images/conductr-1.0.0.tgz', None), result)

        self.assertEqual([
            call('/images'),
            call('/images/conductr-1.0.0.tgz.tmp')
        ], os_path_exists_mock.call_args_list)
        cache_path_mock.assert_called_with('/images', 'conductr-binary-uri')
        get_url_mock.assert_called_with('conductr-binary-uri')
        os_remove_mock.assert_called_with('/images/conductr-1.0.0.tgz.tmp')
        urlretrieve_mock.assert_called_with('conductr-binary-uri', '/images/conductr-1.0.0.tgz.tmp')
        file_move_mock.assert_called_with('/images/conductr-1.0.0.tgz.tmp', '/images/conductr-1.0.0.tgz')

        get_logger_mock.assert_called_with('conductr_cli.resolvers.uri_resolver')
        log_mock.info.assert_called_with('Retrieving conductr-binary-uri')

    def test_resolve_raise_url_error(self):
        os_path_exists_mock = MagicMock(side_effect=[True, True])
        os_remove_mock = MagicMock()
        os_chmod_mock = MagicMock()
        file_move_mock = MagicMock()
        cache_path_mock = MagicMock(return_value='/images/conductr-1.0.0.tgz')
        url_error = URLError('test')
        get_url_mock = MagicMock(return_value=('conductr-1.0.0.tgz', 'conductr-binary-uri'))
        urlretrieve_mock = MagicMock(side_effect=url_error)

        get_logger_mock, log_mock = create_mock_logger()

        with patch('os.path.exists', os_path_exists_mock), \
                patch('os.remove', os_remove_mock), \
                patch('os.chmod', os_chmod_mock), \
                patch('shutil.move', file_move_mock), \
                patch('conductr_cli.resolvers.uri_resolver.cache_path', cache_path_mock), \
                patch('conductr_cli.resolvers.uri_resolver.get_url', get_url_mock), \
                patch('conductr_cli.resolvers.uri_resolver.urlretrieve', urlretrieve_mock), \
                patch('logging.getLogger', get_logger_mock),\
                self.assertRaises(URLError) as e:
            uri_resolver.resolve_file('/images', 'conductr-binary-uri', raise_error=True)

        self.assertEqual(e.exception, url_error)
        self.assertEqual([
            call('/images'),
            call('/images/conductr-1.0.0.tgz.tmp')
        ], os_path_exists_mock.call_args_list)
        cache_path_mock.assert_called_with('/images', 'conductr-binary-uri')
        get_url_mock.assert_called_with('conductr-binary-uri')
        os_remove_mock.assert_called_with('/images/conductr-1.0.0.tgz.tmp')
        urlretrieve_mock.assert_called_with('conductr-binary-uri', '/images/conductr-1.0.0.tgz.tmp')
        file_move_mock.assert_not_called()

        get_logger_mock.assert_called_with('conductr_cli.resolvers.uri_resolver')
        log_mock.info.assert_called_with('Retrieving conductr-binary-uri')

    def test_resolve_unraised_url_error(self):
        os_path_exists_mock = MagicMock(side_effect=[True, True])
        os_remove_mock = MagicMock()
        os_chmod_mock = MagicMock()
        file_move_mock = MagicMock()
        cache_path_mock = MagicMock(return_value='/images/conductr-1.0.0.tgz')
        get_url_mock = MagicMock(return_value=('conductr-1.0.0.tgz', 'conductr-binary-uri'))
        url_error = URLError('test')
        urlretrieve_mock = MagicMock(side_effect=url_error)

        get_logger_mock, log_mock = create_mock_logger()

        with patch('os.path.exists', os_path_exists_mock), \
                patch('os.remove', os_remove_mock), \
                patch('os.chmod', os_chmod_mock), \
                patch('shutil.move', file_move_mock), \
                patch('conductr_cli.resolvers.uri_resolver.cache_path', cache_path_mock), \
                patch('conductr_cli.resolvers.uri_resolver.get_url', get_url_mock), \
                patch('conductr_cli.resolvers.uri_resolver.urlretrieve', urlretrieve_mock), \
                patch('logging.getLogger', get_logger_mock):
            result = uri_resolver.resolve_file('/images', 'conductr-binary-uri')
            self.assertEqual((False, None, None, url_error), result)

        self.assertEqual([
            call('/images'),
            call('/images/conductr-1.0.0.tgz.tmp')
        ], os_path_exists_mock.call_args_list)
        cache_path_mock.assert_called_with('/images', 'conductr-binary-uri')
        get_url_mock.assert_called_with('conductr-binary-uri')
        os_remove_mock.assert_called_with('/images/conductr-1.0.0.tgz.tmp')
        urlretrieve_mock.assert_called_with('conductr-binary-uri', '/images/conductr-1.0.0.tgz.tmp')
        file_move_mock.assert_not_called()

        get_logger_mock.assert_called_with('conductr_cli.resolvers.uri_resolver')
        log_mock.info.assert_called_with('Retrieving conductr-binary-uri')


class TestLoadBundleFromCache(TestCase):
    def test_file(self):
        exists_mock = MagicMock()

        with patch('os.path.exists', exists_mock):
            result = uri_resolver.load_bundle_from_cache('/cache-dir', '/tmp/bundle.zip')
            self.assertEqual((False, None, None, None), result)

        exists_mock.assert_not_called()

    def test_uri_found(self):
        exists_mock = MagicMock(return_value=True)

        get_logger_mock, log_mock = create_mock_logger()

        with patch('os.path.exists', exists_mock), \
                patch('logging.getLogger', get_logger_mock):
            result = uri_resolver.load_bundle_from_cache('/cache-dir', 'http://site.com/path/bundle-file.zip')
            self.assertEqual((True, 'bundle-file.zip', '/cache-dir/bundle-file.zip', None), result)

        exists_mock.assert_called_with('/cache-dir/bundle-file.zip')

        get_logger_mock.assert_called_with('conductr_cli.resolvers.uri_resolver')
        log_mock.info.assert_called_with('Retrieving from cache /cache-dir/bundle-file.zip')

    def test_uri_not_found(self):
        exists_mock = MagicMock(return_value=False)

        with patch('os.path.exists', exists_mock):
            result = uri_resolver.load_bundle_from_cache('/cache-dir', 'http://site.com/path/bundle-file.zip')
            self.assertEqual((False, None, None, None), result)

        exists_mock.assert_called_with('/cache-dir/bundle-file.zip')


class TestLoadBundleConfigurationFromCache(TestCase):
    def test_file(self):
        exists_mock = MagicMock()

        with patch('os.path.exists', exists_mock):
            result = uri_resolver.load_bundle_configuration_from_cache('/cache-dir', '/tmp/bundle.zip')
            self.assertEqual((False, None, None, None), result)

        exists_mock.assert_not_called()

    def test_uri_found(self):
        exists_mock = MagicMock(return_value=True)

        get_logger_mock, log_mock = create_mock_logger()

        with patch('os.path.exists', exists_mock), \
                patch('logging.getLogger', get_logger_mock):
            result = uri_resolver.load_bundle_configuration_from_cache('/cache-dir',
                                                                       'http://site.com/path/bundle-file.zip')
            self.assertEqual((True, 'bundle-file.zip', '/cache-dir/bundle-file.zip', None), result)

        exists_mock.assert_called_with('/cache-dir/bundle-file.zip')

        get_logger_mock.assert_called_with('conductr_cli.resolvers.uri_resolver')
        log_mock.info.assert_called_with('Retrieving from cache /cache-dir/bundle-file.zip')

    def test_uri_not_found(self):
        exists_mock = MagicMock(return_value=False)

        with patch('os.path.exists', exists_mock):
            result = uri_resolver.load_bundle_configuration_from_cache('/cache-dir',
                                                                       'http://site.com/path/bundle-file.zip')
            self.assertEqual((False, None, None, None), result)

        exists_mock.assert_called_with('/cache-dir/bundle-file.zip')


class TestContinuousDeliveryUri(TestCase):
    def test_return_none(self):
        self.assertIsNone(uri_resolver.continuous_delivery_uri({}))


class TestGetUrl(TestCase):
    def test_url(self):
        filename, url = uri_resolver.get_url(
            'https://site.com/bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip')
        self.assertEqual(
            'bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip', filename)
        self.assertEqual(
            'https://site.com/bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip', url)

    def test_file(self):
        filename, url = uri_resolver.get_url(
            'bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip')
        self.assertEqual(
            'bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip', filename)
        # os.getcwd() does not return path starting with '/' on windows - additional '/' will be required to form a
        # correct file uri on windows
        base_uri = 'file://' + os.getcwd() if os.getcwd().startswith('/') else 'file:///' + os.getcwd()
        self.assertEqual(
            base_uri + os.sep +
            'bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip', url)

    def test_file_with_protocol_prefix(self):
        filename, url = uri_resolver.get_url(
            'file:///basedir/bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip')
        self.assertEqual(
            'bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip', filename)
        self.assertEqual(
            'file:///basedir/bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip', url)


class TestCachePath(TestCase):
    def test_cache_path_file(self):
        result = uri_resolver.cache_path('/cache-dir', '/var/test/file.zip')
        self.assertEqual('/cache-dir/file.zip', result)

    def test_cache_path_url(self):
        result = uri_resolver.cache_path('/cache-dir', 'http://some-site.com/path/test/file.zip')
        self.assertEqual('/cache-dir/file.zip', result)


class TestProgressBar(TestCase):
    def test_show_progress_bar(self):
        os_path_exists_mock = MagicMock(side_effect=[True, True])
        os_remove_mock = MagicMock()
        os_chmod_mock = MagicMock()
        file_move_mock = MagicMock()
        cache_path_mock = MagicMock(return_value='/bundle-cached-path')
        get_url_mock = MagicMock(return_value=('bundle-name', 'http://site.com/bundle-url-resolved'))
        urlretrieve_mock = MagicMock()
        report_hook_mock = MagicMock()
        show_progress_mock = MagicMock(return_value=report_hook_mock)

        get_logger_mock, log_mock = create_mock_logger()

        with patch('os.path.exists', os_path_exists_mock), \
                patch('os.remove', os_remove_mock), \
                patch('os.chmod', os_chmod_mock), \
                patch('shutil.move', file_move_mock), \
                patch('conductr_cli.resolvers.uri_resolver.cache_path', cache_path_mock), \
                patch('conductr_cli.resolvers.uri_resolver.get_url', get_url_mock), \
                patch('conductr_cli.resolvers.uri_resolver.urlretrieve', urlretrieve_mock), \
                patch('conductr_cli.resolvers.uri_resolver.show_progress', show_progress_mock), \
                patch('logging.getLogger', get_logger_mock):
            result = uri_resolver.resolve_bundle('/cache-dir', 'http://site.com/bundle-url')
            self.assertEqual((True, 'bundle-name', '/bundle-cached-path', None), result)

        self.assertEqual([
            call('/cache-dir'),
            call('/bundle-cached-path.tmp')
        ], os_path_exists_mock.call_args_list)
        cache_path_mock.assert_called_with('/cache-dir', 'http://site.com/bundle-url')
        get_url_mock.assert_called_with('http://site.com/bundle-url')
        os_remove_mock.assert_called_with('/bundle-cached-path.tmp')
        urlretrieve_mock.assert_called_with('http://site.com/bundle-url-resolved',
                                            '/bundle-cached-path.tmp', reporthook=report_hook_mock)
        file_move_mock.assert_called_with('/bundle-cached-path.tmp', '/bundle-cached-path')

        get_logger_mock.assert_called_with('conductr_cli.resolvers.uri_resolver')
        log_mock.info.assert_not_called()

    def test_no_progress_bar_given_quiet_mode(self):
        os_path_exists_mock = MagicMock(side_effect=[True, True])
        os_remove_mock = MagicMock()
        os_chmod_mock = MagicMock()
        file_move_mock = MagicMock()
        cache_path_mock = MagicMock(return_value='/bundle-cached-path')
        get_url_mock = MagicMock(return_value=('bundle-name', 'http://site.com/bundle-url-resolved'))
        urlretrieve_mock = MagicMock()

        get_logger_mock, log_mock = create_mock_logger()
        log_mock.is_progress_enabled = MagicMock(return_value=False)

        with patch('os.path.exists', os_path_exists_mock), \
                patch('os.remove', os_remove_mock), \
                patch('os.chmod', os_chmod_mock), \
                patch('shutil.move', file_move_mock), \
                patch('conductr_cli.resolvers.uri_resolver.cache_path', cache_path_mock), \
                patch('conductr_cli.resolvers.uri_resolver.get_url', get_url_mock), \
                patch('conductr_cli.resolvers.uri_resolver.urlretrieve', urlretrieve_mock), \
                patch('logging.getLogger', get_logger_mock):
            result = uri_resolver.resolve_bundle('/cache-dir', 'http://site.com/bundle-url')
            self.assertEqual((True, 'bundle-name', '/bundle-cached-path', None), result)

        self.assertEqual([
            call('/cache-dir'),
            call('/bundle-cached-path.tmp')
        ], os_path_exists_mock.call_args_list)
        cache_path_mock.assert_called_with('/cache-dir', 'http://site.com/bundle-url')
        get_url_mock.assert_called_with('http://site.com/bundle-url')
        os_remove_mock.assert_called_with('/bundle-cached-path.tmp')
        urlretrieve_mock.assert_called_with('http://site.com/bundle-url-resolved', '/bundle-cached-path.tmp')
        file_move_mock.assert_called_with('/bundle-cached-path.tmp', '/bundle-cached-path')

        get_logger_mock.assert_called_with('conductr_cli.resolvers.uri_resolver')
        log_mock.info.assert_called_with('Retrieving http://site.com/bundle-url-resolved')


class TestResolveBundleVersion(TestCase):
    def test_return_none(self):
        self.assertIsNone(uri_resolver.resolve_bundle_version("bundle"))


class TestShowProgress(TestCase):
    def test_log_progress_until_completion(self):
        bundle_url = 'http://url/bundle.zip'

        log_mock = MagicMock()

        log_info_mock = MagicMock()
        log_mock.info = log_info_mock

        log_progress_mock = MagicMock()
        log_mock.progress = log_progress_mock

        progress_bar_mock = MagicMock(return_value='mock progress bar')

        with patch('conductr_cli.screen_utils.progress_bar', progress_bar_mock):
            progress_tracker = uri_resolver.show_progress(log_mock, bundle_url)

            progress_tracker(0, 10, 200)
            progress_bar_mock.assert_called_with(0.0)
            log_progress_mock.assert_called_with('mock progress bar', flush=False)

            progress_tracker(20, 10, 200)
            progress_bar_mock.assert_called_with(1.0)
            log_progress_mock.assert_called_with('mock progress bar', flush=True)

            log_info_mock.assert_called_once_with('Retrieving http://url/bundle.zip')


class TestSupportedSchemes(TestCase):
    def test_supported_schemes(self):
        self.assertEqual([SCHEME_FILE, SCHEME_HTTP, SCHEME_HTTPS], uri_resolver.supported_schemes())
