from unittest import TestCase
from unittest.mock import patch, MagicMock
from typesafe_conductr_cli.test.cli_test_case import CliTestCase
from typesafe_conductr_cli import conduct_services


class TestConductInfoCommand(TestCase, CliTestCase):

    default_args = {
        'ip': '127.0.0.1',
        'port': 9005,
        'verbose': False,
        'long_ids': False
    }

    default_url = 'http://127.0.0.1:9005/bundles'

    def test_two_bundles_mult_components_endpoints(self):
        http_method = self.respond_with_file_contents('data/two_bundles.json')
        stdout = MagicMock()

        with patch('requests.get', http_method), patch('sys.stdout', stdout):
            conduct_services.services(MagicMock(**self.default_args))

        http_method.assert_called_with(self.default_url)
        self.assertEqual(
            self.strip_margin("""|PROTO  SERVICE           BUNDLE ID  BUNDLE NAME                   STATUS
                                 |http   8010/comp1-endp1  f804d64    multi-comp-multi-endp-1.0.0   Running
                                 |http   8011/comp1-endp2  f804d64    multi-comp-multi-endp-1.0.0   Running
                                 |http   9010/comp2-endp1  f804d64    multi-comp-multi-endp-1.0.0   Running
                                 |http   6010/comp2-endp1  6e4560e    multi2-comp-multi-endp-1.0.0  Running
                                 |http   9011/comp2-endp2  f804d64    multi-comp-multi-endp-1.0.0   Running
                                 |http   6011/comp2-endp2  6e4560e    multi2-comp-multi-endp-1.0.0  Running
                                 |http   7010/comp3-endp1  6e4560e    multi2-comp-multi-endp-1.0.0  Running
                                 |http   7011/comp3-endp2  6e4560e    multi2-comp-multi-endp-1.0.0  Running
                                 |
                                 |WARNING: Multiple endpoints found for the following services: /comp2-endp1, /comp2-endp2
                                 |WARNING: Service resolution for these services is undefined.
                                 |"""),
            self.output(stdout))

    def test_one_bundle_starting(self):
        http_method = self.respond_with_file_contents('data/one_bundle_starting.json')
        stdout = MagicMock()

        with patch('requests.get', http_method), patch('sys.stdout', stdout):
            conduct_services.services(MagicMock(**self.default_args))

        http_method.assert_called_with(self.default_url)
        self.assertEqual(
            self.strip_margin("""|PROTO  SERVICE           BUNDLE ID  BUNDLE NAME                  STATUS
                                 |http   8010/comp1-endp1  f804d64    multi-comp-multi-endp-1.0.0  Starting
                                 |http   8011/comp1-endp2  f804d64    multi-comp-multi-endp-1.0.0  Starting
                                 |http   9010/comp2-endp1  f804d64    multi-comp-multi-endp-1.0.0  Starting
                                 |http   9011/comp2-endp2  f804d64    multi-comp-multi-endp-1.0.0  Starting
                                 |"""),
            self.output(stdout))

    def test_one_bundle_starting_long_ids(self):
        http_method = self.respond_with_file_contents('data/one_bundle_starting.json')
        stdout = MagicMock()

        with patch('requests.get', http_method), patch('sys.stdout', stdout):
            args = self.default_args.copy()
            args.update({'long_ids': True})
            conduct_services.services(MagicMock(**args))

        http_method.assert_called_with(self.default_url)
        self.assertEqual(
            self.strip_margin("""|PROTO  SERVICE           BUNDLE ID                         BUNDLE NAME                  STATUS
                                 |http   8010/comp1-endp1  f804d644a01a5ab9f679f76939f5c7e2  multi-comp-multi-endp-1.0.0  Starting
                                 |http   8011/comp1-endp2  f804d644a01a5ab9f679f76939f5c7e2  multi-comp-multi-endp-1.0.0  Starting
                                 |http   9010/comp2-endp1  f804d644a01a5ab9f679f76939f5c7e2  multi-comp-multi-endp-1.0.0  Starting
                                 |http   9011/comp2-endp2  f804d644a01a5ab9f679f76939f5c7e2  multi-comp-multi-endp-1.0.0  Starting
                                 |"""),
            self.output(stdout))
