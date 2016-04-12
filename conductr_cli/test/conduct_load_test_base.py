from conductr_cli.test.cli_test_case import CliTestCase, strip_margin, as_error
from conductr_cli import conduct_load, logging_setup
from conductr_cli.conduct_load import LOAD_HTTP_TIMEOUT
from conductr_cli.exceptions import BundleResolutionError, WaitTimeoutError
from zipfile import BadZipFile
from urllib.error import HTTPError, URLError


try:
    from unittest.mock import call, patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import call, patch, MagicMock


class ConductLoadTestBase(CliTestCase):
    output_template = """|Retrieving bundle...
                         |{downloading_configuration}Loading bundle to ConductR...
                         |{verbose}Bundle loaded.
                         |Start bundle with: conduct run{params} {bundle_id}
                         |Unload bundle with: conduct unload{params} {bundle_id}
                         |Print ConductR info with: conduct info{params}
                         |"""

    def __init__(self, method_name):
        super().__init__(method_name)

        self.bundle_id = None
        self.bundle_name = None
        self.bundle_file = None
        self.default_args = {}
        self.default_files = None
        self.default_url = None
        self.disk_space = None
        self.memory = None
        self.nr_of_cpus = None
        self.roles = []
        self.custom_settings = None
        self.bundle_resolve_cache_dir = None
        self.mock_headers = {'pretend': 'header'}

    @property
    def default_response(self):
        return strip_margin("""|{
                               |  "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c"
                               |}
                               |""")

    def default_output(self, params='', bundle_id='45e0c47', downloading_configuration='', verbose=''):
        return strip_margin(self.output_template.format(**{
            'params': params,
            'bundle_id': bundle_id,
            'downloading_configuration': downloading_configuration,
            'verbose': verbose}))

    def base_test_success(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, self.bundle_file))
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        open_mock = MagicMock(return_value=1)
        wait_for_installation_mock = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('requests.post', http_method), \
                patch('builtins.open', open_mock), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        open_mock.assert_called_with(self.bundle_file, 'rb')
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir, self.bundle_file)
        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, files=self.default_files, timeout=LOAD_HTTP_TIMEOUT,
                                       headers=self.mock_headers)
        wait_for_installation_mock.assert_called_with(self.bundle_id, input_args)

        self.assertEqual(self.default_output(), self.output(stdout))

    def base_test_success_verbose(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, self.bundle_file))
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        open_mock = MagicMock(return_value=1)
        wait_for_installation_mock = MagicMock()

        args = self.default_args.copy()
        args.update({'verbose': True})
        input_args = MagicMock(**args)

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('requests.post', http_method), \
                patch('builtins.open', open_mock), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        open_mock.assert_called_with(self.bundle_file, 'rb')
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir, self.bundle_file)
        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, files=self.default_files, timeout=LOAD_HTTP_TIMEOUT,
                                       headers=self.mock_headers)
        wait_for_installation_mock.assert_called_with(self.bundle_id, input_args)

        self.assertEqual(self.default_output(verbose=self.default_response), self.output(stdout))

    def base_test_success_quiet(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, self.bundle_file))
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        open_mock = MagicMock(return_value=1)
        wait_for_installation_mock = MagicMock()

        args = self.default_args.copy()
        args.update({'quiet': True})
        input_args = MagicMock(**args)

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('requests.post', http_method), \
                patch('builtins.open', open_mock), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        open_mock.assert_called_with(self.bundle_file, 'rb')
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir, self.bundle_file)
        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, files=self.default_files, timeout=LOAD_HTTP_TIMEOUT,
                                       headers=self.mock_headers)
        wait_for_installation_mock.assert_called_with(self.bundle_id, input_args)

        self.assertEqual('45e0c477d3e5ea92aa8d85c0d8f3e25c\n', self.output(stdout))

    def base_test_success_long_ids(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, self.bundle_file))
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        open_mock = MagicMock(return_value=1)
        wait_for_installation_mock = MagicMock()

        args = self.default_args.copy()
        args.update({'long_ids': True})
        input_args = MagicMock(**args)

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('requests.post', http_method), \
                patch('builtins.open', open_mock), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        open_mock.assert_called_with(self.bundle_file, 'rb')
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir, self.bundle_file)
        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, files=self.default_files, timeout=LOAD_HTTP_TIMEOUT,
                                       headers=self.mock_headers)
        wait_for_installation_mock.assert_called_with(self.bundle_id, input_args)

        self.assertEqual(self.default_output(bundle_id='45e0c477d3e5ea92aa8d85c0d8f3e25c'), self.output(stdout))

    def base_test_success_custom_ip_port(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, self.bundle_file))
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        open_mock = MagicMock(return_value=1)
        wait_for_installation_mock = MagicMock()

        cli_parameters = ' --ip 127.0.1.1 --port 9006'
        args = self.default_args.copy()
        args.update({'cli_parameters': cli_parameters})
        input_args = MagicMock(**args)

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('requests.post', http_method), \
                patch('builtins.open', open_mock), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        open_mock.assert_called_with(self.bundle_file, 'rb')
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir, self.bundle_file)
        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, files=self.default_files, timeout=LOAD_HTTP_TIMEOUT,
                                       headers=self.mock_headers)
        wait_for_installation_mock.assert_called_with(self.bundle_id, input_args)

        self.assertEqual(
            self.default_output(params=cli_parameters),
            self.output(stdout))

    def base_test_success_no_wait(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, self.bundle_file))
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        open_mock = MagicMock(return_value=1)

        args = self.default_args.copy()
        args.update({'no_wait': True})
        input_args = MagicMock(**args)

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('requests.post', http_method), \
                patch('builtins.open', open_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        open_mock.assert_called_with(self.bundle_file, 'rb')
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir, self.bundle_file)
        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, files=self.default_files, timeout=LOAD_HTTP_TIMEOUT,
                                       headers=self.mock_headers)

        self.assertEqual(self.default_output(), self.output(stdout))

    def base_test_failure(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, self.bundle_file))
        http_method = self.respond_with(404)
        stdout = MagicMock()
        stderr = MagicMock()
        open_mock = MagicMock(return_value=1)

        input_args = MagicMock(**self.default_args)
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('requests.post', http_method), \
                patch('builtins.open', open_mock):
            logging_setup.configure_logging(input_args, stdout, stderr)
            result = conduct_load.load(input_args)
            self.assertFalse(result)

        open_mock.assert_called_with(self.bundle_file, 'rb')
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir, self.bundle_file)
        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, files=self.default_files, timeout=LOAD_HTTP_TIMEOUT,
                                       headers=self.mock_headers)

        self.assertEqual(
            as_error(strip_margin("""|Error: 404 Not Found
                                     |""")),
            self.output(stderr))

    def base_test_failure_invalid_address(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, self.bundle_file))
        http_method = self.raise_connection_error('test reason', self.default_url)
        stdout = MagicMock()
        stderr = MagicMock()
        open_mock = MagicMock(return_value=1)

        input_args = MagicMock(**self.default_args)
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('requests.post', http_method), \
                patch('builtins.open', open_mock):
            logging_setup.configure_logging(input_args, stdout, stderr)
            result = conduct_load.load(input_args)
            self.assertFalse(result)

        open_mock.assert_called_with(self.bundle_file, 'rb')
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir, self.bundle_file)
        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, files=self.default_files, timeout=LOAD_HTTP_TIMEOUT,
                                       headers=self.mock_headers)

        self.assertEqual(
            self.default_connection_error.format(self.default_url),
            self.output(stderr))

    def base_test_failure_no_response(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, self.bundle_file))
        http_method = self.raise_read_timeout_error('test reason', self.default_url)
        stdout = MagicMock()
        stderr = MagicMock()
        open_mock = MagicMock(return_value=1)

        input_args = MagicMock(**self.default_args)
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('requests.post', http_method), \
                patch('builtins.open', open_mock):
            logging_setup.configure_logging(input_args, stdout, stderr)
            result = conduct_load.load(input_args)
            self.assertFalse(result)

        open_mock.assert_called_with(self.bundle_file, 'rb')
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir, self.bundle_file)
        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, files=self.default_files, timeout=LOAD_HTTP_TIMEOUT,
                                       headers=self.mock_headers)

        self.assertEqual(
            as_error(
                strip_margin("""|Error: Timed out waiting for response from the server: test reason
                                |Error: One possible issue may be that there are not enough resources or machines with the roles that your bundle requires
                                |""")),
            self.output(stderr))

    def base_test_failure_no_bundle(self):
        resolve_bundle_mock = MagicMock(side_effect=BundleResolutionError('some message'))
        stdout = MagicMock()
        stderr = MagicMock()

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock):
            args = self.default_args.copy()
            args.update({'bundle': 'no_such.bundle'})
            logging_setup.configure_logging(MagicMock(**args), stdout, stderr)
            result = conduct_load.load(MagicMock(**args))
            self.assertFalse(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir, 'no_such.bundle')

        self.assertEqual(
            as_error(strip_margin("""|Error: Bundle not found: some message
                                     |""")),
            self.output(stderr))

    def base_test_failure_no_configuration(self):
        resolve_bundle_mock = MagicMock(side_effect=[(self.bundle_name, self.bundle_file),
                                                     BundleResolutionError('some message')])
        stdout = MagicMock()
        stderr = MagicMock()

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock):
            args = self.default_args.copy()
            args.update({'configuration': 'no_such.conf'})
            logging_setup.configure_logging(MagicMock(**args), stdout, stderr)
            result = conduct_load.load(MagicMock(**args))
            self.assertFalse(result)

        self.assertEqual(
            resolve_bundle_mock.call_args_list,
            [
                call(self.custom_settings, self.bundle_resolve_cache_dir, self.bundle_file),
                call(self.custom_settings, self.bundle_resolve_cache_dir, 'no_such.conf')
            ]
        )

        self.assertEqual(
            as_error(strip_margin("""|Error: Bundle not found: some message
                                     |""")),
            self.output(stderr))

    def base_test_failure_bad_zip(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, self.bundle_file))
        stderr = MagicMock()
        open_mock = MagicMock(side_effect=BadZipFile('test bad zip error'))

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('builtins.open', open_mock):
            logging_setup.configure_logging(MagicMock(**self.default_args), err_output=stderr)
            result = conduct_load.load(MagicMock(**self.default_args))
            self.assertFalse(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir, self.bundle_file)
        open_mock.assert_called_with(self.bundle_file, 'rb')

        self.assertEqual(
            as_error(strip_margin("""|Error: Problem with the bundle: test bad zip error
                                     |""")),
            self.output(stderr))

    def base_test_failure_no_file_http_error(self):
        add_info_mock = MagicMock()
        resolve_bundle_mock = MagicMock(side_effect=HTTPError('url', 'code', 'message', 'headers', add_info_mock))
        stderr = MagicMock()

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock):
            logging_setup.configure_logging(MagicMock(**self.default_args), err_output=stderr)
            result = conduct_load.load(MagicMock(**self.default_args))
            self.assertFalse(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir, self.bundle_file)

        self.assertEqual(
            as_error(strip_margin("""|Error: Resource not found: url
                                     |""")),
            self.output(stderr))

    def base_test_failure_no_file_url_error(self):
        resolve_bundle_mock = MagicMock(side_effect=URLError('reason', None))
        stderr = MagicMock()

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock):
            logging_setup.configure_logging(MagicMock(**self.default_args), err_output=stderr)
            result = conduct_load.load(MagicMock(**self.default_args))
            self.assertFalse(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir, self.bundle_file)

        self.assertEqual(
            as_error(strip_margin("""|Error: File not found: reason
                                     |""")),
            self.output(stderr))

    def base_test_failure_install_timeout(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, self.bundle_file))
        http_method = self.respond_with(200, self.default_response)
        stderr = MagicMock()
        open_mock = MagicMock(return_value=1)
        wait_for_installation_mock = MagicMock(side_effect=WaitTimeoutError('test timeout'))

        input_args = MagicMock(**self.default_args)
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('requests.post', http_method), \
                patch('builtins.open', open_mock), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock):
            logging_setup.configure_logging(input_args, err_output=stderr)
            result = conduct_load.load(input_args)
            self.assertFalse(result)

        open_mock.assert_called_with(self.bundle_file, 'rb')
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir, self.bundle_file)
        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, files=self.default_files, timeout=LOAD_HTTP_TIMEOUT,
                                       headers=self.mock_headers)
        wait_for_installation_mock.assert_called_with(self.bundle_id, input_args)

        self.assertEqual(
            as_error(strip_margin("""|Error: Timed out: test timeout
                                     |""")),
            self.output(stderr))
