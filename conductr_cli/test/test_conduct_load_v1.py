from conductr_cli.test.conduct_load_test_base import ConductLoadTestBase
from conductr_cli.test.cli_test_case import create_temp_bundle, strip_margin, as_error, \
    create_temp_bundle_with_contents
from conductr_cli import conduct_load, logging_setup
from conductr_cli.conduct_load import LOAD_HTTP_TIMEOUT
import shutil

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
        self.custom_settings = Mock()
        self.bundle_resolve_cache_dir = 'bundle-resolve-cache-dir'

        self.tmpdir, self.bundle_file = create_temp_bundle(
            strip_margin("""|nrOfCpus   = {},
                            |memory     = {},
                            |diskSpace  = {},
                            |roles      = [{}],
                            |name       = {},
                            |system     = {},
                            |""").format(self.nr_of_cpus,
                                         self.memory,
                                         self.disk_space,
                                         ', '.join(self.roles),
                                         self.bundle_name,
                                         self.system))
        self.default_args = {
            'ip': '127.0.0.1',
            'port': 9005,
            'api_version': '1',
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

        self.default_url = 'http://127.0.0.1:9005/bundles'

        self.default_files = [
            ('nrOfCpus', str(self.nr_of_cpus)),
            ('memory', str(self.memory)),
            ('diskSpace', str(self.disk_space)),
            ('roles', ' '.join(self.roles)),
            ('bundleName', self.bundle_name),
            ('system', self.system),
            ('bundle', (self.bundle_name, 1))
        ]

    def test_success(self):
        self.base_test_success()

    def test_success_verbose(self):
        self.base_test_success_verbose()

    def test_success_quiet(self):
        self.base_test_success_quiet()

    def test_success_long_ids(self):
        self.base_test_success_long_ids()

    def test_success_custom_ip_port(self):
        self.base_test_success_custom_ip_port()

    def test_success_with_configuration(self):
        tmpdir, config_file = create_temp_bundle_with_contents({
            'bundle.conf': '{name="overlaid-name"}',
            'config.sh': 'echo configuring'
        })

        request_headers_mock = MagicMock(return_value=self.mock_headers)
        resolve_bundle_mock = MagicMock(side_effect=[(self.bundle_name, self.bundle_file), ('config.zip', config_file)])
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        open_mock = MagicMock(return_value=1)
        wait_for_installation_mock = MagicMock()

        args = self.default_args.copy()
        args.update({'configuration': config_file})
        input_args = MagicMock(**args)

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('requests.post', http_method), \
                patch('builtins.open', open_mock), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        self.assertEqual(
            open_mock.call_args_list,
            [call(self.bundle_file, 'rb'), call(config_file, 'rb')]
        )

        self.assertEqual(
            resolve_bundle_mock.call_args_list,
            [
                call(self.custom_settings, self.bundle_resolve_cache_dir, self.bundle_file),
                call(self.custom_settings, self.bundle_resolve_cache_dir, config_file)
            ]
        )
        request_headers_mock.assert_called_with(input_args)
        expected_files = self.default_files + [('configuration', ('config.zip', 1))]
        expected_files[4] = ('bundleName', 'overlaid-name')
        http_method.assert_called_with(self.default_url, files=expected_files, timeout=LOAD_HTTP_TIMEOUT,
                                       headers=self.mock_headers)
        wait_for_installation_mock.assert_called_with(self.bundle_id, input_args)

        self.assertEqual(self.default_output(downloading_configuration='Retrieving configuration...\n'),
                         self.output(stdout))

    def test_success_no_wait(self):
        self.base_test_success_no_wait()

    def test_failure(self):
        self.base_test_failure()

    def test_failure_invalid_address(self):
        self.base_test_failure_invalid_address()

    def test_failure_no_response(self):
        self.base_test_failure_no_response()

    def test_failure_no_bundle(self):
        self.base_test_failure_no_bundle()

    def test_failure_no_configuration(self):
        self.base_test_failure_no_configuration()

    def test_failure_no_nr_of_cpus(self):
        stderr = MagicMock()

        tmpdir, bundle_file = create_temp_bundle(
            strip_margin("""|memory     = {}
                            |diskSpace  = {}
                            |roles      = [{}]
                            |""").format(self.memory, self.disk_space, ', '.join(self.roles)))

        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, bundle_file))
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock):
            args = self.default_args.copy()
            args.update({'bundle': bundle_file})
            logging_setup.configure_logging(MagicMock(**args), err_output=stderr)
            result = conduct_load.load(MagicMock(**args))
            self.assertFalse(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir, bundle_file)

        self.assertEqual(
            as_error(strip_margin("""|Error: Unable to parse bundle.conf.
                                     |Error: No configuration setting found for key nrOfCpus.
                                     |""")),
            self.output(stderr))

        shutil.rmtree(tmpdir)

    def test_failure_no_memory(self):
        stderr = MagicMock()

        tmpdir, bundle_file = create_temp_bundle(
            strip_margin("""|nrOfCpus   = {}
                            |diskSpace  = {}
                            |roles      = [{}]
                            |""").format(self.nr_of_cpus, self.disk_space, ', '.join(self.roles)))

        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, bundle_file))
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock):
            args = self.default_args.copy()
            args.update({'bundle': bundle_file})
            logging_setup.configure_logging(MagicMock(**args), err_output=stderr)
            result = conduct_load.load(MagicMock(**args))
            self.assertFalse(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir, bundle_file)

        self.assertEqual(
            as_error(strip_margin("""|Error: Unable to parse bundle.conf.
                                     |Error: No configuration setting found for key memory.
                                     |""")),
            self.output(stderr))

        shutil.rmtree(tmpdir)

    def test_failure_no_disk_space(self):
        stderr = MagicMock()

        tmpdir, bundle_file = create_temp_bundle(
            strip_margin("""|nrOfCpus   = {}
                            |memory     = {}
                            |roles      = [{}]
                            |""").format(self.nr_of_cpus, self.memory, ', '.join(self.roles)))

        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, bundle_file))
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock):
            args = self.default_args.copy()
            args.update({'bundle': bundle_file})
            logging_setup.configure_logging(MagicMock(**args), err_output=stderr)
            result = conduct_load.load(MagicMock(**args))
            self.assertFalse(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir, bundle_file)

        self.assertEqual(
            as_error(strip_margin("""|Error: Unable to parse bundle.conf.
                                     |Error: No configuration setting found for key diskSpace.
                                     |""")),
            self.output(stderr))

        shutil.rmtree(tmpdir)

    def test_failure_no_roles(self):
        stderr = MagicMock()

        tmpdir, bundle_file = create_temp_bundle(
            strip_margin("""|nrOfCpus   = {}
                            |memory     = {}
                            |diskSpace  = {}
                            |""").format(self.nr_of_cpus, self.memory, self.disk_space))

        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, bundle_file))
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock):
            args = self.default_args.copy()
            args.update({'bundle': bundle_file})
            logging_setup.configure_logging(MagicMock(**args), err_output=stderr)
            result = conduct_load.load(MagicMock(**args))
            self.assertFalse(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir, bundle_file)

        self.assertEqual(
            as_error(strip_margin("""|Error: Unable to parse bundle.conf.
                                     |Error: No configuration setting found for key roles.
                                     |""")),
            self.output(stderr))

        shutil.rmtree(tmpdir)

    def test_failure_roles_not_a_list(self):
        stderr = MagicMock()

        tmpdir, bundle_file = create_temp_bundle(
            strip_margin("""|nrOfCpus   = {}
                            |memory     = {}
                            |diskSpace  = {}
                            |roles      = {}
                            |""").format(self.nr_of_cpus, self.memory, self.disk_space, '-'.join(self.roles)))

        resolve_bundle_mock = MagicMock(return_value=(self.bundle_name, bundle_file))
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock):
            args = self.default_args.copy()
            args.update({'bundle': bundle_file})
            logging_setup.configure_logging(MagicMock(**args), err_output=stderr)
            result = conduct_load.load(MagicMock(**args))
            self.assertFalse(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir, bundle_file)

        self.assertEqual(
            as_error(strip_margin("""|Error: Unable to parse bundle.conf.
                                     |Error: roles has type 'str' rather than 'list'.
                                     |""")),
            self.output(stderr))

        shutil.rmtree(tmpdir)

    def test_failure_bad_zip(self):
        self.base_test_failure_bad_zip()

    def test_failure_no_file_http_error(self):
        self.base_test_failure_no_file_http_error()

    def test_failure_no_file_url_error(self):
        self.base_test_failure_no_file_url_error()

    def test_failure_install_timeout(self):
        self.base_test_failure_install_timeout()
