from conductr_cli.test.cli_test_case import CliTestCase, strip_margin, as_error
from conductr_cli import conduct_load
from conductr_cli.conduct_load import LOAD_HTTP_TIMEOUT
from conductr_cli.exceptions import BundleResolutionError


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

        self.bundle_name = None
        self.bundle_file = None
        self.default_args = {}
        self.default_files = None
        self.default_url = None
        self.disk_space = None
        self.memory = None
        self.nr_of_cpus = None
        self.roles = []
        self.bundle_resolve_cache_dir = None

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
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, self.bundle_file))
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        open_mock = MagicMock(return_value=1)

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('requests.post', http_method), \
                patch('sys.stdout', stdout), \
                patch('builtins.open', open_mock):
            conduct_load.load(MagicMock(**self.default_args))

        open_mock.assert_called_with(self.bundle_file, 'rb')
        resolve_bundle_mock.assert_called_with(self.bundle_resolve_cache_dir, self.bundle_file)
        http_method.assert_called_with(self.default_url, files=self.default_files, timeout=LOAD_HTTP_TIMEOUT)

        self.assertEqual(self.default_output(), self.output(stdout))

    def base_test_success_verbose(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, self.bundle_file))
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        open_mock = MagicMock(return_value=1)

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('requests.post', http_method), \
                patch('sys.stdout', stdout), \
                patch('builtins.open', open_mock):
            args = self.default_args.copy()
            args.update({'verbose': True})
            conduct_load.load(MagicMock(**args))

        open_mock.assert_called_with(self.bundle_file, 'rb')
        resolve_bundle_mock.assert_called_with(self.bundle_resolve_cache_dir, self.bundle_file)
        http_method.assert_called_with(self.default_url, files=self.default_files, timeout=LOAD_HTTP_TIMEOUT)

        self.assertEqual(self.default_output(verbose=self.default_response), self.output(stdout))

    def base_test_success_long_ids(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, self.bundle_file))
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        open_mock = MagicMock(return_value=1)

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('requests.post', http_method), \
                patch('sys.stdout', stdout), \
                patch('builtins.open', open_mock):
            args = self.default_args.copy()
            args.update({'long_ids': True})
            conduct_load.load(MagicMock(**args))

        open_mock.assert_called_with(self.bundle_file, 'rb')
        resolve_bundle_mock.assert_called_with(self.bundle_resolve_cache_dir, self.bundle_file)
        http_method.assert_called_with(self.default_url, files=self.default_files, timeout=LOAD_HTTP_TIMEOUT)

        self.assertEqual(self.default_output(bundle_id='45e0c477d3e5ea92aa8d85c0d8f3e25c'), self.output(stdout))

    def base_test_success_custom_ip_port(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, self.bundle_file))
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        open_mock = MagicMock(return_value=1)

        cli_parameters = ' --ip 127.0.1.1 --port 9006'
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('requests.post', http_method), \
                patch('sys.stdout', stdout), \
                patch('builtins.open', open_mock):
            args = self.default_args.copy()
            args.update({'cli_parameters': cli_parameters})
            conduct_load.load(MagicMock(**args))

        open_mock.assert_called_with(self.bundle_file, 'rb')
        resolve_bundle_mock.assert_called_with(self.bundle_resolve_cache_dir, self.bundle_file)
        http_method.assert_called_with(self.default_url, files=self.default_files, timeout=LOAD_HTTP_TIMEOUT)

        self.assertEqual(
            self.default_output(params=cli_parameters),
            self.output(stdout))

    def base_test_failure(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, self.bundle_file))
        http_method = self.respond_with(404)
        stderr = MagicMock()
        open_mock = MagicMock(return_value=1)

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('requests.post', http_method), \
                patch('sys.stderr', stderr), \
                patch('builtins.open', open_mock):
            conduct_load.load(MagicMock(**self.default_args))

        open_mock.assert_called_with(self.bundle_file, 'rb')
        resolve_bundle_mock.assert_called_with(self.bundle_resolve_cache_dir, self.bundle_file)
        http_method.assert_called_with(self.default_url, files=self.default_files, timeout=LOAD_HTTP_TIMEOUT)

        self.assertEqual(
            as_error(strip_margin("""|Error: 404 Not Found
                                     |""")),
            self.output(stderr))

    def base_test_failure_invalid_address(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, self.bundle_file))
        http_method = self.raise_connection_error('test reason', self.default_url)
        stderr = MagicMock()
        open_mock = MagicMock(return_value=1)

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('requests.post', http_method), \
                patch('sys.stderr', stderr), \
                patch('builtins.open', open_mock):
            conduct_load.load(MagicMock(**self.default_args))

        open_mock.assert_called_with(self.bundle_file, 'rb')
        resolve_bundle_mock.assert_called_with(self.bundle_resolve_cache_dir, self.bundle_file)
        http_method.assert_called_with(self.default_url, files=self.default_files, timeout=LOAD_HTTP_TIMEOUT)

        self.assertEqual(
            self.default_connection_error.format(self.default_url),
            self.output(stderr))

    def base_test_failure_no_bundle(self):
        resolve_bundle_mock = MagicMock(side_effect=BundleResolutionError('some message'))
        stderr = MagicMock()

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), patch('sys.stderr', stderr):
            args = self.default_args.copy()
            args.update({'bundle': 'no_such.bundle'})
            conduct_load.load(MagicMock(**args))

        resolve_bundle_mock.assert_called_with(self.bundle_resolve_cache_dir, 'no_such.bundle')

        self.assertEqual(
            as_error(strip_margin("""|Error: Bundle not found: some message
                                     |""")),
            self.output(stderr))

    def base_test_failure_no_configuration(self):
        resolve_bundle_mock = MagicMock(side_effect=[(self.bundle_name, self.bundle_file),
                                                     BundleResolutionError('some message')])

        stderr = MagicMock()

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), patch('sys.stderr', stderr):
            args = self.default_args.copy()
            args.update({'configuration': 'no_such.conf'})
            conduct_load.load(MagicMock(**args))

        self.assertEqual(
            resolve_bundle_mock.call_args_list,
            [
                call(self.bundle_resolve_cache_dir, self.bundle_file),
                call(self.bundle_resolve_cache_dir, 'no_such.conf')
            ]
        )

        self.assertEqual(
            as_error(strip_margin("""|Error: Bundle not found: some message
                                     |""")),
            self.output(stderr))
