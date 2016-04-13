from conductr_cli.test.cli_test_case import CliTestCase, strip_margin, as_error
from conductr_cli import conduct_stop, logging_setup
from conductr_cli.exceptions import WaitTimeoutError
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

    bundle_id = '45e0c477d3e5ea92aa8d85c0d8f3e25c'

    default_args = {
        'ip': '127.0.0.1',
        'port': 9005,
        'api_version': '1',
        'verbose': False,
        'quiet': False,
        'no_wait': False,
        'long_ids': False,
        'cli_parameters': '',
        'bundle': bundle_id
    }

    default_url = 'http://127.0.0.1:9005/bundles/45e0c477d3e5ea92aa8d85c0d8f3e25c?scale=0'

    output_template = """|Bundle stop request sent.
                         |Unload bundle with: conduct unload{params} {bundle_id}
                         |Print ConductR info with: conduct info{params}
                         |"""

    mock_headers = {'pretend': 'header'}

    def default_output(self, params='', bundle_id='45e0c47'):
        return strip_margin(self.output_template.format(**{'params': params, 'bundle_id': bundle_id}))

    def test_success(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with(200, self.default_response)
        wait_for_scale_mock = MagicMock()
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.put', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('conductr_cli.bundle_scale.wait_for_scale', wait_for_scale_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_stop.stop(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        wait_for_scale_mock.assert_called_with(self.bundle_id, 0, input_args)

        self.assertEqual(self.default_output(), self.output(stdout))

    def test_success_verbose(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with(200, self.default_response)
        wait_for_scale_mock = MagicMock()
        stdout = MagicMock()

        args = self.default_args.copy()
        args.update({'verbose': True})
        input_args = MagicMock(**args)
        with patch('requests.put', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('conductr_cli.bundle_scale.wait_for_scale', wait_for_scale_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_stop.stop(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        wait_for_scale_mock.assert_called_with(self.bundle_id, 0, input_args)

        self.assertEqual(self.default_response + self.default_output(), self.output(stdout))

    def test_success_long_ids(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with(200, self.default_response)
        wait_for_scale_mock = MagicMock()
        stdout = MagicMock()

        args = self.default_args.copy()
        args.update({'long_ids': True})
        input_args = MagicMock(**args)
        with patch('requests.put', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('conductr_cli.bundle_scale.wait_for_scale', wait_for_scale_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_stop.stop(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        wait_for_scale_mock.assert_called_with(self.bundle_id, 0, input_args)

        self.assertEqual(self.default_output(bundle_id='45e0c477d3e5ea92aa8d85c0d8f3e25c'), self.output(stdout))

    def test_success_with_configuration(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with(200, self.default_response)
        wait_for_scale_mock = MagicMock()
        stdout = MagicMock()

        args = self.default_args.copy()
        cli_parameters = ' --ip 127.0.1.1 --port 9006'
        args.update({'cli_parameters': cli_parameters})
        input_args = MagicMock(**args)

        with patch('requests.put', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('conductr_cli.bundle_scale.wait_for_scale', wait_for_scale_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_stop.stop(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        wait_for_scale_mock.assert_called_with(self.bundle_id, 0, input_args)

        self.assertEqual(
            self.default_output(params=cli_parameters),
            self.output(stdout))

    def test_failure(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with(404)
        stderr = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.put', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, err_output=stderr)
            result = conduct_stop.stop(input_args)
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
        with patch('requests.put', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, err_output=stderr)
            result = conduct_stop.stop(input_args)
            self.assertFalse(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)

        self.assertEqual(
            self.default_connection_error.format(self.default_url),
            self.output(stderr))

    def test_failure_stop_timeout(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with(200, self.default_response)
        wait_for_scale_mock = MagicMock(side_effect=WaitTimeoutError('test timeout error'))
        stderr = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.put', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('conductr_cli.bundle_scale.wait_for_scale', wait_for_scale_mock):
            logging_setup.configure_logging(input_args, err_output=stderr)
            result = conduct_stop.stop(input_args)
            self.assertFalse(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        wait_for_scale_mock.assert_called_with(self.bundle_id, 0, input_args)

        self.assertEqual(
            as_error(strip_margin("""|Error: Timed out: test timeout error
                                     |""")),
            self.output(stderr))
