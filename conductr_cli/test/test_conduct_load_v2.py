from conductr_cli.test.cli_test_case import create_temp_bundle, strip_margin, as_error, \
    create_temp_bundle_with_contents, create_attributes_object
from conductr_cli.test.conduct_load_test_base import ConductLoadTestBase
from conductr_cli import conduct_load, logging_setup
from conductr_cli.bndl_utils import BndlFormat
from unittest import TestCase
from unittest.mock import ANY, call, patch, MagicMock, Mock


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
        self.system_version = '2.3'
        self.compatibility_version = '2.0'
        self.tags = ['2.0.0']
        self.custom_settings = Mock()
        self.bundle_resolve_cache_dir = 'bundle-resolve-cache-dir'
        self.configuration_resolve_cache_dir = 'configuration-resolve-cache-dir'

        self.tmpdir, self.bundle_file = create_temp_bundle(
            strip_margin("""|nrOfCpus               = {}
                            |memory                 = {}
                            |diskSpace              = {}
                            |roles                  = [{}]
                            |name                   = {}
                            |system                 = {}
                            |systemVersion          = {}
                            |compatibilityVersion   = {}
                            |tags                   = [{}]
                            |""").format(self.nr_of_cpus,
                                         self.memory,
                                         self.disk_space,
                                         ', '.join(self.roles),
                                         self.bundle_file_name,
                                         self.system,
                                         self.system_version,
                                         self.compatibility_version,
                                         self.tags))

        self.default_args = {
            'dcos_mode': False,
            'scheme': 'http',
            'host': '127.0.0.1',
            'port': 9005,
            'base_path': '/',
            'api_version': '2',
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

        self.default_url = 'http://127.0.0.1:9005/v2/bundles'

        self.default_files = [
            ('bundleConf', ('bundle.conf', 'mock bundle.conf - string i/o')),
            ('bundle', (self.bundle_file_name, 1))
        ]

    def test_success(self):
        conf_mock = MagicMock(return_value='mock bundle.conf')
        string_io_mock = MagicMock(return_value='mock bundle.conf - string i/o')
        with \
                patch('conductr_cli.bundle_utils.conf', conf_mock), \
                patch('conductr_cli.conduct_load.string_io', string_io_mock), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', lambda _: False), \
                patch('conductr_cli.conduct_load.is_bundle', lambda _: True):
            self.base_test_success()
        conf_mock.assert_called_with(self.bundle_file)
        string_io_mock.assert_called_with('mock bundle.conf')

    def test_success_dcos_mode(self):
        self.default_url = 'http://127.0.0.1/v2/bundles'
        conf_mock = MagicMock(return_value='mock bundle.conf')
        string_io_mock = MagicMock(return_value='mock bundle.conf - string i/o')
        with \
                patch('conductr_cli.bundle_utils.conf', conf_mock), \
                patch('conductr_cli.conduct_load.string_io', string_io_mock), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', lambda _: False), \
                patch('conductr_cli.conduct_load.is_bundle', lambda _: True):
            self.base_test_success_dcos_mode()
        conf_mock.assert_called_with(self.bundle_file)
        string_io_mock.assert_called_with('mock bundle.conf')

    def test_success_verbose(self):
        conf_mock = MagicMock(return_value='mock bundle.conf')
        string_io_mock = MagicMock(return_value='mock bundle.conf - string i/o')
        with \
                patch('conductr_cli.bundle_utils.conf', conf_mock), \
                patch('conductr_cli.conduct_load.string_io', string_io_mock), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', lambda _: False), \
                patch('conductr_cli.conduct_load.is_bundle', lambda _: True):
            self.base_test_success_verbose()
        conf_mock.assert_called_with(self.bundle_file)
        string_io_mock.assert_called_with('mock bundle.conf')

    def test_success_quiet(self):
        conf_mock = MagicMock(return_value='mock bundle.conf')
        string_io_mock = MagicMock(return_value='mock bundle.conf - string i/o')
        with \
                patch('conductr_cli.bundle_utils.conf', conf_mock), \
                patch('conductr_cli.conduct_load.string_io', string_io_mock), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', lambda _: False), \
                patch('conductr_cli.conduct_load.is_bundle', lambda _: True):
            self.base_test_success_quiet()
        conf_mock.assert_called_with(self.bundle_file)
        string_io_mock.assert_called_with('mock bundle.conf')

    def test_success_long_ids(self):
        conf_mock = MagicMock(return_value='mock bundle.conf')
        string_io_mock = MagicMock(return_value='mock bundle.conf - string i/o')
        with \
                patch('conductr_cli.bundle_utils.conf', conf_mock), \
                patch('conductr_cli.conduct_load.string_io', string_io_mock), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', lambda _: False), \
                patch('conductr_cli.conduct_load.is_bundle', lambda _: True):
            self.base_test_success_long_ids()
        conf_mock.assert_called_with(self.bundle_file)
        string_io_mock.assert_called_with('mock bundle.conf')

    def test_success_custom_ip_port(self):
        conf_mock = MagicMock(return_value='mock bundle.conf')
        string_io_mock = MagicMock(return_value='mock bundle.conf - string i/o')
        with \
                patch('conductr_cli.bundle_utils.conf', conf_mock), \
                patch('conductr_cli.conduct_load.string_io', string_io_mock), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', lambda _: False), \
                patch('conductr_cli.conduct_load.is_bundle', lambda _: True):
            self.base_test_success_custom_ip_port()
        conf_mock.assert_called_with(self.bundle_file)
        string_io_mock.assert_called_with('mock bundle.conf')

    def test_success_custom_host_port(self):
        conf_mock = MagicMock(return_value='mock bundle.conf')
        string_io_mock = MagicMock(return_value='mock bundle.conf - string i/o')
        with \
                patch('conductr_cli.bundle_utils.conf', conf_mock), \
                patch('conductr_cli.conduct_load.string_io', string_io_mock), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', lambda _: False), \
                patch('conductr_cli.conduct_load.is_bundle', lambda _: True):
            self.base_test_success_custom_host_port()
        conf_mock.assert_called_with(self.bundle_file)
        string_io_mock.assert_called_with('mock bundle.conf')

    def test_success_ip(self):
        conf_mock = MagicMock(return_value='mock bundle.conf')
        string_io_mock = MagicMock(return_value='mock bundle.conf - string i/o')
        with \
                patch('conductr_cli.bundle_utils.conf', conf_mock), \
                patch('conductr_cli.conduct_load.string_io', string_io_mock), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', lambda _: False), \
                patch('conductr_cli.conduct_load.is_bundle', lambda _: True):
            self.base_test_success_ip()
        conf_mock.assert_called_with(self.bundle_file)
        string_io_mock.assert_called_with('mock bundle.conf')

    def test_success_with_configuration(self):
        tmpdir, config_file = create_temp_bundle_with_contents({
            'bundle.conf': '{name="overlaid-name"}',
            'config.sh': 'echo configuring'
        })

        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, self.bundle_file))
        resolve_bundle_configuration_mock = MagicMock(return_value=('config.zip', config_file))
        conf_mock = MagicMock(side_effect=['mock bundle.conf', 'mock bundle.conf overlay'])
        string_io_mock = MagicMock(side_effect=['mock bundle.conf - string i/o',
                                                'mock bundle.conf overlay - string i/o'])
        create_multipart_mock = MagicMock(return_value=self.multipart_mock)
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        open_mock = MagicMock(return_value=(1, None))
        bundle_open_mock = MagicMock(side_effect=lambda p1, p2, p3: (p1, 1))
        wait_for_installation_mock = MagicMock()

        args = self.default_args.copy()
        args.update({'configuration': config_file})
        input_args = MagicMock(**args)

        with \
                patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.resolver.resolve_bundle_configuration', resolve_bundle_configuration_mock), \
                patch('conductr_cli.bundle_utils.conf', conf_mock), \
                patch('conductr_cli.conduct_load.string_io', string_io_mock), \
                patch('conductr_cli.conduct_load.create_multipart', create_multipart_mock), \
                patch('requests.post', http_method), \
                patch('conductr_cli.bundle_utils.digest_extract_and_open', open_mock), \
                patch('conductr_cli.conduct_load.open_bundle', bundle_open_mock), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', lambda _: False), \
                patch('conductr_cli.conduct_load.is_bundle', lambda _: True):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, self.offline_mode)
        resolve_bundle_configuration_mock.assert_called_with(self.custom_settings, self.configuration_resolve_cache_dir,
                                                             config_file, self.offline_mode)
        self.assertEqual(
            conf_mock.call_args_list,
            [
                call(self.bundle_file),
                call(config_file)
            ]
        )

        self.assertEqual(
            string_io_mock.call_args_list,
            [
                call('mock bundle.conf'),
                call('mock bundle.conf overlay')
            ]
        )

        self.assertEqual(
            bundle_open_mock.call_args_list,
            [call(self.bundle_file_name, self.bundle_file, 'mock bundle.conf')]
        )

        self.assertEqual(
            open_mock.call_args_list,
            [call(config_file)]
        )

        expected_files = [
            ('bundleConf', ('bundle.conf', 'mock bundle.conf - string i/o')),
            ('bundleConfOverlay', ('bundle.conf', 'mock bundle.conf overlay - string i/o')),
            ('bundle', ('bundle.zip', 1)),
            ('configuration', ('config.zip', 1))
        ]
        create_multipart_mock.assert_called_with(self.conduct_load_logger, expected_files)

        http_method.assert_called_with(self.default_url,
                                       data=self.multipart_mock,
                                       auth=self.conductr_auth,
                                       verify=self.server_verification_file,
                                       headers={'Content-Type': self.multipart_content_type, 'Host': '127.0.0.1'})

        wait_for_installation_mock.assert_called_with(self.bundle_id, input_args)

        self.assertEqual(self.default_output(downloading_configuration='Retrieving configuration..\n'),
                         self.output(stdout))

    def test_success_with_configuration_no_bundle_conf(self):
        tmpdir, config_file = create_temp_bundle_with_contents({
            'config.sh': 'echo configuring'
        })

        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, self.bundle_file))
        resolve_bundle_configuration_mock = MagicMock(return_value=('config.zip', config_file))
        conf_mock = MagicMock(side_effect=['mock bundle.conf', None])
        string_io_mock = MagicMock(return_value='mock bundle.conf - string i/o')
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
                patch('conductr_cli.bundle_utils.conf', conf_mock), \
                patch('conductr_cli.conduct_load.string_io', string_io_mock), \
                patch('conductr_cli.conduct_load.create_multipart', create_multipart_mock), \
                patch('requests.post', http_method), \
                patch('conductr_cli.bundle_utils.digest_extract_and_open', open_mock), \
                patch('conductr_cli.conduct_load.open_bundle', bundle_open_mock), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', lambda _: False), \
                patch('conductr_cli.conduct_load.is_bundle', lambda _: True), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, self.offline_mode)
        resolve_bundle_configuration_mock.assert_called_with(self.custom_settings, self.configuration_resolve_cache_dir,
                                                             config_file, self.offline_mode)

        self.assertEqual(
            conf_mock.call_args_list,
            [
                call(self.bundle_file),
                call(config_file)
            ]
        )

        string_io_mock.assert_called_with('mock bundle.conf')

        self.assertEqual(
            bundle_open_mock.call_args_list,
            [call(self.bundle_file_name, self.bundle_file, 'mock bundle.conf')]
        )

        self.assertEqual(
            open_mock.call_args_list,
            [call(config_file)]
        )

        expected_files = [
            ('bundleConf', ('bundle.conf', 'mock bundle.conf - string i/o')),
            ('bundle', ('bundle.zip', 1)),
            ('configuration', ('config.zip', 1))
        ]
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
        conf_mock = MagicMock(return_value='mock bundle.conf')
        string_io_mock = MagicMock(return_value='mock bundle.conf - string i/o')
        with \
                patch('conductr_cli.bundle_utils.conf', conf_mock), \
                patch('conductr_cli.conduct_load.string_io', string_io_mock), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', lambda _: False), \
                patch('conductr_cli.conduct_load.is_bundle', lambda _: True):
            self.base_test_success_no_wait()
        conf_mock.assert_called_with(self.bundle_file)
        string_io_mock.assert_called_with('mock bundle.conf')

    def test_success_offline_mode(self):
        conf_mock = MagicMock(return_value='mock bundle.conf')
        string_io_mock = MagicMock(return_value='mock bundle.conf - string i/o')
        with \
                patch('conductr_cli.bundle_utils.conf', conf_mock), \
                patch('conductr_cli.conduct_load.string_io', string_io_mock), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', lambda _: False), \
                patch('conductr_cli.conduct_load.is_bundle', lambda _: True):
            self.base_test_success_offline_mode()
        conf_mock.assert_called_with(self.bundle_file)
        string_io_mock.assert_called_with('mock bundle.conf')

    def test_failure(self):
        conf_mock = MagicMock(return_value='mock bundle.conf')
        string_io_mock = MagicMock(return_value='mock bundle.conf - string i/o')
        with \
                patch('conductr_cli.bundle_utils.conf', conf_mock), \
                patch('conductr_cli.conduct_load.string_io', string_io_mock), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', lambda _: False), \
                patch('conductr_cli.conduct_load.is_bundle', lambda _: True):
            self.base_test_failure()
        conf_mock.assert_called_with(self.bundle_file)
        string_io_mock.assert_called_with('mock bundle.conf')

    def test_failure_invalid_address(self):
        conf_mock = MagicMock(return_value='mock bundle.conf')
        string_io_mock = MagicMock(return_value='mock bundle.conf - string i/o')
        with \
                patch('conductr_cli.bundle_utils.conf', conf_mock), \
                patch('conductr_cli.conduct_load.string_io', string_io_mock), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', lambda _: False), \
                patch('conductr_cli.conduct_load.is_bundle', lambda _: True):
            self.base_test_failure_invalid_address()
        conf_mock.assert_called_with(self.bundle_file)
        string_io_mock.assert_called_with('mock bundle.conf')

    def test_failure_no_response(self):
        conf_mock = MagicMock(return_value='mock bundle.conf')
        string_io_mock = MagicMock(return_value='mock bundle.conf - string i/o')
        with \
                patch('conductr_cli.bundle_utils.conf', conf_mock), \
                patch('conductr_cli.conduct_load.string_io', string_io_mock), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', lambda _: False), \
                patch('conductr_cli.conduct_load.is_bundle', lambda _: True):
            self.base_test_failure_no_response()
        conf_mock.assert_called_with(self.bundle_file)
        string_io_mock.assert_called_with('mock bundle.conf')

    def test_failure_no_bundle(self):
        self.base_test_failure_no_bundle()

    def test_failure_bad_zip(self):
        self.base_test_failure_bad_zip()

    def test_failure_no_file_http_error(self):
        self.base_test_failure_no_file_http_error()

    def test_failure_no_file_url_error(self):
        self.base_test_failure_no_file_url_error()

    def test_failure_no_bundle_conf(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, self.bundle_file))
        conf_mock = MagicMock(return_value=None)
        stderr = MagicMock()

        with \
                patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.bundle_utils.conf', conf_mock), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', lambda _: False), \
                patch('conductr_cli.conduct_load.is_bundle', lambda _: True):
            args = self.default_args.copy()
            logging_setup.configure_logging(MagicMock(**args), err_output=stderr)
            result = conduct_load.load(MagicMock(**args))
            self.assertFalse(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, self.offline_mode)

        self.assertEqual(
            as_error(strip_margin("""|Error: Problem with the bundle: Unable to find bundle.conf within the bundle file
                                     |""")),
            self.output(stderr))
        conf_mock.assert_called_with(self.bundle_file)

    def test_failure_install_timeout(self):
        conf_mock = MagicMock(return_value='mock bundle.conf')
        string_io_mock = MagicMock(return_value='mock bundle.conf - string i/o')
        with \
                patch('conductr_cli.bundle_utils.conf', conf_mock), \
                patch('conductr_cli.conduct_load.string_io', string_io_mock), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', lambda _: False), \
                patch('conductr_cli.conduct_load.is_bundle', lambda _: True):
            self.base_test_failure_install_timeout()
        conf_mock.assert_called_with(self.bundle_file)
        string_io_mock.assert_called_with('mock bundle.conf')

    def test_not_bundle_invoke_bndl(self):
        tmpdir, config_file = create_temp_bundle_with_contents({
            'config.sh': 'echo configuring'
        })

        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, self.bundle_file))
        resolve_bundle_configuration_mock = MagicMock(return_value=('config.zip', config_file))
        conf_mock = MagicMock(side_effect=['mock bundle.conf', None])
        string_io_mock = MagicMock(return_value='mock bundle.conf - string i/o')
        create_multipart_mock = MagicMock(return_value=self.multipart_mock)

        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        open_mock = MagicMock(return_value=(1, None))
        bundle_open_mock = MagicMock(side_effect=lambda p1, p2, p3: (p1, 1))
        wait_for_installation_mock = MagicMock()

        args = self.default_args.copy()
        args.update({'configuration': config_file})
        input_args = MagicMock(**args)

        bndl_mock = MagicMock(side_effect=[
            create_attributes_object({'name': '/my/bundle'}),
            create_attributes_object({'name': '/my/config'})
        ])

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.resolver.resolve_bundle_configuration', resolve_bundle_configuration_mock), \
                patch('conductr_cli.bundle_utils.conf', conf_mock), \
                patch('conductr_cli.conduct_load.string_io', string_io_mock), \
                patch('conductr_cli.conduct_load.create_multipart', create_multipart_mock), \
                patch('requests.post', http_method), \
                patch('conductr_cli.bundle_utils.digest_extract_and_open', open_mock), \
                patch('conductr_cli.conduct_load.open_bundle', bundle_open_mock), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', lambda _: False), \
                patch('conductr_cli.conduct_load.is_bundle', lambda _: False), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock), \
                patch('conductr_cli.conduct_load.invoke_bndl', bndl_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, self.offline_mode)
        resolve_bundle_configuration_mock.assert_called_with(self.custom_settings, self.configuration_resolve_cache_dir,
                                                             config_file, self.offline_mode)

        self.assertEqual(
            bndl_mock.call_args_list,
            [
                call(self.bundle_file),
                call(config_file, BndlFormat.CONFIGURATION.value, input_args, 'mock bundle.conf')
            ]
        )

        self.assertEqual(
            conf_mock.call_args_list,
            [
                call('/my/bundle'),
                call('/my/config')
            ]
        )

        string_io_mock.assert_called_with('mock bundle.conf')

        self.assertEqual(
            bundle_open_mock.call_args_list,
            [call(self.bundle_file_name, '/my/bundle', 'mock bundle.conf')]
        )

        self.assertEqual(
            open_mock.call_args_list,
            [call('/my/config')]
        )

        wait_for_installation_mock.assert_called_with(self.bundle_id, input_args)

        self.assertEqual(self.default_output(downloading_configuration='Retrieving configuration..\n'),
                         self.output(stdout))

    def test_not_bundle_no_config_invoke_bndl(self):
        conf_mock = MagicMock(return_value='mock bundle.conf')
        string_io_mock = MagicMock(return_value='mock bundle.conf - string i/o')
        bndl_mock = MagicMock(return_value=create_attributes_object({'name': self.bundle_file}))
        with \
                patch('conductr_cli.bundle_utils.conf', conf_mock), \
                patch('conductr_cli.conduct_load.string_io', string_io_mock), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', lambda _: False), \
                patch('conductr_cli.conduct_load.is_bundle', lambda _: False), \
                patch('conductr_cli.conduct_load.invoke_bndl', bndl_mock):
            self.base_test_success_offline_mode()
        conf_mock.assert_called_with(self.bundle_file)
        bndl_mock.assert_called_once_with(self.bundle_file)
        string_io_mock.assert_called_with('mock bundle.conf')

    def test_bundle_no_config_bndl_args_invoke_bndl(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, self.bundle_file))
        resolve_bundle_configuration_mock = MagicMock()
        conf_mock = MagicMock(side_effect=['mock bundle.conf', None])
        string_io_mock = MagicMock(return_value='mock bundle.conf - string i/o')
        create_multipart_mock = MagicMock(return_value=self.multipart_mock)

        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        open_mock = MagicMock(return_value=(1, None))
        bundle_open_mock = MagicMock(side_effect=lambda p1, p2, p3: (p1, 1))
        wait_for_installation_mock = MagicMock()

        bndl_mock = MagicMock(return_value=create_attributes_object({'name': '/my/config'}))

        input_args = MagicMock(**self.default_args)

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.resolver.resolve_bundle_configuration', resolve_bundle_configuration_mock), \
                patch('conductr_cli.bundle_utils.conf', conf_mock), \
                patch('conductr_cli.conduct_load.string_io', string_io_mock), \
                patch('conductr_cli.conduct_load.create_multipart', create_multipart_mock), \
                patch('requests.post', http_method), \
                patch('conductr_cli.bundle_utils.digest_extract_and_open', open_mock), \
                patch('conductr_cli.conduct_load.open_bundle', bundle_open_mock), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', lambda _: True), \
                patch('conductr_cli.conduct_load.is_bundle', lambda _: True), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock), \
                patch('conductr_cli.conduct_load.invoke_bndl', bndl_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, self.offline_mode)
        resolve_bundle_configuration_mock.assert_not_called()

        # The invoke_bndl will be called with the name of Python generated temp file as the first argument.
        # We'll accept any file name, and verify the remaining arguments
        temp_file_name = ANY
        bndl_mock.assert_called_once_with(temp_file_name, 'configuration', input_args, 'mock bundle.conf')

        self.assertEqual(
            conf_mock.call_args_list,
            [
                call(self.bundle_file),
                call('/my/config')
            ]
        )

        string_io_mock.assert_called_once_with('mock bundle.conf')

        bundle_open_mock.assert_called_once_with(self.bundle_file_name, self.bundle_file, 'mock bundle.conf')

        open_mock.assert_called_once_with('/my/config')

        wait_for_installation_mock.assert_called_with(self.bundle_id, input_args)

        self.assertEqual(self.default_output(), self.output(stdout))


class TestBndArgumentsPresent(TestCase):
    # This is the empty arguments from bndl command
    empty_bndl_args = {
        'endpoint_dicts': [],
        'envs': [],
        'check_addresses': None,
        'check_connection_timeout': None,
        'check_initial_delay': None,
        'annotations': [],
        'compatibility_version': None,
        'disk_space': None,
        'memory': None,
        'name': None,
        'nr_of_cpus': None,
        'start_command_dicts': [],
        'roles': [],
        'system': None,
        'system_version': None,
        'tags': [],
        'version': None,
        'volume_dicts': []
    }

    def test_not_present(self):
        input_args = MagicMock(**self.empty_bndl_args)
        input_args.name = None
        self.assertFalse(conduct_load.bndl_arguments_present(input_args))

    def test_present(self):
        # Iterate through every key, replacing its empty value with populated value.
        for key in sorted(self.empty_bndl_args.keys()):
            empty_value = self.empty_bndl_args[key]

            # Replace a None with a string value, or a populated array if it's an array
            if empty_value is None:
                value = 'not empty'
            else:
                value = ['not empty']

            args = {}
            args.update(self.empty_bndl_args)
            args.update({key: value})

            input_args = MagicMock(**args)
            if key == 'name':
                input_args.name = 'a name'
            else:
                input_args.name = None

            self.assertTrue(conduct_load.bndl_arguments_present(input_args),
                            'bndl argument {} should be present'.format(key))
