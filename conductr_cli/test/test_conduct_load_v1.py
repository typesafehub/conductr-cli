from conductr_cli.test.conduct_load_test_base import ConductLoadTestBase
from conductr_cli.test.cli_test_case import create_temp_bundle, strip_margin, as_error, \
    create_temp_bundle_with_contents
from conductr_cli import bundle_utils, conduct_load, logging_setup
from unittest.mock import call, patch, MagicMock, Mock
import shutil


class TestConductLoadCommand(ConductLoadTestBase):

    def __init__(self, method_name):
        super().__init__(method_name)

        self.bundle_id = '45e0c477d3e5ea92aa8d85c0d8f3e25c'
        self.nr_of_cpus = 1.0
        self.memory = 200
        self.disk_space = 100
        self.roles = ['web-server']
        self.bundle_file_name = 'bundle.zip'
        self.system = 'bundle'
        self.custom_settings = Mock()
        self.bundle_resolve_cache_dir = 'bundle-resolve-cache-dir'
        self.configuration_resolve_cache_dir = 'configuration-resolve-cache-dir'

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
                                         self.bundle_file_name,
                                         self.system))
        self.default_args = {
            'dcos_mode': False,
            'scheme': 'http',
            'host': '127.0.0.1',
            'port': 9005,
            'base_path': '/',
            'api_version': '1',
            'disable_instructions': False,
            'verbose': False,
            'quiet': False,
            'no_wait': False,
            'offline_mode': False,
            'long_ids': False,
            'command': 'conduct',
            'cli_parameters': '',
            'custom_settings': self.custom_settings,
            'bundle_resolve_cache_dir': self.bundle_resolve_cache_dir,
            'configuration_resolve_cache_dir': self.configuration_resolve_cache_dir,
            'bundle': self.bundle_file,
            'configuration': None,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        }

        self.default_url = 'http://127.0.0.1:9005/bundles'

        self.default_files = [
            ('nrOfCpus', str(self.nr_of_cpus)),
            ('memory', str(self.memory)),
            ('diskSpace', str(self.disk_space)),
            ('roles', ' '.join(self.roles)),
            ('bundleName', self.bundle_file_name),
            ('system', self.system),
            ('bundle', (self.bundle_file_name, 1))
        ]

    def test_success(self):
        self.base_test_success()

    def test_success_dcos_mode(self):
        self.default_url = 'http://127.0.0.1/bundles'
        self.base_test_success_dcos_mode()

    def test_success_verbose(self):
        self.base_test_success_verbose()

    def test_success_quiet(self):
        self.base_test_success_quiet()

    def test_success_long_ids(self):
        self.base_test_success_long_ids()

    def test_success_custom_ip_port(self):
        self.base_test_success_custom_ip_port()

    def test_success_custom_host_port(self):
        self.base_test_success_custom_host_port()

    def test_success_ip(self):
        self.base_test_success_ip()

    def test_success_with_configuration(self):
        tmpdir, config_file = create_temp_bundle_with_contents({
            'bundle.conf': '{name="overlaid-name"}',
            'config.sh': 'echo configuring'
        })

        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, self.bundle_file))
        resolve_bundle_configuration_mock = MagicMock(return_value=('config.zip', config_file))
        create_multipart_mock = MagicMock(return_value=self.multipart_mock)
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        open_mock = MagicMock(return_value=(1, None))
        bundle_open_mock = MagicMock(side_effect=lambda p1, p2, p3: (p1, 1))
        wait_for_installation_mock = MagicMock()

        args = self.default_args.copy()
        args.update({'configuration': config_file})
        input_args = MagicMock(**args)

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.resolver.resolve_bundle_configuration', resolve_bundle_configuration_mock), \
                patch('conductr_cli.conduct_load.create_multipart', create_multipart_mock), \
                patch('requests.post', http_method), \
                patch('conductr_cli.bundle_utils.digest_extract_and_open', open_mock), \
                patch('conductr_cli.conduct_load.open_bundle', bundle_open_mock), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        self.assertEqual(
            open_mock.call_args_list,
            [call(config_file)]
        )

        self.assertEqual(
            bundle_open_mock.call_args_list,
            [call(self.bundle_file_name, self.bundle_file, bundle_utils.conf(self.bundle_file))]
        )

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, self.offline_mode)
        resolve_bundle_configuration_mock.assert_called_with(self.custom_settings, self.configuration_resolve_cache_dir,
                                                             config_file, self.offline_mode)
        expected_files = self.default_files + [('configuration', ('config.zip', 1))]
        expected_files[4] = ('bundleName', 'overlaid-name')
        create_multipart_mock.assert_called_with(self.conduct_load_logger, expected_files)
        http_method.assert_called_with(self.default_url,
                                       data=self.multipart_mock,
                                       auth=self.conductr_auth,
                                       verify=self.server_verification_file,
                                       headers={'Content-Type': self.multipart_content_type, 'Host': '127.0.0.1'})
        wait_for_installation_mock.assert_called_with(self.bundle_id, input_args)

        self.assertEqual(self.default_output(downloading_configuration='Retrieving configuration..\n'),
                         self.output(stdout))

    def test_success_no_wait(self):
        self.base_test_success_no_wait()

    def test_success_offline_mode(self):
        self.base_test_success_offline_mode()

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

        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, bundle_file))
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock):
            args = self.default_args.copy()
            args.update({'bundle': bundle_file})
            logging_setup.configure_logging(MagicMock(**args), err_output=stderr)
            result = conduct_load.load(MagicMock(**args))
            self.assertFalse(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               bundle_file, self.offline_mode)

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

        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, bundle_file))
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock):
            args = self.default_args.copy()
            args.update({'bundle': bundle_file})
            logging_setup.configure_logging(MagicMock(**args), err_output=stderr)
            result = conduct_load.load(MagicMock(**args))
            self.assertFalse(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               bundle_file, self.offline_mode)

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

        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, bundle_file))
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock):
            args = self.default_args.copy()
            args.update({'bundle': bundle_file})
            logging_setup.configure_logging(MagicMock(**args), err_output=stderr)
            result = conduct_load.load(MagicMock(**args))
            self.assertFalse(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               bundle_file, self.offline_mode)

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

        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, bundle_file))
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock):
            args = self.default_args.copy()
            args.update({'bundle': bundle_file})
            logging_setup.configure_logging(MagicMock(**args), err_output=stderr)
            result = conduct_load.load(MagicMock(**args))
            self.assertFalse(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               bundle_file, self.offline_mode)

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

        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, bundle_file))
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock):
            args = self.default_args.copy()
            args.update({'bundle': bundle_file})
            logging_setup.configure_logging(MagicMock(**args), err_output=stderr)
            result = conduct_load.load(MagicMock(**args))
            self.assertFalse(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               bundle_file, self.offline_mode)

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
