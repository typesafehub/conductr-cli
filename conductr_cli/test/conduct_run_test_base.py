from conductr_cli.test.cli_test_case import CliTestCase, strip_margin, as_error
from conductr_cli import conduct_run, logging_setup
from conductr_cli.exceptions import WaitTimeoutError
from unittest.mock import patch, MagicMock


class ConductRunTestBase(CliTestCase):

    def __init__(self, method_name):
        super().__init__(method_name)

        self.bundle_id = None
        self.scale = None
        self.default_args = {}
        self.default_url = None
        self.output_template = None
        self.mock_headers = {'pretend': 'header'}
        self.conductr_auth = ('username', 'password')
        self.server_verification_file = MagicMock(name='server_verification_file')

    @property
    def default_response(self):
        return strip_margin("""|{
                               |  "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c"
                               |}
                               |""")

    def default_output(self, params='', bundle_id='45e0c47'):
        return strip_margin(self.output_template.format(**{'params': params, 'bundle_id': bundle_id}))

    def base_test_success(self):
        http_method = self.respond_with(200, self.default_response)
        wait_for_scale_mock = MagicMock()
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)

        with patch('requests.put', http_method), \
                patch('conductr_cli.bundle_scale.wait_for_scale', wait_for_scale_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_run.run(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       headers={'Host': '127.0.0.1'})
        wait_for_scale_mock.assert_called_with(self.bundle_id, self.scale, wait_for_is_active=True, args=input_args)

        self.assertEqual(self.default_output(), self.output(stdout))

    def base_test_success_verbose(self):
        http_method = self.respond_with(200, self.default_response)
        wait_for_scale_mock = MagicMock()
        stdout = MagicMock()

        args = self.default_args.copy()
        args.update({'verbose': True})
        input_args = MagicMock(**args)

        with patch('requests.put', http_method), \
                patch('conductr_cli.bundle_scale.wait_for_scale', wait_for_scale_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_run.run(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       headers={'Host': '127.0.0.1'})
        wait_for_scale_mock.assert_called_with(self.bundle_id, self.scale, wait_for_is_active=True, args=input_args)

        self.assertEqual(self.default_response + self.default_output(), self.output(stdout))

    def base_test_success_long_ids(self):
        http_method = self.respond_with(200, self.default_response)
        wait_for_scale_mock = MagicMock()
        stdout = MagicMock()

        args = self.default_args.copy()
        args.update({'long_ids': True})
        input_args = MagicMock(**args)

        with patch('requests.put', http_method), \
                patch('conductr_cli.bundle_scale.wait_for_scale', wait_for_scale_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_run.run(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       headers={'Host': '127.0.0.1'})
        wait_for_scale_mock.assert_called_with(self.bundle_id, self.scale, wait_for_is_active=True, args=input_args)

        self.assertEqual(self.default_output(bundle_id='45e0c477d3e5ea92aa8d85c0d8f3e25c'), self.output(stdout))

    def base_test_success_with_custom_ip_port(self):
        http_method = self.respond_with(200, self.default_response)
        wait_for_scale_mock = MagicMock()
        stdout = MagicMock()

        args = self.default_args.copy()
        cli_parameters = ' --ip 127.0.1.1 --port 9006'
        args.update({'cli_parameters': cli_parameters})
        input_args = MagicMock(**args)

        with patch('requests.put', http_method), \
                patch('conductr_cli.bundle_scale.wait_for_scale', wait_for_scale_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_run.run(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       headers={'Host': '127.0.0.1'})
        wait_for_scale_mock.assert_called_with(self.bundle_id, self.scale, wait_for_is_active=True, args=input_args)

        self.assertEqual(
            self.default_output(params=cli_parameters),
            self.output(stdout))

    def base_test_success_with_custom_host_port(self):
        http_method = self.respond_with(200, self.default_response)
        wait_for_scale_mock = MagicMock()
        stdout = MagicMock()

        args = self.default_args.copy()
        cli_parameters = ' --host 127.0.1.1 --port 9006'
        args.update({'cli_parameters': cli_parameters})
        input_args = MagicMock(**args)

        with patch('requests.put', http_method), \
                patch('conductr_cli.bundle_scale.wait_for_scale', wait_for_scale_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_run.run(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       headers={'Host': '127.0.0.1'})
        wait_for_scale_mock.assert_called_with(self.bundle_id, self.scale, wait_for_is_active=True, args=input_args)

        self.assertEqual(
            self.default_output(params=cli_parameters),
            self.output(stdout))

    def base_test_success_ip(self):
        args = {}
        args.update(self.default_args)
        args.pop('host')
        args.update({'ip': '127.0.0.1'})

        http_method = self.respond_with(200, self.default_response)
        wait_for_scale_mock = MagicMock()
        stdout = MagicMock()

        input_args = MagicMock(**args)

        with patch('requests.put', http_method), \
                patch('conductr_cli.bundle_scale.wait_for_scale', wait_for_scale_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_run.run(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       headers={'Host': '127.0.0.1'})
        wait_for_scale_mock.assert_called_with(self.bundle_id, self.scale, wait_for_is_active=True, args=input_args)

        self.assertEqual(self.default_output(), self.output(stdout))

    def base_test_success_no_wait(self):
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()

        args = self.default_args.copy()
        args.update({'no_wait': True})
        input_args = MagicMock(**args)

        with patch('requests.put', http_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_run.run(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       headers={'Host': '127.0.0.1'})

        self.assertEqual(self.default_output(), self.output(stdout))

    def base_test_failure(self):
        http_method = self.respond_with(404)
        stderr = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.put', http_method):
            logging_setup.configure_logging(input_args, err_output=stderr)
            result = conduct_run.run(input_args)
            self.assertFalse(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       headers={'Host': '127.0.0.1'})

        self.assertEqual(
            as_error(strip_margin("""|Error: 404 Not Found
                                     |""")),
            self.output(stderr))

    def base_test_failure_invalid_address(self):
        http_method = self.raise_connection_error('test reason', self.default_url)
        stderr = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.put', http_method):
            logging_setup.configure_logging(input_args, err_output=stderr)
            result = conduct_run.run(input_args)
            self.assertFalse(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       headers={'Host': '127.0.0.1'})

        self.assertEqual(
            self.default_connection_error.format(self.default_url),
            self.output(stderr))

    def base_test_failure_scale_timeout(self):
        http_method = self.respond_with(200, self.default_response)
        wait_for_scale_mock = MagicMock(side_effect=WaitTimeoutError('test wait timeout error'))
        stderr = MagicMock()

        input_args = MagicMock(**self.default_args)

        with patch('requests.put', http_method), \
                patch('conductr_cli.bundle_scale.wait_for_scale', wait_for_scale_mock):
            logging_setup.configure_logging(input_args, err_output=stderr)
            result = conduct_run.run(input_args)
            self.assertFalse(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       headers={'Host': '127.0.0.1'})
        wait_for_scale_mock.assert_called_with(self.bundle_id, self.scale, wait_for_is_active=True, args=input_args)

        self.assertEqual(
            as_error(strip_margin("""|Error: Timed out: test wait timeout error
                                     |""")),
            self.output(stderr))
