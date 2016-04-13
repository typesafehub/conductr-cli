from conductr_cli.test.cli_test_case import create_temp_bundle, strip_margin, as_error, \
    create_temp_bundle_with_contents
from conductr_cli.test.conduct_load_test_base import ConductLoadTestBase
from conductr_cli import conduct_load, logging_setup
from conductr_cli.conduct_load import LOAD_HTTP_TIMEOUT

try:
    from unittest.mock import call, patch, MagicMock, Mock  # 3.3 and beyond
except ImportError:
    from mock import call, patch, MagicMock, Mock


class TestConductLoadCommand(ConductLoadTestBase):
    def __init__(self, method_name):
        super().__init__(method_name)

        self.bundle_id = '45e0c477d3e5ea92aa8d85c0d8f3e25c'
        self.nr_of_cpus = 1.0
        self.memory = 200
        self.disk_space = 100
        self.roles = ['web-server']
        self.bundle_name = 'bundle.zip'
        self.system = 'bundle'
        self.system_version = '2.3'
        self.compatibility_version = '2.0'
        self.custom_settings = Mock()
        self.bundle_resolve_cache_dir = 'bundle-resolve-cache-dir'

        self.tmpdir, self.bundle_file = create_temp_bundle(
            strip_margin("""|nrOfCpus               = {}
                            |memory                 = {}
                            |diskSpace              = {}
                            |roles                  = [{}]
                            |name                   = {}
                            |system                 = {}
                            |systemVersion          = {}
                            |compatibilityVersion   = {}
                            |""").format(self.nr_of_cpus,
                                         self.memory,
                                         self.disk_space,
                                         ', '.join(self.roles),
                                         self.bundle_name,
                                         self.system,
                                         self.system_version,
                                         self.compatibility_version))

        self.default_args = {
            'ip': '127.0.0.1',
            'port': 9005,
            'api_version': '2',
            'verbose': False,
            'quiet': False,
            'no_wait': False,
            'long_ids': False,
            'cli_parameters': '',
            'custom_settings': self.custom_settings,
            'resolve_cache_dir': self.bundle_resolve_cache_dir,
            'bundle': self.bundle_file,
            'configuration': None
        }

        self.default_url = 'http://127.0.0.1:9005/v2/bundles'

        self.default_files = [
            ('bundleConf', ('bundle.conf', 'mock bundle.conf')),
            ('bundle', (self.bundle_name, 1))
        ]

    def test_success(self):
        zip_entry_mock = MagicMock(return_value='mock bundle.conf')
        with patch('conductr_cli.bundle_utils.zip_entry', zip_entry_mock):
            self.base_test_success()
        zip_entry_mock.assert_called_with('bundle.conf', self.bundle_file)

    def test_success_verbose(self):
        zip_entry_mock = MagicMock(return_value='mock bundle.conf')
        with patch('conductr_cli.bundle_utils.zip_entry', zip_entry_mock):
            self.base_test_success_verbose()
        zip_entry_mock.assert_called_with('bundle.conf', self.bundle_file)

    def test_success_quiet(self):
        zip_entry_mock = MagicMock(return_value='mock bundle.conf')
        with patch('conductr_cli.bundle_utils.zip_entry', zip_entry_mock):
            self.base_test_success_quiet()
        zip_entry_mock.assert_called_with('bundle.conf', self.bundle_file)

    def test_success_long_ids(self):
        zip_entry_mock = MagicMock(return_value='mock bundle.conf')
        with patch('conductr_cli.bundle_utils.zip_entry', zip_entry_mock):
            self.base_test_success_long_ids()
        zip_entry_mock.assert_called_with('bundle.conf', self.bundle_file)

    def test_success_custom_ip_port(self):
        zip_entry_mock = MagicMock(return_value='mock bundle.conf')
        with patch('conductr_cli.bundle_utils.zip_entry', zip_entry_mock):
            self.base_test_success_custom_ip_port()
        zip_entry_mock.assert_called_with('bundle.conf', self.bundle_file)

    def test_success_with_configuration(self):
        tmpdir, config_file = create_temp_bundle_with_contents({
            'bundle.conf': '{name="overlaid-name"}',
            'config.sh': 'echo configuring'
        })

        request_headers_mock = MagicMock(return_value=self.mock_headers)
        resolve_bundle_mock = MagicMock(side_effect=[(self.bundle_name, self.bundle_file), ('config.zip', config_file)])
        zip_entry_mock = MagicMock(side_effect=['mock bundle.conf', 'mock bundle.conf overlay'])
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        open_mock = MagicMock(return_value=1)
        wait_for_installation_mock = MagicMock()

        args = self.default_args.copy()
        args.update({'configuration': config_file})
        input_args = MagicMock(**args)

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.bundle_utils.zip_entry', zip_entry_mock), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('requests.post', http_method), \
                patch('builtins.open', open_mock), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        self.assertEqual(
            resolve_bundle_mock.call_args_list,
            [
                call(self.custom_settings, self.bundle_resolve_cache_dir, self.bundle_file),
                call(self.custom_settings, self.bundle_resolve_cache_dir, config_file)
            ]
        )

        self.assertEqual(
            open_mock.call_args_list,
            [call(self.bundle_file, 'rb'), call(config_file, 'rb')]
        )

        request_headers_mock.assert_called_with(input_args)
        expected_files = [
            ('bundleConf', ('bundle.conf', 'mock bundle.conf')),
            ('bundleConfOverlay', ('bundle.conf', 'mock bundle.conf overlay')),
            ('bundle', ('bundle.zip', 1)),
            ('configuration', ('config.zip', 1))
        ]
        http_method.assert_called_with(self.default_url, files=expected_files, timeout=LOAD_HTTP_TIMEOUT,
                                       headers=self.mock_headers)

        wait_for_installation_mock.assert_called_with(self.bundle_id, input_args)

        self.assertEqual(self.default_output(downloading_configuration='Retrieving configuration...\n'),
                         self.output(stdout))

        self.assertEqual(
            zip_entry_mock.call_args_list,
            [call('bundle.conf', self.bundle_file), call('bundle.conf', config_file)]
        )

    def test_success_with_configuration_no_bundle_conf(self):
        tmpdir, config_file = create_temp_bundle_with_contents({
            'config.sh': 'echo configuring'
        })

        request_headers_mock = MagicMock(return_value=self.mock_headers)
        resolve_bundle_mock = MagicMock(side_effect=[(self.bundle_name, self.bundle_file), ('config.zip', config_file)])
        zip_entry_mock = MagicMock(side_effect=['mock bundle.conf', None])
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        open_mock = MagicMock(return_value=1)
        wait_for_installation_mock = MagicMock()

        args = self.default_args.copy()
        args.update({'configuration': config_file})
        input_args = MagicMock(**args)

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.bundle_utils.zip_entry', zip_entry_mock), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('requests.post', http_method), \
                patch('builtins.open', open_mock), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        self.assertEqual(
            resolve_bundle_mock.call_args_list,
            [
                call(self.custom_settings, self.bundle_resolve_cache_dir, self.bundle_file),
                call(self.custom_settings, self.bundle_resolve_cache_dir, config_file)
            ]
        )

        self.assertEqual(
            open_mock.call_args_list,
            [call(self.bundle_file, 'rb'), call(config_file, 'rb')]
        )

        request_headers_mock.assert_called_with(input_args)
        expected_files = [
            ('bundleConf', ('bundle.conf', 'mock bundle.conf')),
            ('bundle', ('bundle.zip', 1)),
            ('configuration', ('config.zip', 1))
        ]
        http_method.assert_called_with(self.default_url, files=expected_files, timeout=LOAD_HTTP_TIMEOUT,
                                       headers=self.mock_headers)

        wait_for_installation_mock.assert_called_with(self.bundle_id, input_args)

        self.assertEqual(self.default_output(downloading_configuration='Retrieving configuration...\n'),
                         self.output(stdout))

        self.assertEqual(
            zip_entry_mock.call_args_list,
            [call('bundle.conf', self.bundle_file), call('bundle.conf', config_file)]
        )

    def test_success_no_wait(self):
        zip_entry_mock = MagicMock(return_value='mock bundle.conf')
        with patch('conductr_cli.bundle_utils.zip_entry', zip_entry_mock):
            self.base_test_success_no_wait()
        zip_entry_mock.assert_called_with('bundle.conf', self.bundle_file)

    def test_failure(self):
        zip_entry_mock = MagicMock(return_value='mock bundle.conf')
        with patch('conductr_cli.bundle_utils.zip_entry', zip_entry_mock):
            self.base_test_failure()
        zip_entry_mock.assert_called_with('bundle.conf', self.bundle_file)

    def test_failure_invalid_address(self):
        zip_entry_mock = MagicMock(return_value='mock bundle.conf')
        with patch('conductr_cli.bundle_utils.zip_entry', zip_entry_mock):
            self.base_test_failure_invalid_address()
        zip_entry_mock.assert_called_with('bundle.conf', self.bundle_file)

    def test_failure_no_response(self):
        zip_entry_mock = MagicMock(return_value='mock bundle.conf')
        with patch('conductr_cli.bundle_utils.zip_entry', zip_entry_mock):
            self.base_test_failure_no_response()
        zip_entry_mock.assert_called_with('bundle.conf', self.bundle_file)

    def test_failure_no_bundle(self):
        self.base_test_failure_no_bundle()

    def test_failure_bad_zip(self):
        self.base_test_failure_bad_zip()

    def test_failure_no_file_http_error(self):
        self.base_test_failure_no_file_http_error()

    def test_failure_no_file_url_error(self):
        self.base_test_failure_no_file_url_error()

    def test_failure_no_bundle_conf(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, self.bundle_file))
        zip_entry_mock = MagicMock(return_value=None)
        stderr = MagicMock()

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.bundle_utils.zip_entry', zip_entry_mock):
            args = self.default_args.copy()
            logging_setup.configure_logging(MagicMock(**args), err_output=stderr)
            result = conduct_load.load(MagicMock(**args))
            self.assertFalse(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir, self.bundle_file)

        self.assertEqual(
            as_error(strip_margin("""|Error: Problem with the bundle: Unable to find bundle.conf within the bundle file
                                     |""")),
            self.output(stderr))
        zip_entry_mock.assert_called_with('bundle.conf', self.bundle_file)

    def test_failure_install_timeout(self):
        zip_entry_mock = MagicMock(return_value='mock bundle.conf')
        with patch('conductr_cli.bundle_utils.zip_entry', zip_entry_mock):
            self.base_test_failure_install_timeout()
        zip_entry_mock.assert_called_with('bundle.conf', self.bundle_file)
