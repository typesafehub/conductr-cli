from unittest import TestCase
from conductr_cli.conduct_main import build_parser, get_cli_parameters
from argparse import Namespace
import os


class TestConduct(TestCase):

    parser = build_parser()

    def test_parser_version(self):
        args = self.parser.parse_args('version'.split())

        self.assertEqual(args.func.__name__, 'version')

    def test_default(self):
        args = self.parser.parse_args(
            'info --ip 127.0.1.1 --port 9999 -v --long-ids --api-version 1 '
            '--settings-dir /settings-dir --custom-plugins-dir /custom-plugins-dir'.split())

        self.assertEqual(args.func.__name__, 'info')
        self.assertEqual(args.ip, '127.0.1.1')
        self.assertEqual(args.port, 9999)
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

    def test_parser_services(self):
        args = self.parser.parse_args('services'.split())

        self.assertEqual(args.func.__name__, 'services')
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
        self.assertEqual(args.resolve_cache_dir, '{}/.conductr/cache'.format(os.path.expanduser('~')))
        self.assertEqual(args.verbose, False)
        self.assertEqual(args.long_ids, False)
        self.assertEqual(args.no_wait, False)
        self.assertEqual(args.wait_timeout, 60)
        self.assertEqual(args.bundle, 'path-to-bundle')
        self.assertEqual(args.configuration, 'path-to-conf')

    def test_parser_load_with_custom_resolve_cache_dir(self):
        args = self.parser.parse_args('load --resolve-cache-dir /somewhere path-to-bundle path-to-conf'.split())

        self.assertEqual(args.func.__name__, 'load')
        self.assertEqual(args.ip, None)
        self.assertEqual(args.port, 9005)
        self.assertEqual(args.api_version, '2')
        self.assertEqual(args.cli_settings_dir, '{}/.conductr'.format(os.path.expanduser('~')))
        self.assertEqual(args.resolve_cache_dir, '/somewhere')
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

    def test_get_cli_parameters(self):
        args = Namespace(ip=None, port=9005, api_version='2')
        self.assertEqual(get_cli_parameters(args), '')

        args = Namespace(ip='127.0.1.1', port=9005)
        self.assertEqual(get_cli_parameters(args), ' --ip 127.0.1.1')

        args = Namespace(ip=None, port=9006)
        self.assertEqual(get_cli_parameters(args), ' --port 9006')

        args = Namespace(ip=None, port=9005, api_version='1')
        self.assertEqual(get_cli_parameters(args), ' --api-version 1')

        args = Namespace(ip='127.0.1.1', port=9006, api_version='1')
        self.assertEqual(get_cli_parameters(args), ' --ip 127.0.1.1 --port 9006 --api-version 1')
