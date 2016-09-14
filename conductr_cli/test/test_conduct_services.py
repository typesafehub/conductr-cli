from conductr_cli.test.cli_test_case import CliTestCase, strip_margin, as_warn
from conductr_cli import conduct_services, logging_setup
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT


try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestConductServicesCommand(CliTestCase):

    default_args = {
        'ip': '127.0.0.1',
        'port': 9005,
        'api_version': '1',
        'verbose': False,
        'long_ids': False
    }

    default_url = 'http://127.0.0.1:9005/bundles'

    mock_headers = {'pretend': 'header'}

    def test_no_bundles(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with(200, '[]')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_services.services(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        self.assertEqual(
            strip_margin("""|SERVICE NAME  BUNDLE ID  BUNDLE NAME  STATUS
                            |"""),
            self.output(stdout))

    def test_two_bundles_mult_components_endpoints(self):
        self.maxDiff = None
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with_file_contents('data/bundle_with_services/two_bundles.json')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_services.services(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
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
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with_file_contents('data/bundle_with_services/two_bundles_no_path.json')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_services.services(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
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
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with_file_contents('data/bundle_with_services/one_bundle_starting.json')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_services.services(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        self.assertEqual(
            strip_margin("""|SERVICE NAME  BUNDLE ID  BUNDLE NAME                  STATUS
                            |comp1-endp1   f804d64    multi-comp-multi-endp-1.0.0  Starting
                            |comp1-endp2   f804d64    multi-comp-multi-endp-1.0.0  Starting
                            |comp2-endp1   f804d64    multi-comp-multi-endp-1.0.0  Starting
                            |comp2-endp2   f804d64    multi-comp-multi-endp-1.0.0  Starting
                            |"""),
            self.output(stdout))

    def test_one_bundle_starting_long_ids(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with_file_contents('data/bundle_with_services/one_bundle_starting.json')
        stdout = MagicMock()

        args = self.default_args.copy()
        args.update({'long_ids': True})
        input_args = MagicMock(**args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_services.services(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
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
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with_file_contents('data/bundle_with_acls/one_bundle_tcp.json')
        stdout = MagicMock()

        args = self.default_args.copy()
        args.update({'long_ids': True})
        input_args = MagicMock(**args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_services.services(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        self.assertEqual(
            strip_margin(
                """|SERVICE NAME  BUNDLE ID  BUNDLE NAME  STATUS
                   |"""),
            self.output(stdout))

    def test_one_bundle_multiple_executions(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with_file_contents('data/bundle_with_services/one_bundle_multiple_executions.json')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_services.services(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        self.assertEqual(
            strip_margin(
                """|SERVICE NAME  BUNDLE ID  BUNDLE NAME                  STATUS
                   |comp1-endp1   f804d64    multi-comp-multi-endp-1.0.0  Running
                   |"""),
            self.output(stdout))

    def test_mix_acls_and_service_uris(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with_file_contents('data/bundle_with_acls_and_services/http_acl_and_service.json')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_services.services(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        self.assertEqual(
            strip_margin(
                """|SERVICE NAME  BUNDLE ID  BUNDLE NAME                 STATUS
                   |my-endp1      f804d64    bundle-with-acl-1.0.0       Running
                   |my-svc1       ga04d64    bundle-with-services-1.0.0  Starting
                   |my-svc2       ga04d64    bundle-with-services-1.0.0  Starting
                   |"""),
            self.output(stdout))
