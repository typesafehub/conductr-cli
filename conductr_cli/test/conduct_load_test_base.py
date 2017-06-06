from conductr_cli.test.cli_test_case import CliTestCase, strip_margin, as_error
from conductr_cli import bundle_utils, conduct_load, logging_setup
from conductr_cli.exceptions import BundleResolutionError, WaitTimeoutError
from zipfile import BadZipFile
from urllib.error import HTTPError, URLError
from unittest.mock import patch, MagicMock
import logging


class ConductLoadTestBase(CliTestCase):
    output_template = """|Retrieving bundle..
                         |{downloading_configuration}Loading bundle to ConductR..
                         |{verbose}Bundle loaded.
                         |Start bundle with:        {command} run{params} {bundle_id}
                         |Unload bundle with:       {command} unload{params} {bundle_id}
                         |Print ConductR info with: {command} info{params}
                         |Print bundle info with:   {command} info{params} {bundle_id}
                         |"""

    def __init__(self, method_name):
        super().__init__(method_name)

        self.bundle_id = None
        self.bundle_file_name = None
        self.bundle_file = None
        self.default_args = {}
        self.default_files = None
        self.default_url = None
        self.disk_space = None
        self.memory = None
        self.nr_of_cpus = None
        self.roles = []
        self.custom_settings = None
        self.offline_mode = False
        self.bundle_resolve_cache_dir = None
        self.mock_headers = {'pretend': 'header'}
        self.multipart_content_type = "multipart/form-data"
        self.multipart_mock = MagicMock()
        self.multipart_mock.content_type = self.multipart_content_type
        self.conduct_load_logger = logging.getLogger('conductr_cli.conduct_load')
        self.conductr_auth = ('username', 'password')
        self.server_verification_file = MagicMock(name='server_verification_file')

    @property
    def default_response(self):
        return strip_margin("""|{
                               |  "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c"
                               |}
                               |""")

    def default_output(self, command='conduct', params='', bundle_id='45e0c47', downloading_configuration='', verbose=''):
        return strip_margin(self.output_template.format(**{
            'command': command,
            'params': params,
            'bundle_id': bundle_id,
            'downloading_configuration': downloading_configuration,
            'verbose': verbose}))

    def base_test_success(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, self.bundle_file))
        create_multipart_mock = MagicMock(return_value=self.multipart_mock)
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        bundle_open_mock = MagicMock(side_effect=lambda p1, p2, p3: (p1, 1))
        wait_for_installation_mock = MagicMock()
        cleanup_old_bundles_mock = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.conduct_load.create_multipart', create_multipart_mock), \
                patch('conductr_cli.conduct_load.cleanup_old_bundles', cleanup_old_bundles_mock), \
                patch('requests.post', http_method), \
                patch('conductr_cli.conduct_load.open_bundle', bundle_open_mock), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        bundle_open_mock.assert_called_with(self.bundle_file_name,
                                            self.bundle_file,
                                            bundle_utils.conf(self.bundle_file))
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, self.offline_mode)
        create_multipart_mock.assert_called_with(self.conduct_load_logger, self.default_files)
        http_method.assert_called_with(self.default_url,
                                       data=self.multipart_mock,
                                       auth=self.conductr_auth,
                                       verify=self.server_verification_file,
                                       headers={'Content-Type': self.multipart_content_type, 'Host': '127.0.0.1'})
        wait_for_installation_mock.assert_called_with(self.bundle_id, input_args)
        cleanup_old_bundles_mock.assert_called_with(self.bundle_resolve_cache_dir, self.bundle_file_name,
                                                    excluded=self.bundle_file)

        self.assertEqual(self.default_output(), self.output(stdout))

    def base_test_success_dcos_mode(self):
        self.default_args['dcos_mode'] = True
        self.default_args['command'] = 'dcos conduct'

        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, self.bundle_file))
        create_multipart_mock = MagicMock(return_value=self.multipart_mock)
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        bundle_open_mock = MagicMock(side_effect=lambda p1, p2, p3: (p1, 1))

        wait_for_installation_mock = MagicMock()
        cleanup_old_bundles_mock = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.conduct_load.create_multipart', create_multipart_mock), \
                patch('conductr_cli.conduct_load.cleanup_old_bundles', cleanup_old_bundles_mock), \
                patch('dcos.http.post', http_method), \
                patch('conductr_cli.conduct_load.open_bundle', bundle_open_mock), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        bundle_open_mock.assert_called_with(self.bundle_file_name,
                                            self.bundle_file,
                                            bundle_utils.conf(self.bundle_file))
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, self.offline_mode)
        create_multipart_mock.assert_called_with(self.conduct_load_logger, self.default_files)
        http_method.assert_called_with(self.default_url,
                                       data=self.multipart_mock,
                                       auth=self.conductr_auth,
                                       verify=self.server_verification_file,
                                       headers={'Content-Type': self.multipart_content_type, 'Host': '127.0.0.1'})
        wait_for_installation_mock.assert_called_with(self.bundle_id, input_args)
        cleanup_old_bundles_mock.assert_called_with(self.bundle_resolve_cache_dir, self.bundle_file_name,
                                                    excluded=self.bundle_file)

        self.assertEqual(self.default_output(command=self.default_args['command']), self.output(stdout))

    def base_test_success_verbose(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, self.bundle_file))
        create_multipart_mock = MagicMock(return_value=self.multipart_mock)
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        bundle_open_mock = MagicMock(side_effect=lambda p1, p2, p3: (p1, 1))
        wait_for_installation_mock = MagicMock()
        cleanup_old_bundles_mock = MagicMock()

        args = self.default_args.copy()
        args.update({'verbose': True})
        input_args = MagicMock(**args)

        with \
                patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.conduct_load.create_multipart', create_multipart_mock), \
                patch('conductr_cli.conduct_load.cleanup_old_bundles', cleanup_old_bundles_mock), \
                patch('requests.post', http_method), \
                patch('conductr_cli.conduct_load.open_bundle', bundle_open_mock), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        bundle_open_mock.assert_called_with(self.bundle_file_name,
                                            self.bundle_file,
                                            bundle_utils.conf(self.bundle_file))
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, self.offline_mode)
        create_multipart_mock.assert_called_with(self.conduct_load_logger, self.default_files)
        http_method.assert_called_with(self.default_url,
                                       data=self.multipart_mock,
                                       auth=self.conductr_auth,
                                       verify=self.server_verification_file,
                                       headers={'Content-Type': self.multipart_content_type, 'Host': '127.0.0.1'})
        wait_for_installation_mock.assert_called_with(self.bundle_id, input_args)
        cleanup_old_bundles_mock.assert_called_with(self.bundle_resolve_cache_dir, self.bundle_file_name,
                                                    excluded=self.bundle_file)

        self.assertEqual(self.default_output(verbose=self.default_response), self.output(stdout))

    def base_test_success_quiet(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, self.bundle_file))
        create_multipart_mock = MagicMock(return_value=self.multipart_mock)
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        bundle_open_mock = MagicMock(side_effect=lambda p1, p2, p3: (p1, 1))
        wait_for_installation_mock = MagicMock()
        cleanup_old_bundles_mock = MagicMock()

        args = self.default_args.copy()
        args.update({'quiet': True})
        input_args = MagicMock(**args)

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.conduct_load.create_multipart', create_multipart_mock), \
                patch('conductr_cli.conduct_load.cleanup_old_bundles', cleanup_old_bundles_mock), \
                patch('requests.post', http_method), \
                patch('conductr_cli.conduct_load.open_bundle', bundle_open_mock), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        bundle_open_mock.assert_called_with(self.bundle_file_name,
                                            self.bundle_file,
                                            bundle_utils.conf(self.bundle_file))
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, self.offline_mode)
        create_multipart_mock.assert_called_with(self.conduct_load_logger, self.default_files)
        http_method.assert_called_with(self.default_url,
                                       data=self.multipart_mock,
                                       auth=self.conductr_auth,
                                       verify=self.server_verification_file,
                                       headers={'Content-Type': self.multipart_content_type, 'Host': '127.0.0.1'})
        wait_for_installation_mock.assert_called_with(self.bundle_id, input_args)
        cleanup_old_bundles_mock.assert_called_with(self.bundle_resolve_cache_dir, self.bundle_file_name,
                                                    excluded=self.bundle_file)

        self.assertEqual('45e0c477d3e5ea92aa8d85c0d8f3e25c\n', self.output(stdout))

    def base_test_success_long_ids(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, self.bundle_file))
        create_multipart_mock = MagicMock(return_value=self.multipart_mock)
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        bundle_open_mock = MagicMock(side_effect=lambda p1, p2, p3: (p1, 1))
        wait_for_installation_mock = MagicMock()
        cleanup_old_bundles_mock = MagicMock()

        args = self.default_args.copy()
        args.update({'long_ids': True})
        input_args = MagicMock(**args)

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.conduct_load.create_multipart', create_multipart_mock), \
                patch('conductr_cli.conduct_load.cleanup_old_bundles', cleanup_old_bundles_mock), \
                patch('requests.post', http_method), \
                patch('conductr_cli.conduct_load.open_bundle', bundle_open_mock), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        bundle_open_mock.assert_called_with(self.bundle_file_name,
                                            self.bundle_file,
                                            bundle_utils.conf(self.bundle_file))
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, self.offline_mode)
        create_multipart_mock.assert_called_with(self.conduct_load_logger, self.default_files)
        http_method.assert_called_with(self.default_url,
                                       data=self.multipart_mock,
                                       auth=self.conductr_auth,
                                       verify=self.server_verification_file,
                                       headers={'Content-Type': self.multipart_content_type, 'Host': '127.0.0.1'})
        wait_for_installation_mock.assert_called_with(self.bundle_id, input_args)
        cleanup_old_bundles_mock.assert_called_with(self.bundle_resolve_cache_dir, self.bundle_file_name,
                                                    excluded=self.bundle_file)

        self.assertEqual(self.default_output(bundle_id='45e0c477d3e5ea92aa8d85c0d8f3e25c'), self.output(stdout))

    def base_test_success_custom_ip_port(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, self.bundle_file))
        create_multipart_mock = MagicMock(return_value=self.multipart_mock)
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        bundle_open_mock = MagicMock(side_effect=lambda p1, p2, p3: (p1, 1))
        wait_for_installation_mock = MagicMock()
        cleanup_old_bundles_mock = MagicMock()

        cli_parameters = ' --ip 127.0.1.1 --port 9006'
        args = self.default_args.copy()
        args.update({'cli_parameters': cli_parameters})
        input_args = MagicMock(**args)

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.conduct_load.create_multipart', create_multipart_mock), \
                patch('conductr_cli.conduct_load.cleanup_old_bundles', cleanup_old_bundles_mock), \
                patch('requests.post', http_method), \
                patch('conductr_cli.conduct_load.open_bundle', bundle_open_mock), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        bundle_open_mock.assert_called_with(self.bundle_file_name,
                                            self.bundle_file,
                                            bundle_utils.conf(self.bundle_file))
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, self.offline_mode)
        create_multipart_mock.assert_called_with(self.conduct_load_logger, self.default_files)
        http_method.assert_called_with(self.default_url,
                                       data=self.multipart_mock,
                                       auth=self.conductr_auth,
                                       verify=self.server_verification_file,
                                       headers={'Content-Type': self.multipart_content_type, 'Host': '127.0.0.1'})
        wait_for_installation_mock.assert_called_with(self.bundle_id, input_args)
        cleanup_old_bundles_mock.assert_called_with(self.bundle_resolve_cache_dir, self.bundle_file_name,
                                                    excluded=self.bundle_file)

        self.assertEqual(
            self.default_output(params=cli_parameters),
            self.output(stdout))

    def base_test_success_custom_host_port(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, self.bundle_file))
        create_multipart_mock = MagicMock(return_value=self.multipart_mock)
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        bundle_open_mock = MagicMock(side_effect=lambda p1, p2, p3: (p1, 1))
        wait_for_installation_mock = MagicMock()
        cleanup_old_bundles_mock = MagicMock()

        cli_parameters = ' --host 127.0.1.1 --port 9006'
        args = self.default_args.copy()
        args.update({'cli_parameters': cli_parameters})
        input_args = MagicMock(**args)

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.conduct_load.create_multipart', create_multipart_mock), \
                patch('conductr_cli.conduct_load.cleanup_old_bundles', cleanup_old_bundles_mock), \
                patch('requests.post', http_method), \
                patch('conductr_cli.conduct_load.open_bundle', bundle_open_mock), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        bundle_open_mock.assert_called_with(self.bundle_file_name,
                                            self.bundle_file,
                                            bundle_utils.conf(self.bundle_file))
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, self.offline_mode)
        create_multipart_mock.assert_called_with(self.conduct_load_logger, self.default_files)
        http_method.assert_called_with(self.default_url,
                                       data=self.multipart_mock,
                                       auth=self.conductr_auth,
                                       verify=self.server_verification_file,
                                       headers={'Content-Type': self.multipart_content_type, 'Host': '127.0.0.1'})
        wait_for_installation_mock.assert_called_with(self.bundle_id, input_args)
        cleanup_old_bundles_mock.assert_called_with(self.bundle_resolve_cache_dir, self.bundle_file_name,
                                                    excluded=self.bundle_file)

        self.assertEqual(
            self.default_output(params=cli_parameters),
            self.output(stdout))

    def base_test_success_ip(self):
        args = {}
        args.update(self.default_args)
        args.pop('host')
        args.update({'ip': '127.0.0.1'})

        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, self.bundle_file))
        create_multipart_mock = MagicMock(return_value=self.multipart_mock)
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        bundle_open_mock = MagicMock(side_effect=lambda p1, p2, p3: (p1, 1))
        wait_for_installation_mock = MagicMock()
        cleanup_old_bundles_mock = MagicMock()

        input_args = MagicMock(**args)
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.conduct_load.create_multipart', create_multipart_mock), \
                patch('conductr_cli.conduct_load.cleanup_old_bundles', cleanup_old_bundles_mock), \
                patch('requests.post', http_method), \
                patch('conductr_cli.conduct_load.open_bundle', bundle_open_mock), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        bundle_open_mock.assert_called_with(self.bundle_file_name,
                                            self.bundle_file,
                                            bundle_utils.conf(self.bundle_file))
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, self.offline_mode)
        create_multipart_mock.assert_called_with(self.conduct_load_logger, self.default_files)
        http_method.assert_called_with(self.default_url,
                                       data=self.multipart_mock,
                                       auth=self.conductr_auth,
                                       verify=self.server_verification_file,
                                       headers={'Content-Type': self.multipart_content_type, 'Host': '127.0.0.1'})
        wait_for_installation_mock.assert_called_with(self.bundle_id, input_args)
        cleanup_old_bundles_mock.assert_called_with(self.bundle_resolve_cache_dir, self.bundle_file_name,
                                                    excluded=self.bundle_file)

        self.assertEqual(self.default_output(), self.output(stdout))

    def base_test_success_no_wait(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, self.bundle_file))
        create_multipart_mock = MagicMock(return_value=self.multipart_mock)
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        bundle_open_mock = MagicMock(side_effect=lambda p1, p2, p3: (p1, 1))
        cleanup_old_bundles_mock = MagicMock()

        args = self.default_args.copy()
        args.update({'no_wait': True})
        input_args = MagicMock(**args)

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.conduct_load.create_multipart', create_multipart_mock), \
                patch('conductr_cli.conduct_load.cleanup_old_bundles', cleanup_old_bundles_mock), \
                patch('requests.post', http_method), \
                patch('conductr_cli.conduct_load.open_bundle', bundle_open_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        bundle_open_mock.assert_called_with(self.bundle_file_name,
                                            self.bundle_file,
                                            bundle_utils.conf(self.bundle_file))
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, self.offline_mode)
        create_multipart_mock.assert_called_with(self.conduct_load_logger, self.default_files)
        http_method.assert_called_with(self.default_url,
                                       data=self.multipart_mock,
                                       auth=self.conductr_auth,
                                       verify=self.server_verification_file,
                                       headers={'Content-Type': self.multipart_content_type, 'Host': '127.0.0.1'})
        cleanup_old_bundles_mock.assert_called_with(self.bundle_resolve_cache_dir, self.bundle_file_name,
                                                    excluded=self.bundle_file)

        self.assertEqual(self.default_output(), self.output(stdout))

    def base_test_success_offline_mode(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, self.bundle_file))
        create_multipart_mock = MagicMock(return_value=self.multipart_mock)
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        bundle_open_mock = MagicMock(side_effect=lambda p1, p2, p3: (p1, 1))
        cleanup_old_bundles_mock = MagicMock()
        wait_for_installation_mock = MagicMock()

        args = self.default_args.copy()
        args.update({'offline_mode': True})
        input_args = MagicMock(**args)

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.conduct_load.create_multipart', create_multipart_mock), \
                patch('conductr_cli.conduct_load.cleanup_old_bundles', cleanup_old_bundles_mock), \
                patch('requests.post', http_method), \
                patch('conductr_cli.conduct_load.open_bundle', bundle_open_mock), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_load.load(input_args)
            self.assertTrue(result)

        bundle_open_mock.assert_called_with(self.bundle_file_name,
                                            self.bundle_file,
                                            bundle_utils.conf(self.bundle_file))
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, True)
        create_multipart_mock.assert_called_with(self.conduct_load_logger, self.default_files)
        http_method.assert_called_with(self.default_url,
                                       data=self.multipart_mock,
                                       auth=self.conductr_auth,
                                       verify=self.server_verification_file,
                                       headers={'Content-Type': self.multipart_content_type, 'Host': '127.0.0.1'})
        cleanup_old_bundles_mock.assert_called_with(self.bundle_resolve_cache_dir, self.bundle_file_name,
                                                    excluded=self.bundle_file)

        self.assertEqual(self.default_output(), self.output(stdout))

    def base_test_failure(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, self.bundle_file))
        create_multipart_mock = MagicMock(return_value=self.multipart_mock)
        http_method = self.respond_with(404)
        stdout = MagicMock()
        stderr = MagicMock()
        bundle_open_mock = MagicMock(side_effect=lambda p1, p2, p3: (p1, 1))

        input_args = MagicMock(**self.default_args)
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.conduct_load.create_multipart', create_multipart_mock), \
                patch('requests.post', http_method), \
                patch('conductr_cli.conduct_load.open_bundle', bundle_open_mock):
            logging_setup.configure_logging(input_args, stdout, stderr)
            result = conduct_load.load(input_args)
            self.assertFalse(result)

        bundle_open_mock.assert_called_with(self.bundle_file_name,
                                            self.bundle_file,
                                            bundle_utils.conf(self.bundle_file))
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, self.offline_mode)
        create_multipart_mock.assert_called_with(self.conduct_load_logger, self.default_files)
        http_method.assert_called_with(self.default_url,
                                       data=self.multipart_mock,
                                       auth=self.conductr_auth,
                                       verify=self.server_verification_file,
                                       headers={'Content-Type': self.multipart_content_type, 'Host': '127.0.0.1'})

        self.assertEqual(
            as_error(strip_margin("""|Error: 404 Not Found
                                     |""")),
            self.output(stderr))

    def base_test_failure_invalid_address(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, self.bundle_file))
        create_multipart_mock = MagicMock(return_value=self.multipart_mock)
        http_method = self.raise_connection_error('test reason', self.default_url)
        stdout = MagicMock()
        stderr = MagicMock()
        bundle_open_mock = MagicMock(side_effect=lambda p1, p2, p3: (p1, 1))

        input_args = MagicMock(**self.default_args)
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.conduct_load.create_multipart', create_multipart_mock), \
                patch('requests.post', http_method), \
                patch('conductr_cli.conduct_load.open_bundle', bundle_open_mock):
            logging_setup.configure_logging(input_args, stdout, stderr)
            result = conduct_load.load(input_args)
            self.assertFalse(result)

        bundle_open_mock.assert_called_with(self.bundle_file_name,
                                            self.bundle_file,
                                            bundle_utils.conf(self.bundle_file))
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, self.offline_mode)
        create_multipart_mock.assert_called_with(self.conduct_load_logger, self.default_files)
        http_method.assert_called_with(self.default_url,
                                       data=self.multipart_mock,
                                       auth=self.conductr_auth,
                                       verify=self.server_verification_file,
                                       headers={'Content-Type': self.multipart_content_type, 'Host': '127.0.0.1'})

        self.assertEqual(
            self.default_connection_error.format(self.default_url),
            self.output(stderr))

    def base_test_failure_no_response(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, self.bundle_file))
        create_multipart_mock = MagicMock(return_value=self.multipart_mock)
        http_method = self.raise_read_timeout_error('test reason', self.default_url)
        stdout = MagicMock()
        stderr = MagicMock()
        bundle_open_mock = MagicMock(side_effect=lambda p1, p2, p3: (p1, 1))

        input_args = MagicMock(**self.default_args)
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.conduct_load.create_multipart', create_multipart_mock), \
                patch('requests.post', http_method), \
                patch('conductr_cli.conduct_load.open_bundle', bundle_open_mock):
            logging_setup.configure_logging(input_args, stdout, stderr)
            result = conduct_load.load(input_args)
            self.assertFalse(result)

        bundle_open_mock.assert_called_with(self.bundle_file_name,
                                            self.bundle_file,
                                            bundle_utils.conf(self.bundle_file))
        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, self.offline_mode)
        create_multipart_mock.assert_called_with(self.conduct_load_logger, self.default_files)
        http_method.assert_called_with(self.default_url,
                                       data=self.multipart_mock,
                                       auth=self.conductr_auth,
                                       verify=self.server_verification_file,
                                       headers={'Content-Type': self.multipart_content_type, 'Host': '127.0.0.1'})

        self.assertEqual(
            as_error(
                strip_margin("""|Error: Timed out waiting for response from the server: test reason
                                |Error: One possible issue may be that there are not enough resources or machines with the roles that your bundle requires
                                |""")),
            self.output(stderr))

    def base_test_failure_no_bundle(self):
        resolve_bundle_mock = MagicMock(side_effect=BundleResolutionError('some message',
                                                                          cache_resolution_errors=[],
                                                                          bundle_resolution_errors=[]))
        stdout = MagicMock()
        stderr = MagicMock()

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock):
            args = self.default_args.copy()
            args.update({'bundle': 'no_such.bundle'})
            logging_setup.configure_logging(MagicMock(**args), stdout, stderr)
            result = conduct_load.load(MagicMock(**args))
            self.assertFalse(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               'no_such.bundle', self.offline_mode)

        self.assertEqual(
            as_error(strip_margin("""|Error: some message
                                     |""")),
            self.output(stderr))

    def base_test_failure_no_configuration(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, self.bundle_file))
        resolve_bundle_configuration_mock = MagicMock(side_effect=BundleResolutionError('some message',
                                                                                        cache_resolution_errors=[],
                                                                                        bundle_resolution_errors=[]))
        stdout = MagicMock()
        stderr = MagicMock()

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.resolver.resolve_bundle_configuration', resolve_bundle_configuration_mock):
            args = self.default_args.copy()
            args.update({'configuration': 'no_such.conf'})
            logging_setup.configure_logging(MagicMock(**args), stdout, stderr)
            result = conduct_load.load(MagicMock(**args))
            self.assertFalse(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, self.offline_mode)
        resolve_bundle_configuration_mock.assert_called_with(self.custom_settings, self.configuration_resolve_cache_dir,
                                                             'no_such.conf', self.offline_mode)

        self.assertEqual(
            as_error(strip_margin("""|Error: some message
                                     |""")),
            self.output(stderr))

    def base_test_failure_bad_zip(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, self.bundle_file))
        stderr = MagicMock()
        bundle_open_mock = MagicMock(side_effect=BadZipFile('test bad zip error'))

        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.conduct_load.open_bundle', bundle_open_mock):
            logging_setup.configure_logging(MagicMock(**self.default_args), err_output=stderr)
            result = conduct_load.load(MagicMock(**self.default_args))
            self.assertFalse(result)

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, self.offline_mode)
        bundle_open_mock.assert_called_with(
            self.bundle_file_name,
            self.bundle_file,
            bundle_utils.conf(self.bundle_file)
        )

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

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, self.offline_mode)

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

        resolve_bundle_mock.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle_file, self.offline_mode)

        self.assertEqual(
            as_error(strip_margin("""|Error: File not found: reason
                                     |""")),
            self.output(stderr))

    def base_test_failure_install_timeout(self):
        resolve_bundle_mock = MagicMock(return_value=(self.bundle_file_name, self.bundle_file))
        create_multipart_mock = MagicMock(return_value=self.multipart_mock)
        http_method = self.respond_with(200, self.default_response)
        stderr = MagicMock()
        bundle_open_mock = MagicMock(side_effect=lambda p1, p2, p3: (p1, 1))
        wait_for_installation_mock = MagicMock(side_effect=WaitTimeoutError('test timeout'))

        input_args = MagicMock(**self.default_args)
        with patch('conductr_cli.resolver.resolve_bundle', resolve_bundle_mock), \
                patch('conductr_cli.conduct_load.create_multipart', create_multipart_mock), \
                patch('requests.post', http_method), \
                patch('conductr_cli.conduct_load.open_bundle', bundle_open_mock), \
                patch('conductr_cli.bundle_installation.wait_for_installation', wait_for_installation_mock):
            logging_setup.configure_logging(input_args, err_output=stderr)
            result = conduct_load.load(input_args)
            self.assertFalse(result)

        bundle_open_mock.assert_called_with(self.bundle_file_name,
                                            self.bundle_file,
                                            bundle_utils.conf(self.bundle_file))
        create_multipart_mock.assert_called_with(self.conduct_load_logger, self.default_files)
        http_method.assert_called_with(self.default_url,
                                       data=self.multipart_mock,
                                       auth=self.conductr_auth,
                                       verify=self.server_verification_file,
                                       headers={'Content-Type': self.multipart_content_type, 'Host': '127.0.0.1'})
        wait_for_installation_mock.assert_called_with(self.bundle_id, input_args)

        self.assertEqual(
            as_error(strip_margin("""|Error: Timed out: test timeout
                                     |""")),
            self.output(stderr))
