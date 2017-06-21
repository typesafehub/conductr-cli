from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import logging_setup
from conductr_cli.resolvers import offline_resolver
from conductr_cli.resolvers.schemes import SCHEME_BUNDLE, SCHEME_FILE
from unittest.mock import call, patch, MagicMock


class TestResolveBundle(CliTestCase):

    cache_dir = '~/.conductr/cache'
    abspath = '/tmp/bundle.zip'

    def test_bundle_file_found(self):
        stdout = MagicMock()

        mock_exists = MagicMock(return_value=True)
        mock_abspath = MagicMock(return_value=self.abspath)

        args = MagicMock(**{})

        with patch('os.path.exists', mock_exists), \
                patch('os.path.abspath', mock_abspath):
            logging_setup.configure_logging(args, stdout)
            self.assertEqual((True, 'bundle.zip', self.abspath, None),
                             offline_resolver.resolve_bundle(self.cache_dir, self.abspath))

        mock_exists.assert_called_once_with(self.abspath)
        mock_abspath.assert_called_once_with(self.abspath)

        expected_output = strip_margin("""|Retrieving /tmp/bundle.zip
                                          |""")
        self.assertEqual(expected_output, self.output(stdout))

    def test_bundle_file_not_found(self):
        stdout = MagicMock()

        mock_exists = MagicMock(return_value=False)

        args = MagicMock(**{})

        with patch('os.path.exists', mock_exists):
            logging_setup.configure_logging(args, stdout)
            self.assertEqual((False, None, None, None),
                             offline_resolver.resolve_bundle(self.cache_dir, self.abspath))

        mock_exists.assert_called_once_with(self.abspath)

        self.assertEqual('', self.output(stdout))


class TestResolveBundleConfiguration(CliTestCase):

    cache_dir = '~/.conductr/cache'
    abspath = '/tmp/bundle-configuration.zip'

    def test_bundle_file_found(self):
        stdout = MagicMock()

        mock_exists = MagicMock(return_value=True)
        mock_abspath = MagicMock(return_value=self.abspath)

        args = MagicMock(**{})

        with patch('os.path.exists', mock_exists), \
                patch('os.path.abspath', mock_abspath):
            logging_setup.configure_logging(args, stdout)
            self.assertEqual((True, 'bundle-configuration.zip', self.abspath, None),
                             offline_resolver.resolve_bundle_configuration(self.cache_dir, self.abspath))

        mock_exists.assert_called_once_with(self.abspath)
        mock_abspath.assert_called_once_with(self.abspath)

        expected_output = strip_margin("""|Retrieving /tmp/bundle-configuration.zip
                                          |""")
        self.assertEqual(expected_output, self.output(stdout))

    def test_bundle_file_not_found(self):
        stdout = MagicMock()

        mock_exists = MagicMock(return_value=False)

        args = MagicMock(**{})

        with patch('os.path.exists', mock_exists):
            logging_setup.configure_logging(args, stdout)
            self.assertEqual((False, None, None, None),
                             offline_resolver.resolve_bundle_configuration(self.cache_dir, self.abspath))

        mock_exists.assert_called_once_with(self.abspath)

        self.assertEqual('', self.output(stdout))


class TestLoadBundleFromCache(CliTestCase):
    cache_dir = '~/.conductr/cache'

    paths = [
        '{}/path-1.zip'.format(cache_dir),
        '{}/path-2.zip'.format(cache_dir),
        '{}/path-3.zip'.format(cache_dir)
    ]

    def test_cached_bundle_found(self):
        stdout = MagicMock()

        mock_glob = MagicMock(return_value=self.paths)
        mock_getctime = MagicMock(side_effect=[9, 10, 3])

        args = MagicMock(**{})

        with patch('glob.glob', mock_glob), \
                patch('os.path.getctime', mock_getctime):
            logging_setup.configure_logging(args, stdout)
            self.assertEqual((True, 'path-2.zip', '~/.conductr/cache/path-2.zip', None),
                             offline_resolver.load_bundle_from_cache(self.cache_dir, 'visualizer'))

        mock_glob.assert_called_once_with('~/.conductr/cache/visualizer*')
        self.assertEqual([
            call('~/.conductr/cache/path-1.zip'),
            call('~/.conductr/cache/path-2.zip'),
            call('~/.conductr/cache/path-3.zip')
        ], mock_getctime.call_args_list)

        expected_output = strip_margin("""|Retrieving from cache ~/.conductr/cache/path-2.zip
                                          |""")
        self.assertEqual(expected_output, self.output(stdout))

    def test_cached_bundle_not_found(self):
        stdout = MagicMock()

        mock_glob = MagicMock(return_value=[])

        args = MagicMock(**{})

        with patch('glob.glob', mock_glob):
            logging_setup.configure_logging(args, stdout)
            self.assertEqual((False, None, None, None),
                             offline_resolver.load_bundle_from_cache(self.cache_dir, 'visualizer'))

        mock_glob.assert_called_once_with('~/.conductr/cache/visualizer*')

        self.assertEqual('', self.output(stdout))

    def test_not_bundle_name(self):
        self.assertEqual((False, None, None, None),
                         offline_resolver.load_bundle_from_cache(self.cache_dir, '/tmp/visualizer.zip'))
        self.assertEqual((False, None, None, None),
                         offline_resolver.load_bundle_from_cache(self.cache_dir, 'visualizer.zip'))


class TestLoadBundleConfigurationFromCache(CliTestCase):
    cache_dir = '~/.conductr/cache'

    paths = [
        '{}/path-1.zip'.format(cache_dir),
        '{}/path-2.zip'.format(cache_dir),
        '{}/path-3.zip'.format(cache_dir)
    ]

    def test_cached_bundle_found(self):
        stdout = MagicMock()

        mock_glob = MagicMock(return_value=self.paths)
        mock_getctime = MagicMock(side_effect=[9, 10, 3])

        args = MagicMock(**{})

        with patch('glob.glob', mock_glob), \
                patch('os.path.getctime', mock_getctime):
            logging_setup.configure_logging(args, stdout)
            self.assertEqual((True, 'path-2.zip', '~/.conductr/cache/path-2.zip', None),
                             offline_resolver.load_bundle_configuration_from_cache(self.cache_dir,
                                                                                   'conductr-haproxy-dev-mode'))

        mock_glob.assert_called_once_with('~/.conductr/cache/conductr-haproxy-dev-mode*')
        self.assertEqual([
            call('~/.conductr/cache/path-1.zip'),
            call('~/.conductr/cache/path-2.zip'),
            call('~/.conductr/cache/path-3.zip')
        ], mock_getctime.call_args_list)

        expected_output = strip_margin("""|Retrieving from cache ~/.conductr/cache/path-2.zip
                                          |""")
        self.assertEqual(expected_output, self.output(stdout))

    def test_cached_bundle_not_found(self):
        stdout = MagicMock()

        mock_glob = MagicMock(return_value=[])

        args = MagicMock(**{})

        with patch('glob.glob', mock_glob):
            logging_setup.configure_logging(args, stdout)
            self.assertEqual((False, None, None, None),
                             offline_resolver.load_bundle_configuration_from_cache(self.cache_dir,
                                                                                   'conductr-haproxy-dev-mode'))

        mock_glob.assert_called_once_with('~/.conductr/cache/conductr-haproxy-dev-mode*')

        self.assertEqual('', self.output(stdout))

    def test_not_bundle_name(self):
        self.assertEqual((False, None, None, None),
                         offline_resolver.load_bundle_configuration_from_cache(self.cache_dir,
                                                                               '/tmp/conductr-haproxy-dev-mode.zip'))
        self.assertEqual((False, None, None, None),
                         offline_resolver.load_bundle_configuration_from_cache(self.cache_dir,
                                                                               'conductr-haproxy-dev-mode.zip'))


class TestResolveBundleVersion(CliTestCase):
    def test_return_none(self):
        self.assertEqual((None, None), offline_resolver.resolve_bundle_version('visualizer'))


class TestContinuousDeliveryUri(CliTestCase):
    def test_return_none(self):
        self.assertIsNone(offline_resolver.continuous_delivery_uri('visualizer'))


class TestIsBundleName(CliTestCase):
    def test_return_true(self):
        self.assertTrue(offline_resolver.is_bundle_name('visualizer'))
        self.assertTrue(offline_resolver.is_bundle_name('conductr-haproxy-dev-mode'))

    def test_return_false(self):
        self.assertFalse(offline_resolver.is_bundle_name('/tmp/visualizer.zip'))
        self.assertFalse(offline_resolver.is_bundle_name('conductr-haproxy-dev-mode.zip'))


class TestSupportedSchemes(CliTestCase):
    def test_supported_schemes(self):
        self.assertEqual([SCHEME_BUNDLE, SCHEME_FILE], offline_resolver.supported_schemes())
