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

    def test_no_bundles(self):
        http_method = self.respond_with(200, '[]')
        stdout = MagicMock()

        with patch('requests.get', http_method):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            result = conduct_services.services(MagicMock(**self.default_args))
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT)
        self.assertEqual(
            strip_margin("""|SERVICE  BUNDLE ID  BUNDLE NAME  STATUS
                            |"""),
            self.output(stdout))

    def test_two_bundles_mult_components_endpoints(self):
        http_method = self.respond_with_file_contents('data/bundle_with_services/two_bundles.json')
        stdout = MagicMock()

        with patch('requests.get', http_method):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            result = conduct_services.services(MagicMock(**self.default_args))
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT)
        self.assertEqual(
            as_warn(strip_margin("""|SERVICE                   BUNDLE ID  BUNDLE NAME                   STATUS
                                    |http://:6011/comp2-endp2  6e4560e    multi2-comp-multi-endp-1.0.0  Running
                                    |http://:7010/comp3-endp1  6e4560e    multi2-comp-multi-endp-1.0.0  Running
                                    |http://:7011/comp3-endp2  6e4560e    multi2-comp-multi-endp-1.0.0  Running
                                    |http://:8010/comp1-endp1  f804d64    multi-comp-multi-endp-1.0.0   Running
                                    |http://:8011/comp1-endp2  f804d64    multi-comp-multi-endp-1.0.0   Running
                                    |http://:9010/comp2-endp1  f804d64    multi-comp-multi-endp-1.0.0   Running
                                    |http://:9010/comp2-endp1  6e4560e    multi2-comp-multi-endp-1.0.0  Running
                                    |http://:9011/comp2-endp2  f804d64    multi-comp-multi-endp-1.0.0   Running
                                    |
                                    |Warning: Multiple endpoints found for the following services: /comp2-endp2
                                    |Warning: Service resolution for these services is undefined.
                                    |""")),
            self.output(stdout))

    def test_two_bundles_mult_components_endpoints_no_path(self):
        http_method = self.respond_with_file_contents('data/bundle_with_services/two_bundles_no_path.json')
        stdout = MagicMock()

        with patch('requests.get', http_method):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            result = conduct_services.services(MagicMock(**self.default_args))
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT)
        self.assertEqual(
            strip_margin("""|SERVICE                   BUNDLE ID  BUNDLE NAME                   STATUS
                            |http://:6011              6e4560e    multi2-comp-multi-endp-1.0.0  Running
                            |http://:7010/comp3-endp1  6e4560e    multi2-comp-multi-endp-1.0.0  Running
                            |http://:7011/comp3-endp2  6e4560e    multi2-comp-multi-endp-1.0.0  Running
                            |http://:8010/comp1-endp1  f804d64    multi-comp-multi-endp-1.0.0   Running
                            |http://:8011/comp1-endp2  f804d64    multi-comp-multi-endp-1.0.0   Running
                            |http://:9010/comp2-endp1  f804d64    multi-comp-multi-endp-1.0.0   Running
                            |http://:9010/comp2-endp1  6e4560e    multi2-comp-multi-endp-1.0.0  Running
                            |http://:9011              f804d64    multi-comp-multi-endp-1.0.0   Running
                            |"""),
            self.output(stdout))

    def test_one_bundle_starting(self):
        http_method = self.respond_with_file_contents('data/bundle_with_services/one_bundle_starting.json')
        stdout = MagicMock()

        with patch('requests.get', http_method):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            result = conduct_services.services(MagicMock(**self.default_args))
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT)
        self.assertEqual(
            strip_margin("""|SERVICE                   BUNDLE ID  BUNDLE NAME                  STATUS
                            |http://:8010/comp1-endp1  f804d64    multi-comp-multi-endp-1.0.0  Starting
                            |http://:8011/comp1-endp2  f804d64    multi-comp-multi-endp-1.0.0  Starting
                            |http://:9010/comp2-endp1  f804d64    multi-comp-multi-endp-1.0.0  Starting
                            |http://:9011/comp2-endp2  f804d64    multi-comp-multi-endp-1.0.0  Starting
                            |http://my.service         f804d64    multi-comp-multi-endp-1.0.0  Starting
                            |"""),
            self.output(stdout))

    def test_one_bundle_starting_long_ids(self):
        http_method = self.respond_with_file_contents('data/bundle_with_services/one_bundle_starting.json')
        stdout = MagicMock()

        with patch('requests.get', http_method):
            args = self.default_args.copy()
            args.update({'long_ids': True})
            logging_setup.configure_logging(MagicMock(**args), stdout)
            result = conduct_services.services(MagicMock(**args))
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT)
        self.assertEqual(
            strip_margin(
                """|SERVICE                   BUNDLE ID                         BUNDLE NAME                  STATUS
                   |http://:8010/comp1-endp1  f804d644a01a5ab9f679f76939f5c7e2  multi-comp-multi-endp-1.0.0  Starting
                   |http://:8011/comp1-endp2  f804d644a01a5ab9f679f76939f5c7e2  multi-comp-multi-endp-1.0.0  Starting
                   |http://:9010/comp2-endp1  f804d644a01a5ab9f679f76939f5c7e2  multi-comp-multi-endp-1.0.0  Starting
                   |http://:9011/comp2-endp2  f804d644a01a5ab9f679f76939f5c7e2  multi-comp-multi-endp-1.0.0  Starting
                   |http://my.service         f804d644a01a5ab9f679f76939f5c7e2  multi-comp-multi-endp-1.0.0  Starting
                   |"""),
            self.output(stdout))

    def test_one_bundle_no_services(self):
        http_method = self.respond_with_file_contents('data/bundle_with_acls/one_bundle_tcp.json')
        stdout = MagicMock()

        with patch('requests.get', http_method):
            args = self.default_args.copy()
            args.update({'long_ids': True})
            logging_setup.configure_logging(MagicMock(**args), stdout)
            result = conduct_services.services(MagicMock(**args))
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT)
        self.assertEqual(
            strip_margin("""|SERVICE  BUNDLE ID  BUNDLE NAME  STATUS
                        |"""),
            self.output(stdout))
