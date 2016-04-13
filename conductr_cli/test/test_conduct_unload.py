from conductr_cli.test.cli_test_case import CliTestCase, strip_margin, as_error
from conductr_cli import conduct_unload, logging_setup
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT

try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestConductUnloadCommand(CliTestCase):

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
        'no_wait': False,
        'quiet': False,
        'cli_parameters': '',
        'bundle': '45e0c477d3e5ea92aa8d85c0d8f3e25c'
    }

    default_url = 'http://127.0.0.1:9005/bundles/45e0c477d3e5ea92aa8d85c0d8f3e25c'

    output_template = """|Bundle unload request sent.
                         |Print ConductR info with: conduct info{params}
                         |"""

    mock_headers = {'pretend': 'header'}

    def default_output(self, params=''):
        return strip_margin(self.output_template.format(**{'params': params}))

    def test_success(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        wait_for_uninstallation_mock = MagicMock()
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.delete', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('conductr_cli.bundle_installation.wait_for_uninstallation', wait_for_uninstallation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_unload.unload(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        wait_for_uninstallation_mock.assert_called_with('45e0c477d3e5ea92aa8d85c0d8f3e25c', input_args)

        self.assertEqual(self.default_output(), self.output(stdout))

    def test_success_verbose(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        wait_for_uninstallation_mock = MagicMock()
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()

        args = self.default_args.copy()
        args.update({'verbose': True})
        input_args = MagicMock(**args)

        with patch('requests.delete', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('conductr_cli.bundle_installation.wait_for_uninstallation', wait_for_uninstallation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_unload.unload(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        wait_for_uninstallation_mock.assert_called_with('45e0c477d3e5ea92aa8d85c0d8f3e25c', input_args)

        self.assertEqual(self.default_response + self.default_output(), self.output(stdout))

    def test_success_quiet(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        wait_for_uninstallation_mock = MagicMock()
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()

        args = self.default_args.copy()
        args.update({'quiet': True})
        input_args = MagicMock(**args)

        with patch('requests.delete', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('conductr_cli.bundle_installation.wait_for_uninstallation', wait_for_uninstallation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_unload.unload(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        wait_for_uninstallation_mock.assert_called_with('45e0c477d3e5ea92aa8d85c0d8f3e25c', input_args)

        self.assertEqual('45e0c477d3e5ea92aa8d85c0d8f3e25c\n', self.output(stdout))

    def test_success_with_configuration(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        wait_for_uninstallation_mock = MagicMock()
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()

        args = self.default_args.copy()
        cli_parameters = ' --ip 127.0.1.1 --port 9006'
        args.update({'cli_parameters': cli_parameters})
        input_args = MagicMock(**args)

        with patch('requests.delete', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('conductr_cli.bundle_installation.wait_for_uninstallation', wait_for_uninstallation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_unload.unload(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        wait_for_uninstallation_mock.assert_called_with('45e0c477d3e5ea92aa8d85c0d8f3e25c', input_args)

        self.assertEqual(
            self.default_output(params=cli_parameters),
            self.output(stdout))

    def test_success_no_wait(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()

        args = self.default_args.copy()
        args.update({'no_wait': True})
        input_args = MagicMock(**args)
        with patch('requests.delete', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_unload.unload(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)

        self.assertEqual(self.default_output(), self.output(stdout))

    def test_failure(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with(404)
        stderr = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.delete', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, err_output=stderr)
            result = conduct_unload.unload(input_args)
            self.assertFalse(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)

        self.assertEqual(
            as_error(strip_margin("""|Error: 404 Not Found
                                     |""")),
            self.output(stderr))

    def test_failure_invalid_address(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.raise_connection_error('test reason', self.default_url)
        stderr = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.delete', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, err_output=stderr)
            result = conduct_unload.unload(input_args)
            self.assertFalse(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)

        self.assertEqual(
            self.default_connection_error.format(self.default_url),
            self.output(stderr))
