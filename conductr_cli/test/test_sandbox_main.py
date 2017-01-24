from conductr_cli.test.cli_test_case import CliTestCase
from conductr_cli import sandbox_main
from conductr_cli.constants import DEFAULT_SANDBOX_ADDR_RANGE, DEFAULT_SANDBOX_IMAGE_DIR
from conductr_cli.sandbox_common import CONDUCTR_DEV_IMAGE
from conductr_cli.test.data.test_constants import LATEST_CONDUCTR_VERSION
import argparse
import ipaddress


class TestSandbox(CliTestCase):

    parser = sandbox_main.build_parser()

    def test_parser_run_default_args(self):
        args = self.parser.parse_args('run {}'.format(LATEST_CONDUCTR_VERSION).split())
        self.assertEqual(args.func.__name__, 'run')
        self.assertEqual(args.image_version, LATEST_CONDUCTR_VERSION)
        self.assertEqual(args.conductr_roles, [])
        self.assertEqual(args.envs, [])
        self.assertEqual(args.image, CONDUCTR_DEV_IMAGE)
        self.assertEqual(args.log_level, 'info')
        self.assertEqual(args.nr_of_instances, '1')
        self.assertEqual(args.ports, [])
        self.assertEqual(args.features, [])
        self.assertEqual(args.local_connection, True)
        self.assertEqual(args.resolve_ip, True)
        self.assertEqual(args.addr_range, ipaddress.ip_network(DEFAULT_SANDBOX_ADDR_RANGE, strict=True))
        self.assertEqual(args.image_dir, DEFAULT_SANDBOX_IMAGE_DIR)

    def test_parser_run_custom_args(self):
        args = self.parser.parse_args('run 1.1.0 '
                                      '--conductr-role role1 role2 -r role3 '
                                      '--env env1 -e env2 '
                                      '--image my-image '
                                      '--log-level debug '
                                      '--nr-of-containers 5 '
                                      '--port 1000 -p 1001 '
                                      '--bundle-http-port 7111 '
                                      '--image-dir /foo/bar '
                                      '--addr-range 192.168.10.0/24 '
                                      '--feature visualization -f logging -f monitoring 2.1.0'.split())
        self.assertEqual(args.func.__name__, 'run')
        self.assertEqual(args.image_version, '1.1.0')
        self.assertEqual(args.conductr_roles, [['role1', 'role2'], ['role3']])
        self.assertEqual(args.envs, ['env1', 'env2'])
        self.assertEqual(args.image, 'my-image')
        self.assertEqual(args.log_level, 'debug')
        self.assertEqual(args.nr_of_instances, '5')
        self.assertEqual(args.ports, [1000, 1001])
        self.assertEqual(args.features, [['visualization'], ['logging'], ['monitoring', '2.1.0']])
        self.assertEqual(args.local_connection, True)
        self.assertEqual(args.resolve_ip, True)
        self.assertEqual(args.bundle_http_port, 7111)
        self.assertEqual(args.addr_range, ipaddress.ip_network('192.168.10.0/24', strict=True))
        self.assertEqual(args.image_dir, '/foo/bar')

    def test_parser_run_multiple_core_agent_instances(self):
        args = self.parser.parse_args('run 1.1.0 '
                                      '--conductr-role role1 role2 -r role3 '
                                      '--env env1 -e env2 '
                                      '--image my-image '
                                      '--log-level debug '
                                      '--nr-of-containers 5:3 '
                                      '--port 1000 -p 1001 '
                                      '--bundle-http-port 7111 '
                                      '--feature visualization -f logging -f monitoring 2.1.0'.split())
        self.assertEqual(args.func.__name__, 'run')
        self.assertEqual(args.image_version, '1.1.0')
        self.assertEqual(args.conductr_roles, [['role1', 'role2'], ['role3']])
        self.assertEqual(args.envs, ['env1', 'env2'])
        self.assertEqual(args.image, 'my-image')
        self.assertEqual(args.log_level, 'debug')
        self.assertEqual(args.nr_of_instances, '5:3')
        self.assertEqual(args.ports, [1000, 1001])
        self.assertEqual(args.features, [['visualization'], ['logging'], ['monitoring', '2.1.0']])
        self.assertEqual(args.local_connection, True)
        self.assertEqual(args.resolve_ip, True)
        self.assertEqual(args.bundle_http_port, 7111)

    def test_parser_stop(self):
        args = self.parser.parse_args('stop'.split())
        self.assertEqual(args.func.__name__, 'stop')
        self.assertEqual(args.local_connection, True)
        self.assertEqual(args.resolve_ip, True)

    def test_parser_ps(self):
        args = self.parser.parse_args('ps'.split())
        self.assertEqual(args.func.__name__, 'ps')
        self.assertEqual(args.local_connection, True)
        self.assertEqual(args.resolve_ip, True)
        self.assertEqual(args.is_filter_core, False)
        self.assertEqual(args.is_filter_agent, False)
        self.assertEqual(args.is_quiet, False)

    def test_parser_ps_core(self):
        args = self.parser.parse_args('ps --core --quiet'.split())
        self.assertEqual(args.func.__name__, 'ps')
        self.assertEqual(args.local_connection, True)
        self.assertEqual(args.is_filter_core, True)
        self.assertEqual(args.is_filter_agent, False)
        self.assertEqual(args.is_quiet, True)

    def test_parser_ps_agent(self):
        args = self.parser.parse_args('ps --agent --quiet'.split())
        self.assertEqual(args.func.__name__, 'ps')
        self.assertEqual(args.local_connection, True)
        self.assertEqual(args.is_filter_core, False)
        self.assertEqual(args.is_filter_agent, True)
        self.assertEqual(args.is_quiet, True)

    def test_parser_version(self):
        args = self.parser.parse_args('version'.split())
        self.assertEqual(args.func.__name__, 'version')


class TestValidation(CliTestCase):
    def test_nr_of_instances_valid_int(self):
        self.assertEqual('1', sandbox_main.nr_of_instances('1'))

    def test_nr_of_instances_valid_expression(self):
        self.assertEqual('1:3', sandbox_main.nr_of_instances('1:3'))

    def test_nr_of_instances_invalid(self):
        self.assertRaises(argparse.ArgumentTypeError, sandbox_main.nr_of_instances, 'FOO')

    def test_addr_range_valid(self):
        self.assertEqual(ipaddress.ip_network('192.168.1.0/24', strict=True), sandbox_main.addr_range('192.168.1.0/24'))

    def test_addr_range_invalid(self):
        self.assertRaises(argparse.ArgumentTypeError, sandbox_main.addr_range, 'FOO')
