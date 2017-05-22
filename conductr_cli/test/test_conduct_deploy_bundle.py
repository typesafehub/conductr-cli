from conductr_cli.test.cli_test_case import CliTestCase
from conductr_cli import conduct_deploy_bundle
from conductr_cli.exceptions import BundleResolutionError
from requests.exceptions import HTTPError
from unittest.mock import ANY, call, patch, MagicMock
import json
import logging


class TestConductDeployBundle(CliTestCase):
    dcos_mode = False
    scheme = 'http'
    host = '10.0.0.1'
    port = 9005
    base_path = '/'
    api_version = '2'
    conductr_auth = MagicMock(name='conductr auth')
    server_verification_file = MagicMock(name='server verification file')
    custom_settings = MagicMock(name='custom_settings')
    bundle_resolve_cache_dir = MagicMock(name='bundle_resolve_cache_dir')
    configuration_resolve_cache_dir = MagicMock(name='configuration_resolve_cache_dir')
    offline_mode = False
    auto_deploy = True
    target_tags = ['apples', 'oranges']

    bundle = 'cassandra'

    args = {
        'dcos_mode': dcos_mode,
        'scheme': scheme,
        'host': host,
        'port': port,
        'base_path': base_path,
        'api_version': api_version,
        'conductr_auth': conductr_auth,
        'server_verification_file': server_verification_file,
        'custom_settings': custom_settings,
        'bundle_resolve_cache_dir': bundle_resolve_cache_dir,
        'configuration_resolve_cache_dir': configuration_resolve_cache_dir,
        'offline_mode': offline_mode,
        'auto_deploy': auto_deploy,
        'target_tags': target_tags,
        'bundle': bundle,
        'configuration': None,
    }

    bundle_file_name = 'viz-v1-digest.zip'
    bundle_file_path = MagicMock(name='file for {}'.format(bundle_file_name))
    bundle_file_path_opened = MagicMock(name='opened file for {}'.format(bundle_file_name))

    bndl_config_digest = ['IGNORED', 'ABC123']
    bndl_config_file_name = 'config-{}.zip'.format(bndl_config_digest[1])
    bndl_config_path = '/tmp/{}'.format(bndl_config_file_name)
    bndl_config_path_opened = MagicMock(name='opened file for {}'.format(bndl_config_path))
    mock_bndl_result = MagicMock()
    mock_bndl_result.name = bndl_config_path

    mock_bundle_conf = MagicMock(name='bundle.conf')
    multipart_payload_content_type = 'multipart/form-data'
    mock_multipart_payload = MagicMock(name='mock http multipart payload',
                                       **{'content_type': multipart_payload_content_type})

    deployment_batch_id = {'value': 'deployment_batch_id'}
    deployment_batch_id_json = json.dumps(deployment_batch_id)

    conduct_deploy_logger = logging.getLogger('conductr_cli.conduct_deploy_bundle')

    def test_deploy_bundle_file_and_configuration_file(self):
        configuration_dir = '/tmp/custom-config'
        configuration_file_name = 'custom-config'
        configuration_file_path = MagicMock(name='file for {}'.format(configuration_file_name))

        # Mocks from conductr_cli.resolver
        mock_resolve_bundle = MagicMock(return_value=(self.bundle_file_name, self.bundle_file_path))
        mock_resolve_bundle_configuration = MagicMock(return_value=(configuration_file_name,
                                                                    configuration_file_path))

        # Mocks from conductr_cli.bundle_utils
        mock_bundle_utils_conf = MagicMock(return_value=self.mock_bundle_conf)
        mock_digest_extract_and_open = MagicMock(return_value=(self.bndl_config_path_opened, self.bndl_config_digest))

        # Mocks from conductr_cli.conduct_load
        mock_validate_cache_dir_permissions = MagicMock()
        mock_is_bundle = MagicMock(side_effect=[True, False])  # returns True for bundle.zip, but False for config dir
        mock_bndl_arguments_present = MagicMock(return_value=False)
        mock_invoke_bndl = MagicMock(return_value=self.mock_bndl_result)
        mock_open_bundle = MagicMock(return_value=(self.bundle_file_name, self.bundle_file_path_opened))
        mock_create_multipart = MagicMock(return_value=self.mock_multipart_payload)

        mock_request_deploy_confirmation = MagicMock()

        mock_http_post = self.respond_with(200, self.deployment_batch_id_json, content_type='application/json')
        mock_http_response = mock_http_post.return_value

        args_with_config = self.args.copy()
        args_with_config.update({'configuration': configuration_dir})
        input_args = MagicMock(**args_with_config)

        with patch('conductr_cli.resolver.resolve_bundle', mock_resolve_bundle), \
                patch('conductr_cli.resolver.resolve_bundle_configuration', mock_resolve_bundle_configuration), \
                patch('conductr_cli.bundle_utils.conf', mock_bundle_utils_conf), \
                patch('conductr_cli.bundle_utils.digest_extract_and_open', mock_digest_extract_and_open), \
                patch('conductr_cli.conduct_load.validate_cache_dir_permissions',
                      mock_validate_cache_dir_permissions), \
                patch('conductr_cli.conduct_load.is_bundle', mock_is_bundle), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', mock_bndl_arguments_present), \
                patch('conductr_cli.conduct_load.invoke_bndl', mock_invoke_bndl), \
                patch('conductr_cli.conduct_load.open_bundle', mock_open_bundle), \
                patch('conductr_cli.conduct_load.create_multipart', mock_create_multipart), \
                patch('conductr_cli.conduct_request.post', mock_http_post), \
                patch('conductr_cli.conduct_deploy_bundle.request_deploy_confirmation',
                      mock_request_deploy_confirmation):
            self.assertEqual(mock_http_response, conduct_deploy_bundle.deploy(input_args))

        mock_validate_cache_dir_permissions.assert_called_once_with(self.bundle_resolve_cache_dir,
                                                                    self.configuration_resolve_cache_dir,
                                                                    self.conduct_deploy_logger)
        mock_resolve_bundle.assert_called_with(self.custom_settings,
                                               self.bundle_resolve_cache_dir,
                                               self.bundle,
                                               self.offline_mode)
        mock_resolve_bundle_configuration.assert_called_once_with(self.custom_settings,
                                                                  self.configuration_resolve_cache_dir,
                                                                  configuration_dir,
                                                                  self.offline_mode)
        self.assertEqual([
            call(self.bundle_file_path),
            call(configuration_file_path),
        ], mock_is_bundle.call_args_list)
        mock_invoke_bndl.assert_called_once_with(configuration_file_path,
                                                 'configuration',
                                                 input_args,
                                                 self.mock_bundle_conf)
        mock_bndl_arguments_present.assert_not_called()
        mock_open_bundle.assert_called_once_with(self.bundle_file_name, self.bundle_file_path, self.mock_bundle_conf)
        mock_digest_extract_and_open.assert_called_once_with(self.bndl_config_path)
        mock_request_deploy_confirmation.assert_not_called()
        mock_create_multipart.assert_called_once_with(self.conduct_deploy_logger,
                                                      [('bundle', (self.bundle_file_name,
                                                                   self.bundle_file_path_opened)),
                                                       ('configuration', (self.bndl_config_file_name,
                                                                          self.bndl_config_path_opened))])

        mock_http_post.assert_called_once_with(self.dcos_mode,
                                               self.host,
                                               'http://10.0.0.1:9005/v2/deployments?bundleName=viz&tag=apples&tag=oranges',
                                               auth=self.conductr_auth,
                                               data=self.mock_multipart_payload,
                                               headers={'Content-Type': self.multipart_payload_content_type},
                                               verify=self.server_verification_file)

    def test_deploy_bundle_file(self):
        # Mocks from conductr_cli.resolver
        mock_resolve_bundle = MagicMock(return_value=(self.bundle_file_name, self.bundle_file_path))
        mock_resolve_bundle_configuration = MagicMock()

        # Mocks from conductr_cli.bundle_utils
        mock_bundle_utils_conf = MagicMock(return_value=self.mock_bundle_conf)
        mock_digest_extract_and_open = MagicMock()

        # Mocks from conductr_cli.conduct_load
        mock_validate_cache_dir_permissions = MagicMock()
        mock_is_bundle = MagicMock(return_value=True)
        mock_bndl_arguments_present = MagicMock(return_value=False)
        mock_invoke_bndl = MagicMock()
        mock_open_bundle = MagicMock(return_value=(self.bundle_file_name, self.bundle_file_path_opened))
        mock_create_multipart = MagicMock(return_value=self.mock_multipart_payload)

        mock_request_deploy_confirmation = MagicMock()

        mock_http_post = self.respond_with(200, self.deployment_batch_id_json, content_type='application/json')
        mock_http_response = mock_http_post.return_value

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.resolver.resolve_bundle', mock_resolve_bundle), \
                patch('conductr_cli.resolver.resolve_bundle_configuration', mock_resolve_bundle_configuration), \
                patch('conductr_cli.bundle_utils.conf', mock_bundle_utils_conf), \
                patch('conductr_cli.bundle_utils.digest_extract_and_open', mock_digest_extract_and_open), \
                patch('conductr_cli.conduct_load.validate_cache_dir_permissions',
                      mock_validate_cache_dir_permissions), \
                patch('conductr_cli.conduct_load.is_bundle', mock_is_bundle), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', mock_bndl_arguments_present), \
                patch('conductr_cli.conduct_load.invoke_bndl', mock_invoke_bndl), \
                patch('conductr_cli.conduct_load.open_bundle', mock_open_bundle), \
                patch('conductr_cli.conduct_load.create_multipart', mock_create_multipart), \
                patch('conductr_cli.conduct_request.post', mock_http_post), \
                patch('conductr_cli.conduct_deploy_bundle.request_deploy_confirmation',
                      mock_request_deploy_confirmation):
            self.assertEqual(mock_http_response, conduct_deploy_bundle.deploy(input_args))

        mock_validate_cache_dir_permissions.assert_called_once_with(self.bundle_resolve_cache_dir,
                                                                    self.configuration_resolve_cache_dir,
                                                                    self.conduct_deploy_logger)
        mock_resolve_bundle.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle, self.offline_mode)
        mock_resolve_bundle_configuration.assert_not_called()
        mock_is_bundle.assert_called_once_with(self.bundle_file_path)
        mock_invoke_bndl.assert_not_called()
        mock_bndl_arguments_present.assert_called_once_with(input_args)
        mock_open_bundle.assert_called_once_with(self.bundle_file_name, self.bundle_file_path, self.mock_bundle_conf)
        mock_digest_extract_and_open.assert_not_called()
        mock_request_deploy_confirmation.assert_not_called()
        mock_create_multipart.assert_called_once_with(self.conduct_deploy_logger,
                                                      [('bundle', (self.bundle_file_name,
                                                                   self.bundle_file_path_opened))])

        mock_http_post.assert_called_once_with(self.dcos_mode,
                                               self.host,
                                               'http://10.0.0.1:9005/v2/deployments?bundleName=viz&tag=apples&tag=oranges',
                                               auth=self.conductr_auth,
                                               data=self.mock_multipart_payload,
                                               headers={'Content-Type': self.multipart_payload_content_type},
                                               verify=self.server_verification_file)

    def test_deploy_bundle_from_bndl(self):
        # Mocks from conductr_cli.resolver
        mock_resolve_bundle = MagicMock(return_value=(self.bundle_file_name, self.bundle_file_path))
        mock_resolve_bundle_configuration = MagicMock()

        # Mocks from conductr_cli.bundle_utils
        mock_bundle_utils_conf = MagicMock(return_value=self.mock_bundle_conf)
        mock_digest_extract_and_open = MagicMock(return_value=(self.bndl_config_path_opened, self.bndl_config_digest))

        # Mocks from conductr_cli.conduct_load
        mock_validate_cache_dir_permissions = MagicMock()
        mock_is_bundle = MagicMock(return_value=True)
        mock_bndl_arguments_present = MagicMock(return_value=True)
        mock_invoke_bndl = MagicMock(return_value=self.mock_bndl_result)
        mock_open_bundle = MagicMock(return_value=(self.bundle_file_name, self.bundle_file_path_opened))
        mock_create_multipart = MagicMock(return_value=self.mock_multipart_payload)

        mock_request_deploy_confirmation = MagicMock()

        mock_http_post = self.respond_with(200, self.deployment_batch_id_json, content_type='application/json')
        mock_http_response = mock_http_post.return_value

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.resolver.resolve_bundle', mock_resolve_bundle), \
                patch('conductr_cli.resolver.resolve_bundle_configuration', mock_resolve_bundle_configuration), \
                patch('conductr_cli.bundle_utils.conf', mock_bundle_utils_conf), \
                patch('conductr_cli.bundle_utils.digest_extract_and_open', mock_digest_extract_and_open), \
                patch('conductr_cli.conduct_load.validate_cache_dir_permissions',
                      mock_validate_cache_dir_permissions), \
                patch('conductr_cli.conduct_load.is_bundle', mock_is_bundle), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', mock_bndl_arguments_present), \
                patch('conductr_cli.conduct_load.invoke_bndl', mock_invoke_bndl), \
                patch('conductr_cli.conduct_load.open_bundle', mock_open_bundle), \
                patch('conductr_cli.conduct_load.create_multipart', mock_create_multipart), \
                patch('conductr_cli.conduct_request.post', mock_http_post), \
                patch('conductr_cli.conduct_deploy_bundle.request_deploy_confirmation',
                      mock_request_deploy_confirmation):
            self.assertEqual(mock_http_response, conduct_deploy_bundle.deploy(input_args))

        mock_validate_cache_dir_permissions.assert_called_once_with(self.bundle_resolve_cache_dir,
                                                                    self.configuration_resolve_cache_dir,
                                                                    self.conduct_deploy_logger)
        mock_resolve_bundle.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle, self.offline_mode)
        mock_resolve_bundle_configuration.assert_not_called()
        mock_is_bundle.assert_called_once_with(self.bundle_file_path)
        # Ignore the first argument for mock_invoke_bndl since it's automatically generated temp directory.
        mock_invoke_bndl.assert_called_once_with(ANY, 'configuration', input_args, self.mock_bundle_conf)
        mock_bndl_arguments_present.assert_called_once_with(input_args)
        mock_open_bundle.assert_called_once_with(self.bundle_file_name, self.bundle_file_path, self.mock_bundle_conf)
        mock_digest_extract_and_open.assert_called_once_with(self.bndl_config_path)
        mock_request_deploy_confirmation.assert_not_called()
        mock_create_multipart.assert_called_once_with(self.conduct_deploy_logger,
                                                      [('bundle', (self.bundle_file_name,
                                                                   self.bundle_file_path_opened)),
                                                       ('configuration', (self.bndl_config_file_name,
                                                                          self.bndl_config_path_opened))])

        mock_http_post.assert_called_once_with(self.dcos_mode,
                                               self.host,
                                               'http://10.0.0.1:9005/v2/deployments?bundleName=viz&tag=apples&tag=oranges',
                                               auth=self.conductr_auth,
                                               data=self.mock_multipart_payload,
                                               headers={'Content-Type': self.multipart_payload_content_type},
                                               verify=self.server_verification_file)

    def test_confirmation(self):
        # Mocks from conductr_cli.resolver
        mock_resolve_bundle = MagicMock(return_value=(self.bundle_file_name, self.bundle_file_path))
        mock_resolve_bundle_configuration = MagicMock()

        # Mocks from conductr_cli.bundle_utils
        mock_bundle_utils_conf = MagicMock(return_value=self.mock_bundle_conf)
        mock_digest_extract_and_open = MagicMock()

        # Mocks from conductr_cli.conduct_load
        mock_validate_cache_dir_permissions = MagicMock()
        mock_is_bundle = MagicMock(return_value=True)
        mock_bndl_arguments_present = MagicMock(return_value=False)
        mock_invoke_bndl = MagicMock()
        mock_open_bundle = MagicMock(return_value=(self.bundle_file_name, self.bundle_file_path_opened))
        mock_create_multipart = MagicMock(return_value=self.mock_multipart_payload)

        mock_request_deploy_confirmation = MagicMock(return_value=True)

        mock_http_post = self.respond_with(200, self.deployment_batch_id_json, content_type='application/json')
        mock_http_response = mock_http_post.return_value

        args = self.args.copy()
        args.update({'auto_deploy': False})
        input_args = MagicMock(**args)

        with patch('conductr_cli.resolver.resolve_bundle', mock_resolve_bundle), \
                patch('conductr_cli.resolver.resolve_bundle_configuration', mock_resolve_bundle_configuration), \
                patch('conductr_cli.bundle_utils.conf', mock_bundle_utils_conf), \
                patch('conductr_cli.bundle_utils.digest_extract_and_open', mock_digest_extract_and_open), \
                patch('conductr_cli.conduct_load.validate_cache_dir_permissions',
                      mock_validate_cache_dir_permissions), \
                patch('conductr_cli.conduct_load.is_bundle', mock_is_bundle), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', mock_bndl_arguments_present), \
                patch('conductr_cli.conduct_load.invoke_bndl', mock_invoke_bndl), \
                patch('conductr_cli.conduct_load.open_bundle', mock_open_bundle), \
                patch('conductr_cli.conduct_load.create_multipart', mock_create_multipart), \
                patch('conductr_cli.conduct_request.post', mock_http_post), \
                patch('conductr_cli.conduct_deploy_bundle.request_deploy_confirmation',
                      mock_request_deploy_confirmation):
            self.assertEqual(mock_http_response, conduct_deploy_bundle.deploy(input_args))

        mock_validate_cache_dir_permissions.assert_called_once_with(self.bundle_resolve_cache_dir,
                                                                    self.configuration_resolve_cache_dir,
                                                                    self.conduct_deploy_logger)
        mock_resolve_bundle.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle, self.offline_mode)
        mock_resolve_bundle_configuration.assert_not_called()
        mock_is_bundle.assert_called_once_with(self.bundle_file_path)
        mock_invoke_bndl.assert_not_called()
        mock_bndl_arguments_present.assert_called_once_with(input_args)
        mock_open_bundle.assert_called_once_with(self.bundle_file_name, self.bundle_file_path, self.mock_bundle_conf)
        mock_digest_extract_and_open.assert_not_called()
        mock_request_deploy_confirmation.assert_called_once_with(self.bundle_file_name, input_args)
        mock_create_multipart.assert_called_once_with(self.conduct_deploy_logger,
                                                      [('bundle', (self.bundle_file_name,
                                                                   self.bundle_file_path_opened))])

        mock_http_post.assert_called_once_with(self.dcos_mode,
                                               self.host,
                                               'http://10.0.0.1:9005/v2/deployments?bundleName=viz&tag=apples&tag=oranges',
                                               auth=self.conductr_auth,
                                               data=self.mock_multipart_payload,
                                               headers={'Content-Type': self.multipart_payload_content_type},
                                               verify=self.server_verification_file)

    def test_declined(self):
        # Mocks from conductr_cli.resolver
        mock_resolve_bundle = MagicMock(return_value=(self.bundle_file_name, self.bundle_file_path))
        mock_resolve_bundle_configuration = MagicMock()

        # Mocks from conductr_cli.bundle_utils
        mock_bundle_utils_conf = MagicMock(return_value=self.mock_bundle_conf)
        mock_digest_extract_and_open = MagicMock()

        # Mocks from conductr_cli.conduct_load
        mock_validate_cache_dir_permissions = MagicMock()
        mock_is_bundle = MagicMock(return_value=True)
        mock_bndl_arguments_present = MagicMock(return_value=False)
        mock_invoke_bndl = MagicMock()
        mock_open_bundle = MagicMock(return_value=(self.bundle_file_name, self.bundle_file_path_opened))
        mock_create_multipart = MagicMock(return_value=self.mock_multipart_payload)

        mock_request_deploy_confirmation = MagicMock(return_value=False)

        mock_http_post = MagicMock()

        args = self.args.copy()
        args.update({'auto_deploy': False})
        input_args = MagicMock(**args)

        with patch('conductr_cli.resolver.resolve_bundle', mock_resolve_bundle), \
                patch('conductr_cli.resolver.resolve_bundle_configuration', mock_resolve_bundle_configuration), \
                patch('conductr_cli.bundle_utils.conf', mock_bundle_utils_conf), \
                patch('conductr_cli.bundle_utils.digest_extract_and_open', mock_digest_extract_and_open), \
                patch('conductr_cli.conduct_load.validate_cache_dir_permissions',
                      mock_validate_cache_dir_permissions), \
                patch('conductr_cli.conduct_load.is_bundle', mock_is_bundle), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', mock_bndl_arguments_present), \
                patch('conductr_cli.conduct_load.invoke_bndl', mock_invoke_bndl), \
                patch('conductr_cli.conduct_load.open_bundle', mock_open_bundle), \
                patch('conductr_cli.conduct_load.create_multipart', mock_create_multipart), \
                patch('conductr_cli.conduct_request.post', mock_http_post), \
                patch('conductr_cli.conduct_deploy_bundle.request_deploy_confirmation',
                      mock_request_deploy_confirmation):
            self.assertFalse(conduct_deploy_bundle.deploy(input_args))

        mock_validate_cache_dir_permissions.assert_called_once_with(self.bundle_resolve_cache_dir,
                                                                    self.configuration_resolve_cache_dir,
                                                                    self.conduct_deploy_logger)
        mock_resolve_bundle.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle, self.offline_mode)
        mock_resolve_bundle_configuration.assert_not_called()
        mock_is_bundle.assert_called_once_with(self.bundle_file_path)
        mock_invoke_bndl.assert_not_called()
        mock_bndl_arguments_present.assert_called_once_with(input_args)
        mock_open_bundle.assert_called_once_with(self.bundle_file_name, self.bundle_file_path, self.mock_bundle_conf)
        mock_digest_extract_and_open.assert_not_called()
        mock_request_deploy_confirmation.assert_called_once_with(self.bundle_file_name, input_args)
        mock_create_multipart.assert_not_called()
        mock_http_post.assert_not_called()

    def test_no_tags(self):
        # Mocks from conductr_cli.resolver
        mock_resolve_bundle = MagicMock(return_value=(self.bundle_file_name, self.bundle_file_path))
        mock_resolve_bundle_configuration = MagicMock()

        # Mocks from conductr_cli.bundle_utils
        mock_bundle_utils_conf = MagicMock(return_value=self.mock_bundle_conf)
        mock_digest_extract_and_open = MagicMock()

        # Mocks from conductr_cli.conduct_load
        mock_validate_cache_dir_permissions = MagicMock()
        mock_is_bundle = MagicMock(return_value=True)
        mock_bndl_arguments_present = MagicMock(return_value=False)
        mock_invoke_bndl = MagicMock()
        mock_open_bundle = MagicMock(return_value=(self.bundle_file_name, self.bundle_file_path_opened))
        mock_create_multipart = MagicMock(return_value=self.mock_multipart_payload)

        mock_request_deploy_confirmation = MagicMock()

        mock_http_post = self.respond_with(200, self.deployment_batch_id_json, content_type='application/json')
        mock_http_response = mock_http_post.return_value

        args = self.args.copy()
        args.update({'target_tags': []})
        input_args = MagicMock(**args)

        with patch('conductr_cli.resolver.resolve_bundle', mock_resolve_bundle), \
                patch('conductr_cli.resolver.resolve_bundle_configuration', mock_resolve_bundle_configuration), \
                patch('conductr_cli.bundle_utils.conf', mock_bundle_utils_conf), \
                patch('conductr_cli.bundle_utils.digest_extract_and_open', mock_digest_extract_and_open), \
                patch('conductr_cli.conduct_load.validate_cache_dir_permissions',
                      mock_validate_cache_dir_permissions), \
                patch('conductr_cli.conduct_load.is_bundle', mock_is_bundle), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', mock_bndl_arguments_present), \
                patch('conductr_cli.conduct_load.invoke_bndl', mock_invoke_bndl), \
                patch('conductr_cli.conduct_load.open_bundle', mock_open_bundle), \
                patch('conductr_cli.conduct_load.create_multipart', mock_create_multipart), \
                patch('conductr_cli.conduct_request.post', mock_http_post), \
                patch('conductr_cli.conduct_deploy_bundle.request_deploy_confirmation',
                      mock_request_deploy_confirmation):
            self.assertEqual(mock_http_response, conduct_deploy_bundle.deploy(input_args))

        mock_validate_cache_dir_permissions.assert_called_once_with(self.bundle_resolve_cache_dir,
                                                                    self.configuration_resolve_cache_dir,
                                                                    self.conduct_deploy_logger)
        mock_resolve_bundle.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle, self.offline_mode)
        mock_resolve_bundle_configuration.assert_not_called()
        mock_is_bundle.assert_called_once_with(self.bundle_file_path)
        mock_invoke_bndl.assert_not_called()
        mock_bndl_arguments_present.assert_called_once_with(input_args)
        mock_open_bundle.assert_called_once_with(self.bundle_file_name, self.bundle_file_path, self.mock_bundle_conf)
        mock_digest_extract_and_open.assert_not_called()
        mock_request_deploy_confirmation.assert_not_called()
        mock_create_multipart.assert_called_once_with(self.conduct_deploy_logger,
                                                      [('bundle', (self.bundle_file_name,
                                                                   self.bundle_file_path_opened))])

        mock_http_post.assert_called_once_with(self.dcos_mode,
                                               self.host,
                                               'http://10.0.0.1:9005/v2/deployments?bundleName=viz',
                                               auth=self.conductr_auth,
                                               data=self.mock_multipart_payload,
                                               headers={'Content-Type': self.multipart_payload_content_type},
                                               verify=self.server_verification_file)

    def test_error_bundle_resolution_error(self):
        # Mocks from conductr_cli.resolver
        mock_resolve_bundle = MagicMock(side_effect=BundleResolutionError('test only', [], []))
        mock_resolve_bundle_configuration = MagicMock()

        # Mocks from conductr_cli.bundle_utils
        mock_bundle_utils_conf = MagicMock()
        mock_digest_extract_and_open = MagicMock()

        # Mocks from conductr_cli.conduct_load
        mock_validate_cache_dir_permissions = MagicMock()
        mock_is_bundle = MagicMock()
        mock_bndl_arguments_present = MagicMock()
        mock_invoke_bndl = MagicMock()
        mock_open_bundle = MagicMock()
        mock_create_multipart = MagicMock()

        mock_request_deploy_confirmation = MagicMock()

        mock_http_post = MagicMock()

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.resolver.resolve_bundle', mock_resolve_bundle), \
                patch('conductr_cli.resolver.resolve_bundle_configuration', mock_resolve_bundle_configuration), \
                patch('conductr_cli.bundle_utils.conf', mock_bundle_utils_conf), \
                patch('conductr_cli.bundle_utils.digest_extract_and_open', mock_digest_extract_and_open), \
                patch('conductr_cli.conduct_load.validate_cache_dir_permissions',
                      mock_validate_cache_dir_permissions), \
                patch('conductr_cli.conduct_load.is_bundle', mock_is_bundle), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', mock_bndl_arguments_present), \
                patch('conductr_cli.conduct_load.invoke_bndl', mock_invoke_bndl), \
                patch('conductr_cli.conduct_load.open_bundle', mock_open_bundle), \
                patch('conductr_cli.conduct_load.create_multipart', mock_create_multipart), \
                patch('conductr_cli.conduct_request.post', mock_http_post), \
                patch('conductr_cli.conduct_deploy_bundle.request_deploy_confirmation',
                      mock_request_deploy_confirmation), \
                self.assertRaises(BundleResolutionError):
            conduct_deploy_bundle.deploy(input_args)

        mock_validate_cache_dir_permissions.assert_called_once_with(self.bundle_resolve_cache_dir,
                                                                    self.configuration_resolve_cache_dir,
                                                                    self.conduct_deploy_logger)
        mock_resolve_bundle.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle, self.offline_mode)
        mock_resolve_bundle_configuration.assert_not_called()
        mock_is_bundle.assert_not_called()
        mock_invoke_bndl.assert_not_called()
        mock_bndl_arguments_present.assert_not_called()
        mock_open_bundle.assert_not_called()
        mock_digest_extract_and_open.assert_not_called()
        mock_request_deploy_confirmation.assert_not_called()
        mock_create_multipart.assert_not_called()
        mock_http_post.assert_not_called()

    def test_error_http(self):
        # Mocks from conductr_cli.resolver
        mock_resolve_bundle = MagicMock(return_value=(self.bundle_file_name, self.bundle_file_path))
        mock_resolve_bundle_configuration = MagicMock()

        # Mocks from conductr_cli.bundle_utils
        mock_bundle_utils_conf = MagicMock(return_value=self.mock_bundle_conf)
        mock_digest_extract_and_open = MagicMock()

        # Mocks from conductr_cli.conduct_load
        mock_validate_cache_dir_permissions = MagicMock()
        mock_is_bundle = MagicMock(return_value=True)
        mock_bndl_arguments_present = MagicMock(return_value=False)
        mock_invoke_bndl = MagicMock()
        mock_open_bundle = MagicMock(return_value=(self.bundle_file_name, self.bundle_file_path_opened))
        mock_create_multipart = MagicMock(return_value=self.mock_multipart_payload)

        mock_request_deploy_confirmation = MagicMock()

        mock_http_post = self.respond_with(500, text='test error')

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.resolver.resolve_bundle', mock_resolve_bundle), \
                patch('conductr_cli.resolver.resolve_bundle_configuration', mock_resolve_bundle_configuration), \
                patch('conductr_cli.bundle_utils.conf', mock_bundle_utils_conf), \
                patch('conductr_cli.bundle_utils.digest_extract_and_open', mock_digest_extract_and_open), \
                patch('conductr_cli.conduct_load.validate_cache_dir_permissions',
                      mock_validate_cache_dir_permissions), \
                patch('conductr_cli.conduct_load.is_bundle', mock_is_bundle), \
                patch('conductr_cli.conduct_load.bndl_arguments_present', mock_bndl_arguments_present), \
                patch('conductr_cli.conduct_load.invoke_bndl', mock_invoke_bndl), \
                patch('conductr_cli.conduct_load.open_bundle', mock_open_bundle), \
                patch('conductr_cli.conduct_load.create_multipart', mock_create_multipart), \
                patch('conductr_cli.conduct_request.post', mock_http_post), \
                patch('conductr_cli.conduct_deploy_bundle.request_deploy_confirmation',
                      mock_request_deploy_confirmation), \
                self.assertRaises(HTTPError):
            conduct_deploy_bundle.deploy(input_args)

        mock_validate_cache_dir_permissions.assert_called_once_with(self.bundle_resolve_cache_dir,
                                                                    self.configuration_resolve_cache_dir,
                                                                    self.conduct_deploy_logger)
        mock_resolve_bundle.assert_called_with(self.custom_settings, self.bundle_resolve_cache_dir,
                                               self.bundle, self.offline_mode)
        mock_resolve_bundle_configuration.assert_not_called()
        mock_is_bundle.assert_called_once_with(self.bundle_file_path)
        mock_invoke_bndl.assert_not_called()
        mock_bndl_arguments_present.assert_called_once_with(input_args)
        mock_open_bundle.assert_called_once_with(self.bundle_file_name, self.bundle_file_path, self.mock_bundle_conf)
        mock_digest_extract_and_open.assert_not_called()
        mock_request_deploy_confirmation.assert_not_called()
        mock_create_multipart.assert_called_once_with(self.conduct_deploy_logger,
                                                      [('bundle', (self.bundle_file_name,
                                                                   self.bundle_file_path_opened))])

        mock_http_post.assert_called_once_with(self.dcos_mode,
                                               self.host,
                                               'http://10.0.0.1:9005/v2/deployments?bundleName=viz&tag=apples&tag=oranges',
                                               auth=self.conductr_auth,
                                               data=self.mock_multipart_payload,
                                               headers={'Content-Type': self.multipart_payload_content_type},
                                               verify=self.server_verification_file)
