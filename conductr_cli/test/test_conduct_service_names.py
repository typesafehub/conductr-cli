from conductr_cli.test.cli_test_case import CliTestCase, strip_margin, as_warn
from conductr_cli import conduct_service_names, logging_setup
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT
from unittest.mock import patch, MagicMock


class TestConductServiceNamesCommand(CliTestCase):

    default_args = {
        'dcos_mode': False,
        'scheme': 'http',
        'host': '127.0.0.1',
        'port': 9005,
        'base_path': '/',
        'api_version': '1',
        'verbose': False,
        'long_ids': False
    }

    default_url = 'http://127.0.0.1:9005/bundles'

    def test_no_bundles(self):
        http_method = self.respond_with(200, '[]')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_service_names.service_names(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin("""|SERVICE NAME  BUNDLE ID  BUNDLE NAME  STATUS
                            |"""),
            self.output(stdout))

    def test_two_bundles_mult_components_endpoints(self):
        self.maxDiff = None
        http_method = self.respond_with_file_contents('data/bundle_with_services/two_bundles.json')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_service_names.service_names(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            as_warn(strip_margin("""|SERVICE NAME  BUNDLE ID  BUNDLE NAME                   STATUS
                                    |comp1-endp1   f804d64    multi-comp-multi-endp-1.0.0   Running
                                    |comp1-endp2   f804d64    multi-comp-multi-endp-1.0.0   Running
                                    |comp2-endp1   f804d64    multi-comp-multi-endp-1.0.0   Running
                                    |comp2-endp1   6e4560e    multi2-comp-multi-endp-1.0.0  Running
                                    |comp2-endp2   f804d64    multi-comp-multi-endp-1.0.0   Running
                                    |comp2-endp2   6e4560e    multi2-comp-multi-endp-1.0.0  Running
                                    |comp3-endp1   6e4560e    multi2-comp-multi-endp-1.0.0  Running
                                    |comp3-endp2   6e4560e    multi2-comp-multi-endp-1.0.0  Running
                                    |
                                    |Warning: Multiple endpoints found for the following services: /comp2-endp2
                                    |Warning: Service resolution for these services is undefined.
                                    |""")),
            self.output(stdout))

    def test_two_bundles_mult_components_endpoints_no_path(self):
        http_method = self.respond_with_file_contents('data/bundle_with_services/two_bundles_no_path.json')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_service_names.service_names(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin("""|SERVICE NAME  BUNDLE ID  BUNDLE NAME                   STATUS
                            |comp1-endp1   f804d64    multi-comp-multi-endp-1.0.0   Running
                            |comp1-endp2   f804d64    multi-comp-multi-endp-1.0.0   Running
                            |comp2-endp1   f804d64    multi-comp-multi-endp-1.0.0   Running
                            |comp2-endp1   6e4560e    multi2-comp-multi-endp-1.0.0  Running
                            |comp3-endp1   6e4560e    multi2-comp-multi-endp-1.0.0  Running
                            |comp3-endp2   6e4560e    multi2-comp-multi-endp-1.0.0  Running
                            |"""),
            self.output(stdout))

    def test_one_bundle_starting(self):
        http_method = self.respond_with_file_contents('data/bundle_with_services/one_bundle_starting.json')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_service_names.service_names(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin("""|SERVICE NAME  BUNDLE ID  BUNDLE NAME                  STATUS
                            |comp1-endp1   f804d64    multi-comp-multi-endp-1.0.0  Starting
                            |comp1-endp2   f804d64    multi-comp-multi-endp-1.0.0  Starting
                            |comp2-endp1   f804d64    multi-comp-multi-endp-1.0.0  Starting
                            |comp2-endp2   f804d64    multi-comp-multi-endp-1.0.0  Starting
                            |"""),
            self.output(stdout))

    def test_one_bundle_starting_long_ids(self):
        http_method = self.respond_with_file_contents('data/bundle_with_services/one_bundle_starting.json')
        stdout = MagicMock()

        args = self.default_args.copy()
        args.update({'long_ids': True})
        input_args = MagicMock(**args)
        with patch('requests.get', http_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_service_names.service_names(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin(
                """|SERVICE NAME  BUNDLE ID                         BUNDLE NAME                  STATUS
                   |comp1-endp1   f804d644a01a5ab9f679f76939f5c7e2  multi-comp-multi-endp-1.0.0  Starting
                   |comp1-endp2   f804d644a01a5ab9f679f76939f5c7e2  multi-comp-multi-endp-1.0.0  Starting
                   |comp2-endp1   f804d644a01a5ab9f679f76939f5c7e2  multi-comp-multi-endp-1.0.0  Starting
                   |comp2-endp2   f804d644a01a5ab9f679f76939f5c7e2  multi-comp-multi-endp-1.0.0  Starting
                   |"""),
            self.output(stdout))

    def test_one_bundle_no_services(self):
        http_method = self.respond_with_file_contents('data/bundle_with_acls/one_bundle_tcp.json')
        stdout = MagicMock()

        args = self.default_args.copy()
        args.update({'long_ids': True})
        input_args = MagicMock(**args)
        with patch('requests.get', http_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_service_names.service_names(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin(
                """|SERVICE NAME  BUNDLE ID  BUNDLE NAME  STATUS
                   |"""),
            self.output(stdout))

    def test_one_bundle_multiple_executions(self):
        http_method = self.respond_with_file_contents('data/bundle_with_services/one_bundle_multiple_executions.json')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_service_names.service_names(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin(
                """|SERVICE NAME  BUNDLE ID  BUNDLE NAME                  STATUS
                   |comp1-endp1   f804d64    multi-comp-multi-endp-1.0.0  Running
                   |"""),
            self.output(stdout))

    def test_mix_acls_and_service_uris(self):
        http_method = self.respond_with_file_contents('data/bundle_with_acls_and_services/http_acl_and_service.json')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_service_names.service_names(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin(
                """|SERVICE NAME  BUNDLE ID  BUNDLE NAME                 STATUS
                   |my-endp1      f804d64    bundle-with-acl-1.0.0       Running
                   |my-svc1       ga04d64    bundle-with-services-1.0.0  Starting
                   |my-svc2       ga04d64    bundle-with-services-1.0.0  Starting
                   |"""),
            self.output(stdout))

    def test_ip(self):
        args = {}
        args.update(self.default_args)
        args.pop('host')
        args.update({'ip': '10.0.0.1'})

        http_method = self.respond_with(200, '[]')
        stdout = MagicMock()

        input_args = MagicMock(**args)
        with patch('requests.get', http_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_service_names.service_names(input_args)
            self.assertTrue(result)

        default_url = 'http://10.0.0.1:9005/bundles'
        http_method.assert_called_with(default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '10.0.0.1'})
        self.assertEqual(
            strip_margin("""|SERVICE NAME  BUNDLE ID  BUNDLE NAME  STATUS
                            |"""),
            self.output(stdout))
