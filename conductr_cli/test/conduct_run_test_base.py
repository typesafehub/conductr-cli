from conductr_cli.test.cli_test_case import CliTestCase, strip_margin, as_error
from conductr_cli import conduct_run, logging_setup
from conductr_cli.exceptions import WaitTimeoutError

try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class ConductRunTestBase(CliTestCase):

    def __init__(self, method_name):
        super().__init__(method_name)

        self.bundle_id = None
        self.scale = None
        self.default_args = {}
        self.default_url = None
        self.output_template = None
        self.mock_headers = {'pretend': 'header'}

    @property
    def default_response(self):
        return strip_margin("""|{
                               |  "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c"
                               |}
                               |""")

    def default_output(self, params='', bundle_id='45e0c47'):
        return strip_margin(self.output_template.format(**{'params': params, 'bundle_id': bundle_id}))

    def base_test_success(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with(200, self.default_response)
        wait_for_scale_mock = MagicMock()
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)

        with patch('requests.put', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('conductr_cli.bundle_scale.wait_for_scale', wait_for_scale_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_run.run(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, headers=self.mock_headers)
        wait_for_scale_mock.assert_called_with(self.bundle_id, self.scale, input_args)

        self.assertEqual(self.default_output(), self.output(stdout))

    def base_test_success_verbose(self):
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
            result = conduct_run.run(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, headers=self.mock_headers)
        wait_for_scale_mock.assert_called_with(self.bundle_id, self.scale, input_args)

        self.assertEqual(self.default_response + self.default_output(), self.output(stdout))

    def base_test_success_long_ids(self):
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
            result = conduct_run.run(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, headers=self.mock_headers)
        wait_for_scale_mock.assert_called_with(self.bundle_id, self.scale, input_args)

        self.assertEqual(self.default_output(bundle_id='45e0c477d3e5ea92aa8d85c0d8f3e25c'), self.output(stdout))

    def base_test_success_with_configuration(self):
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
            result = conduct_run.run(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, headers=self.mock_headers)
        wait_for_scale_mock.assert_called_with(self.bundle_id, self.scale, input_args)

        self.assertEqual(
            self.default_output(params=cli_parameters),
            self.output(stdout))

    def base_test_success_no_wait(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()

        args = self.default_args.copy()
        args.update({'no_wait': True})
        input_args = MagicMock(**args)

        with patch('requests.put', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_run.run(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, headers=self.mock_headers)

        self.assertEqual(self.default_output(), self.output(stdout))

    def base_test_failure(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with(404)
        stderr = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.put', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, err_output=stderr)
            result = conduct_run.run(input_args)
            self.assertFalse(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, headers=self.mock_headers)

        self.assertEqual(
            as_error(strip_margin("""|Error: 404 Not Found
                                     |""")),
            self.output(stderr))

    def base_test_failure_invalid_address(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.raise_connection_error('test reason', self.default_url)
        stderr = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.put', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, err_output=stderr)
            result = conduct_run.run(input_args)
            self.assertFalse(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, headers=self.mock_headers)

        self.assertEqual(
            self.default_connection_error.format(self.default_url),
            self.output(stderr))

    def base_test_failure_scale_timeout(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with(200, self.default_response)
        wait_for_scale_mock = MagicMock(side_effect=WaitTimeoutError('test wait timeout error'))
        stderr = MagicMock()

        input_args = MagicMock(**self.default_args)

        with patch('requests.put', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('conductr_cli.bundle_scale.wait_for_scale', wait_for_scale_mock):
            logging_setup.configure_logging(input_args, err_output=stderr)
            result = conduct_run.run(input_args)
            self.assertFalse(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, headers=self.mock_headers)
        wait_for_scale_mock.assert_called_with(self.bundle_id, self.scale, input_args)

        self.assertEqual(
            as_error(strip_margin("""|Error: Timed out: test wait timeout error
                                     |""")),
            self.output(stderr))
