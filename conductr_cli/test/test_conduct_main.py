from unittest import TestCase
from unittest.mock import MagicMock, patch
from conductr_cli.conduct_main import build_parser, get_cli_parameters
from conductr_cli.constants import DEFAULT_LICENSE_DOWNLOAD_URL
from argparse import Namespace
import os


class TestConduct(TestCase):
    with patch('sys.stdin.isatty', lambda: False):
        parser = build_parser(False)

    with patch('sys.stdin.isatty', lambda: True):
        parser_tty = build_parser(False)

    def test_parser_version(self):
        args = self.parser.parse_args('version'.split())

        self.assertEqual(args.func.__name__, 'version')

    def test_default(self):
        args = self.parser.parse_args(
            'info --ip 127.0.1.1 --port 9999 -v --long-ids --api-version 1 '
            '--settings-dir /settings-dir --custom-plugins-dir /custom-plugins-dir'.split())

        self.assertEqual(args.func.__name__, 'info')
        self.assertEqual(args.scheme, 'http')
        self.assertEqual(args.ip, '127.0.1.1')
        self.assertEqual(args.port, 9999)
        self.assertEqual(args.base_path, '/')
        self.assertEqual(args.api_version, '1')
        self.assertEqual(args.cli_settings_dir, '/settings-dir')
        self.assertEqual(args.custom_plugins_dir, '/custom-plugins-dir')
        self.assertEqual(args.verbose, True)
        self.assertEqual(args.long_ids, True)

    def test_parser_info(self):
        args = self.parser.parse_args('info'.split())

        self.assertEqual(args.func.__name__, 'info')
        self.assertEqual(args.ip, None)
        self.assertEqual(args.port, 9005)
        self.assertEqual(args.api_version, '2')
        self.assertEqual(args.cli_settings_dir, '{}/.conductr'.format(os.path.expanduser('~')))
        self.assertEqual(args.verbose, False)
        self.assertEqual(args.long_ids, False)
        self.assertEqual(args.bundle, None)

    def test_parser_info_with_bundle(self):
        args = self.parser.parse_args('info vis'.split())

        self.assertEqual(args.func.__name__, 'info')
        self.assertEqual(args.ip, None)
        self.assertEqual(args.port, 9005)
        self.assertEqual(args.api_version, '2')
        self.assertEqual(args.cli_settings_dir, '{}/.conductr'.format(os.path.expanduser('~')))
        self.assertEqual(args.verbose, False)
        self.assertEqual(args.long_ids, False)
        self.assertEqual(args.bundle, 'vis')

    def test_parser_services(self):
        args = self.parser.parse_args('service-names'.split())

        self.assertEqual(args.func.__name__, 'service_names')
        self.assertEqual(args.ip, None)
        self.assertEqual(args.port, 9005)
        self.assertEqual(args.api_version, '2')
        self.assertEqual(args.cli_settings_dir, '{}/.conductr'.format(os.path.expanduser('~')))
        self.assertEqual(args.verbose, False)
        self.assertEqual(args.long_ids, False)

    def test_parser_acls_http(self):
        for protocol_family in ['http', 'tcp']:
            args = self.parser.parse_args('acls {}'.format(protocol_family).split())

            self.assertEqual(args.func.__name__, 'acls')
            self.assertEqual(args.ip, None)
            self.assertEqual(args.port, 9005)
            self.assertEqual(args.api_version, '2')
            self.assertEqual(args.cli_settings_dir, '{}/.conductr'.format(os.path.expanduser('~')))
            self.assertEqual(args.verbose, False)
            self.assertEqual(args.long_ids, False)

    def test_parser_load(self):
        args = self.parser.parse_args('load path-to-bundle path-to-conf'.split())

        self.assertEqual(args.func.__name__, 'load')
        self.assertEqual(args.ip, None)
        self.assertEqual(args.port, 9005)
        self.assertEqual(args.api_version, '2')
        self.assertEqual(args.cli_settings_dir, '{}/.conductr'.format(os.path.expanduser('~')))
        self.assertEqual(args.bundle_resolve_cache_dir, '{}/.conductr/cache/bundle'.format(os.path.expanduser('~')))
        self.assertEqual(args.configuration_resolve_cache_dir,
                         '{}/.conductr/cache/configuration'.format(os.path.expanduser('~')))
        self.assertEqual(args.verbose, False)
        self.assertEqual(args.long_ids, False)
        self.assertEqual(args.no_wait, False)
        self.assertEqual(args.wait_timeout, 60)
        self.assertEqual(args.bundle, 'path-to-bundle')
        self.assertEqual(args.configuration, 'path-to-conf')

    def test_parser_load_stdin_explicit(self):
        args = self.parser.parse_args('load - path-to-conf'.split())

        self.assertEqual(args.func.__name__, 'load')
        self.assertEqual(args.bundle, '-')
        self.assertEqual(args.configuration, 'path-to-conf')

    def test_parser_load_stdin_implied(self):
        args = self.parser.parse_args('load'.split())

        self.assertEqual(args.func.__name__, 'load')
        self.assertEqual(args.bundle, '-')

    def test_parser_load_no_stdin_noargs(self):
        exit_mock = MagicMock()
        print_usage_mock = MagicMock()
        stderr = MagicMock()

        with patch('sys.exit', exit_mock), \
                patch('argparse.ArgumentParser.print_usage', print_usage_mock), \
                patch('sys.stderr.write', stderr):
            self.parser_tty.parse_args('load'.split())

        self.assertEqual(print_usage_mock.call_count, 1)
        stderr.assert_called_once_with('conduct load: error: the following arguments are required: bundle\n')
        exit_mock.assert_called_with(2)

    def test_parser_load_with_custom_bundle_resolve_cache_dir(self):
        args = self.parser.parse_args('load --bundle-resolve-cache-dir /new-bundle-dir path-to-bundle path-to-conf'
                                      .split())

        self.assertEqual(args.func.__name__, 'load')
        self.assertEqual(args.ip, None)
        self.assertEqual(args.port, 9005)
        self.assertEqual(args.api_version, '2')
        self.assertEqual(args.cli_settings_dir, '{}/.conductr'.format(os.path.expanduser('~')))
        self.assertEqual(args.bundle_resolve_cache_dir, '/new-bundle-dir')
        self.assertEqual(args.configuration_resolve_cache_dir,
                         '{}/.conductr/cache/configuration'.format(os.path.expanduser('~')))
        self.assertEqual(args.verbose, False)
        self.assertEqual(args.long_ids, False)
        self.assertEqual(args.no_wait, False)
        self.assertEqual(args.wait_timeout, 60)
        self.assertEqual(args.bundle, 'path-to-bundle')
        self.assertEqual(args.configuration, 'path-to-conf')
        self.assertFalse(args.quiet)

    def test_parser_load_with_custom_configuration_resolve_cache_dir(self):
        args = self.parser.parse_args('load --configuration-resolve-cache-dir /new-conf-dir path-to-bundle path-to-conf'
                                      .split())

        self.assertEqual(args.func.__name__, 'load')
        self.assertEqual(args.ip, None)
        self.assertEqual(args.port, 9005)
        self.assertEqual(args.api_version, '2')
        self.assertEqual(args.cli_settings_dir, '{}/.conductr'.format(os.path.expanduser('~')))
        self.assertEqual(args.bundle_resolve_cache_dir, '{}/.conductr/cache/bundle'.format(os.path.expanduser('~')))
        self.assertEqual(args.configuration_resolve_cache_dir, '/new-conf-dir')
        self.assertEqual(args.verbose, False)
        self.assertEqual(args.long_ids, False)
        self.assertEqual(args.no_wait, False)
        self.assertEqual(args.wait_timeout, 60)
        self.assertEqual(args.bundle, 'path-to-bundle')
        self.assertEqual(args.configuration, 'path-to-conf')
        self.assertFalse(args.quiet)

    def test_parser_run(self):
        args = self.parser.parse_args('run --scale 5 path-to-bundle'.split())

        self.assertEqual(args.func.__name__, 'run')
        self.assertEqual(args.ip, None)
        self.assertEqual(args.port, 9005)
        self.assertEqual(args.api_version, '2')
        self.assertEqual(args.cli_settings_dir, '{}/.conductr'.format(os.path.expanduser('~')))
        self.assertEqual(args.verbose, False)
        self.assertEqual(args.long_ids, False)
        self.assertEqual(args.no_wait, False)
        self.assertEqual(args.wait_timeout, 60)
        self.assertEqual(args.scale, 5)
        self.assertEqual(args.bundle, 'path-to-bundle')
        # These args are for displaying bundle events and logs when error occurs during scale.
        self.assertEqual(args.lines, 10)
        self.assertEqual(args.utc, False)
        self.assertEqual(args.follow, False)

    def test_parser_stop(self):
        args = self.parser.parse_args('stop path-to-bundle'.split())

        self.assertEqual(args.func.__name__, 'stop')
        self.assertEqual(args.ip, None)
        self.assertEqual(args.port, 9005)
        self.assertEqual(args.api_version, '2')
        self.assertEqual(args.cli_settings_dir, '{}/.conductr'.format(os.path.expanduser('~')))
        self.assertEqual(args.verbose, False)
        self.assertEqual(args.long_ids, False)
        self.assertEqual(args.no_wait, False)
        self.assertEqual(args.wait_timeout, 60)
        self.assertEqual(args.bundle, 'path-to-bundle')
        # These args are for displaying bundle events and logs when error occurs during scale.
        self.assertEqual(args.lines, 10)
        self.assertEqual(args.utc, False)
        self.assertEqual(args.follow, False)

    def test_parser_unload(self):
        args = self.parser.parse_args('unload path-to-bundle'.split())

        self.assertEqual(args.func.__name__, 'unload')
        self.assertEqual(args.ip, None)
        self.assertEqual(args.port, 9005)
        self.assertEqual(args.api_version, '2')
        self.assertEqual(args.cli_settings_dir, '{}/.conductr'.format(os.path.expanduser('~')))
        self.assertEqual(args.verbose, False)
        self.assertEqual(args.long_ids, False)
        self.assertEqual(args.no_wait, False)
        self.assertEqual(args.wait_timeout, 60)
        self.assertEqual(args.bundle, 'path-to-bundle')

    def test_parser_deploy(self):
        args = self.parser.parse_args('deploy cassandra'.split())

        self.assertEqual(args.func.__name__, 'deploy')
        self.assertEqual(args.ip, None)
        self.assertEqual(args.port, 9005)
        self.assertEqual(args.api_version, '2')
        self.assertEqual(args.cli_settings_dir, '{}/.conductr'.format(os.path.expanduser('~')))
        self.assertEqual(args.no_wait, False)
        self.assertEqual(args.wait_timeout, 180)
        self.assertEqual(args.long_ids, False)
        self.assertEqual(args.auto_deploy, False)
        self.assertEqual(args.tags, [])
        self.assertEqual(args.bundle, 'cassandra')

    def test_parser_deploy_with_auto_deploy(self):
        args = self.parser.parse_args('deploy cassandra -y'.split())

        self.assertEqual(args.func.__name__, 'deploy')
        self.assertEqual(args.ip, None)
        self.assertEqual(args.port, 9005)
        self.assertEqual(args.api_version, '2')
        self.assertEqual(args.cli_settings_dir, '{}/.conductr'.format(os.path.expanduser('~')))
        self.assertEqual(args.no_wait, False)
        self.assertEqual(args.wait_timeout, 180)
        self.assertEqual(args.long_ids, False)
        self.assertEqual(args.auto_deploy, True)
        self.assertEqual(args.tags, [])
        self.assertEqual(args.webhook, None)
        self.assertEqual(args.bundle, 'cassandra')

    def test_parser_deploy_with_tags(self):
        args = self.parser.parse_args('deploy cassandra --target-tag 1.0.1 --target-tag 1.0.2 --webhook bintray'.split())

        self.assertEqual(args.func.__name__, 'deploy')
        self.assertEqual(args.ip, None)
        self.assertEqual(args.port, 9005)
        self.assertEqual(args.api_version, '2')
        self.assertEqual(args.cli_settings_dir, '{}/.conductr'.format(os.path.expanduser('~')))
        self.assertEqual(args.no_wait, False)
        self.assertEqual(args.wait_timeout, 180)
        self.assertEqual(args.long_ids, False)
        self.assertEqual(args.auto_deploy, False)
        self.assertEqual(args.target_tags, ['1.0.1', '1.0.2'])
        self.assertEqual(args.webhook, 'bintray')
        self.assertEqual(args.bundle, 'cassandra')

    def test_parser_load_license(self):
        args = self.parser.parse_args('load-license'.split())

        self.assertEqual(args.func.__name__, 'load_license')
        self.assertEqual(args.host, None)
        self.assertEqual(args.port, 9005)
        self.assertEqual(args.api_version, '2')
        self.assertFalse(args.offline_mode)
        self.assertEqual(args.cli_settings_dir, '{}/.conductr'.format(os.path.expanduser('~')))
        self.assertEqual(args.custom_settings_file, '{}/.conductr/settings.conf'.format(os.path.expanduser('~')))
        self.assertEqual(args.custom_plugins_dir, '{}/.conductr/plugins'.format(os.path.expanduser('~')))
        self.assertFalse(args.force_flag_enabled)
        self.assertEqual(args.license_download_url, DEFAULT_LICENSE_DOWNLOAD_URL)
        self.assertEqual(args.local_connection, True)

    def test_parser_load_license_custom_args(self):
        args = self.parser.parse_args('load-license '
                                      '--offline '
                                      '--host 127.0.0.1 '
                                      '--port 29005 '
                                      '--api-version 1 '
                                      '--settings-dir /tmp '
                                      '--custom-settings-file /tmp/foo.conf '
                                      '--custom-plugins-dir /tmp/plugins '
                                      '--force '
                                      '--license-download-url http://example.org'.split())

        self.assertEqual(args.func.__name__, 'load_license')
        self.assertEqual(args.host, '127.0.0.1')
        self.assertEqual(args.port, 29005)
        self.assertEqual(args.api_version, '1')
        self.assertTrue(args.offline_mode)
        self.assertEqual(args.cli_settings_dir, '/tmp')
        self.assertEqual(args.custom_settings_file, '/tmp/foo.conf')
        self.assertEqual(args.custom_plugins_dir, '/tmp/plugins')
        self.assertTrue(args.force_flag_enabled)
        self.assertEqual(args.license_download_url, 'http://example.org')
        self.assertEqual(args.local_connection, True)

    def test_default_with_dcos(self):
        dcos_parser = build_parser(True)

        args = dcos_parser.parse_args('info'.split())

        self.assertEqual(args.service, 'conductr')

    def test_default_with_dcos_info(self):
        dcos_parser = build_parser(True)

        args = dcos_parser.parse_args('--info'.split())

        self.assertEqual(args.dcos_info, True)

    def test_get_cli_parameters(self):
        mock_resolve_default_host = MagicMock(return_value='127.0.0.1')
        mock_resolve_default_ip = MagicMock(return_value='127.0.0.1')

        with patch('conductr_cli.host.resolve_default_host', mock_resolve_default_host), \
                patch('conductr_cli.host.resolve_default_ip', mock_resolve_default_ip):
            args = Namespace(dcos_mode=False, scheme='http', ip='127.0.0.1', port=9005, api_version='2')
            self.assertEqual(get_cli_parameters(args), '')

            args = Namespace(dcos_mode=False, scheme='http', ip='127.0.1.1', port=9005)
            self.assertEqual(get_cli_parameters(args), ' --ip 127.0.1.1')

            args = Namespace(dcos_mode=False, scheme='http', host='127.0.1.1', port=9005)
            self.assertEqual(get_cli_parameters(args), ' --host 127.0.1.1')

            args = Namespace(dcos_mode=False, scheme='http', ip='127.0.0.1', port=9006)
            self.assertEqual(get_cli_parameters(args), ' --port 9006')

            args = Namespace(dcos_mode=False, scheme='http', ip='127.0.0.1', port=9005, api_version='1')
            self.assertEqual(get_cli_parameters(args), ' --api-version 1')

            args = Namespace(dcos_mode=False, scheme='http', ip='127.0.1.1', port=9006, api_version='1')
            self.assertEqual(get_cli_parameters(args), ' --ip 127.0.1.1 --port 9006 --api-version 1')

        mock_resolve_default_host.assert_called_with()
        mock_resolve_default_ip.assert_called_with()
