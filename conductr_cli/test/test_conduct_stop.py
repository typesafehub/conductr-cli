from conductr_cli.test.cli_test_case import CliTestCase, strip_margin, as_error
from conductr_cli import conduct_stop, logging_setup
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT


try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestConductStopCommand(CliTestCase):

    @property
    def default_response(self):
        return strip_margin("""|{
                               |  "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c"
                               |}
                               |""")

    default_args = {
        'ip': '127.0.0.1',
        'port': 9005,
        'api_version': '1',
        'verbose': False,
        'quiet': False,
        'long_ids': False,
        'cli_parameters': '',
        'bundle': '45e0c477d3e5ea92aa8d85c0d8f3e25c'
    }

    default_url = 'http://127.0.0.1:9005/bundles/45e0c477d3e5ea92aa8d85c0d8f3e25c?scale=0'

    output_template = """|Bundle stop request sent.
                         |Unload bundle with: conduct unload{params} {bundle_id}
                         |Print ConductR info with: conduct info{params}
                         |"""

    def default_output(self, params='', bundle_id='45e0c47'):
        return strip_margin(self.output_template.format(**{'params': params, 'bundle_id': bundle_id}))

    def test_success(self):
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()

        with patch('requests.put', http_method):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            conduct_stop.stop(MagicMock(**self.default_args))

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT)

        self.assertEqual(self.default_output(), self.output(stdout))

    def test_success_verbose(self):
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()

        with patch('requests.put', http_method):
            args = self.default_args.copy()
            args.update({'verbose': True})
            logging_setup.configure_logging(MagicMock(**args), stdout)
            conduct_stop.stop(MagicMock(**args))

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT)

        self.assertEqual(self.default_response + self.default_output(), self.output(stdout))

    def test_success_long_ids(self):
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()

        with patch('requests.put', http_method):
            args = self.default_args.copy()
            args.update({'long_ids': True})
            logging_setup.configure_logging(MagicMock(**args), stdout)
            conduct_stop.stop(MagicMock(**args))

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT)

        self.assertEqual(self.default_output(bundle_id='45e0c477d3e5ea92aa8d85c0d8f3e25c'), self.output(stdout))

    def test_success_with_configuration(self):
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()

        cli_parameters = ' --ip 127.0.1.1 --port 9006'
        with patch('requests.put', http_method):
            args = self.default_args.copy()
            args.update({'cli_parameters': cli_parameters})
            logging_setup.configure_logging(MagicMock(**args), stdout)
            conduct_stop.stop(MagicMock(**args))

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT)

        self.assertEqual(
            self.default_output(params=cli_parameters),
            self.output(stdout))

    def test_failure(self):
        http_method = self.respond_with(404)
        stderr = MagicMock()

        with patch('requests.put', http_method):
            logging_setup.configure_logging(MagicMock(**self.default_args), err_output=stderr)
            conduct_stop.stop(MagicMock(**self.default_args))

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT)

        self.assertEqual(
            as_error(strip_margin("""|Error: 404 Not Found
                                     |""")),
            self.output(stderr))

    def test_failure_invalid_address(self):
        http_method = self.raise_connection_error('test reason', self.default_url)
        stderr = MagicMock()

        with patch('requests.put', http_method):
            logging_setup.configure_logging(MagicMock(**self.default_args), err_output=stderr)
            conduct_stop.stop(MagicMock(**self.default_args))

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT)

        self.assertEqual(
            self.default_connection_error.format(self.default_url),
            self.output(stderr))
