from conductr_cli.test.cli_test_case import CliTestCase
from conductr_cli import conduct_deploy
from unittest.mock import patch, MagicMock


class ConductDeployTestBase(CliTestCase):

    host = '10.0.0.1'
    conductr_auth = ('username', 'password')
    server_verification_file = '/home/user/test.pem'

    bintray_webhook_secret = 'secret'
    resolved_version = {
        'org': 'typesafe',
        'repo': 'bundle',
        'package_name': 'cassandra',
        'tag': 'v1',
        'digest': 'abcabc'
    }
    deploy_uri = '/deployments/typesafe/bundle/typesafe'
    bundle_id = 'cass'
    custom_settings = MagicMock(name='custom_settings')
    url_mock = MagicMock(name='url_mock')
    hmac_mock = MagicMock(name='hmac_mock')

    def base_test_success(self, input_args, http_mock, wait_for_deployment_complete_mock):
        load_bintray_webhook_secret_mock = MagicMock(return_value=self.bintray_webhook_secret)
        resolved_version_mock = MagicMock(return_value=self.resolved_version)
        continuous_delivery_uri_mock = MagicMock(return_value=self.deploy_uri)
        request_deploy_confirmation_mock = MagicMock()
        url_mock = MagicMock(return_value=self.url_mock)
        generate_hmac_signature_mock = MagicMock(return_value=self.hmac_mock)

        with patch('conductr_cli.custom_settings.load_bintray_webhook_secret', load_bintray_webhook_secret_mock), \
                patch('conductr_cli.resolver.resolve_bundle_version', resolved_version_mock), \
                patch('conductr_cli.resolver.continuous_delivery_uri', continuous_delivery_uri_mock), \
                patch('conductr_cli.conduct_deploy.request_deploy_confirmation', request_deploy_confirmation_mock), \
                patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_deploy.generate_hmac_signature', generate_hmac_signature_mock), \
                patch('conductr_cli.conduct_request.post', http_mock):
            self.assertTrue(conduct_deploy.deploy(input_args))

        load_bintray_webhook_secret_mock.assert_called_with(input_args)
        resolved_version_mock.assert_called_with(self.custom_settings, self.bundle_id)
        continuous_delivery_uri_mock.assert_called_with(self.custom_settings, self.resolved_version)
        request_deploy_confirmation_mock.assert_not_called()
        url_mock.assert_called_with(self.deploy_uri, input_args)
        generate_hmac_signature_mock.assert_called_with(self.bintray_webhook_secret, 'cassandra')

    def base_test_success_no_wait(self, input_args, http_mock, wait_for_deployment_complete_mock):
        load_bintray_webhook_secret_mock = MagicMock(return_value=self.bintray_webhook_secret)
        resolved_version_mock = MagicMock(return_value=self.resolved_version)
        continuous_delivery_uri_mock = MagicMock(return_value=self.deploy_uri)
        request_deploy_confirmation_mock = MagicMock()
        url_mock = MagicMock(return_value=self.url_mock)
        generate_hmac_signature_mock = MagicMock(return_value=self.hmac_mock)

        with patch('conductr_cli.custom_settings.load_bintray_webhook_secret', load_bintray_webhook_secret_mock), \
                patch('conductr_cli.resolver.resolve_bundle_version', resolved_version_mock), \
                patch('conductr_cli.resolver.continuous_delivery_uri', continuous_delivery_uri_mock), \
                patch('conductr_cli.conduct_deploy.request_deploy_confirmation', request_deploy_confirmation_mock), \
                patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_deploy.generate_hmac_signature', generate_hmac_signature_mock), \
                patch('conductr_cli.conduct_request.post', http_mock):
            self.assertTrue(conduct_deploy.deploy(input_args))

        load_bintray_webhook_secret_mock.assert_called_with(input_args)
        resolved_version_mock.assert_called_with(self.custom_settings, self.bundle_id)
        continuous_delivery_uri_mock.assert_called_with(self.custom_settings, self.resolved_version)
        request_deploy_confirmation_mock.assert_not_called()
        url_mock.assert_called_with(self.deploy_uri, input_args)
        generate_hmac_signature_mock.assert_called_with(self.bintray_webhook_secret, 'cassandra')

    def base_test_success_with_confirmation(self, input_args, http_mock, wait_for_deployment_complete_mock):
        load_bintray_webhook_secret_mock = MagicMock(return_value=self.bintray_webhook_secret)
        resolved_version_mock = MagicMock(return_value=self.resolved_version)
        continuous_delivery_uri_mock = MagicMock(return_value=self.deploy_uri)
        request_deploy_confirmation_mock = MagicMock(return_value=True)
        url_mock = MagicMock(return_value=self.url_mock)
        generate_hmac_signature_mock = MagicMock(return_value=self.hmac_mock)

        with patch('conductr_cli.custom_settings.load_bintray_webhook_secret', load_bintray_webhook_secret_mock), \
                patch('conductr_cli.resolver.resolve_bundle_version', resolved_version_mock), \
                patch('conductr_cli.resolver.continuous_delivery_uri', continuous_delivery_uri_mock), \
                patch('conductr_cli.conduct_deploy.request_deploy_confirmation', request_deploy_confirmation_mock), \
                patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_deploy.generate_hmac_signature', generate_hmac_signature_mock), \
                patch('conductr_cli.conduct_request.post', http_mock):
            self.assertTrue(conduct_deploy.deploy(input_args))

        load_bintray_webhook_secret_mock.assert_called_with(input_args)
        resolved_version_mock.assert_called_with(self.custom_settings, self.bundle_id)
        continuous_delivery_uri_mock.assert_called_with(self.custom_settings, self.resolved_version)
        request_deploy_confirmation_mock.assert_called_with(self.resolved_version, input_args)
        url_mock.assert_called_with(self.deploy_uri, input_args)
        generate_hmac_signature_mock.assert_called_with(self.bintray_webhook_secret, 'cassandra')

    def base_test_success_with_tags(self, input_args, http_mock, wait_for_deployment_complete_mock):
        load_bintray_webhook_secret_mock = MagicMock(return_value=self.bintray_webhook_secret)
        resolved_version_mock = MagicMock(return_value=self.resolved_version)
        continuous_delivery_uri_mock = MagicMock(return_value=self.deploy_uri)
        request_deploy_confirmation_mock = MagicMock()
        url_mock = MagicMock(return_value=self.url_mock)
        generate_hmac_signature_mock = MagicMock(return_value=self.hmac_mock)

        with patch('conductr_cli.custom_settings.load_bintray_webhook_secret', load_bintray_webhook_secret_mock), \
                patch('conductr_cli.resolver.resolve_bundle_version', resolved_version_mock), \
                patch('conductr_cli.resolver.continuous_delivery_uri', continuous_delivery_uri_mock), \
                patch('conductr_cli.conduct_deploy.request_deploy_confirmation', request_deploy_confirmation_mock), \
                patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_deploy.generate_hmac_signature', generate_hmac_signature_mock), \
                patch('conductr_cli.conduct_request.post', http_mock):
            self.assertTrue(conduct_deploy.deploy(input_args))

        load_bintray_webhook_secret_mock.assert_called_with(input_args)
        resolved_version_mock.assert_called_with(self.custom_settings, self.bundle_id)
        continuous_delivery_uri_mock.assert_called_with(self.custom_settings, self.resolved_version)
        request_deploy_confirmation_mock.assert_not_called()
        url_mock.assert_called_with('{}?tag=1.0.1&tag=white+nectarine'.format(self.deploy_uri), input_args)
        generate_hmac_signature_mock.assert_called_with(self.bintray_webhook_secret, 'cassandra')

    def base_test_declined(self):
        load_bintray_webhook_secret_mock = MagicMock(return_value=self.bintray_webhook_secret)
        resolved_version_mock = MagicMock(return_value=self.resolved_version)
        continuous_delivery_uri_mock = MagicMock(return_value=self.deploy_uri)
        request_deploy_confirmation_mock = MagicMock(return_value=False)
        url_mock = MagicMock(return_value=self.url_mock)
        generate_hmac_signature_mock = MagicMock(return_value=self.hmac_mock)
        http_mock = MagicMock()

        input_args = MagicMock(**{
            'dcos_mode': False,
            'host': self.host,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file,
            'auto_deploy': False,
            'bundle': self.bundle_id,
            'tags': [],
            'custom_settings': self.custom_settings,
            'no_wait': False
        })

        with patch('conductr_cli.custom_settings.load_bintray_webhook_secret', load_bintray_webhook_secret_mock), \
                patch('conductr_cli.resolver.resolve_bundle_version', resolved_version_mock), \
                patch('conductr_cli.resolver.continuous_delivery_uri', continuous_delivery_uri_mock), \
                patch('conductr_cli.conduct_deploy.request_deploy_confirmation', request_deploy_confirmation_mock), \
                patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_deploy.generate_hmac_signature', generate_hmac_signature_mock), \
                patch('conductr_cli.conduct_request.post', http_mock):
            self.assertIsNone(conduct_deploy.deploy(input_args))

        load_bintray_webhook_secret_mock.assert_called_with(input_args)
        resolved_version_mock.assert_called_with(self.custom_settings, self.bundle_id)
        continuous_delivery_uri_mock.assert_called_with(self.custom_settings, self.resolved_version)
        request_deploy_confirmation_mock.assert_called_with(self.resolved_version, input_args)
        url_mock.assert_not_called()
        generate_hmac_signature_mock.assert_not_called()
        http_mock.assert_not_called()

    def base_test_error_bintray_webhook_secret_not_defined(self):
        load_bintray_webhook_secret_mock = MagicMock(return_value=None)
        resolved_version_mock = MagicMock()
        continuous_delivery_uri_mock = MagicMock()
        request_deploy_confirmation_mock = MagicMock()
        url_mock = MagicMock()
        generate_hmac_signature_mock = MagicMock()
        http_mock = MagicMock()

        input_args = MagicMock(**{
            'dcos_mode': False,
            'host': self.host,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file,
            'auto_deploy': False,
            'bundle': self.bundle_id,
            'tags': [],
            'custom_settings': self.custom_settings,
            'no_wait': False
        })

        with patch('conductr_cli.custom_settings.load_bintray_webhook_secret', load_bintray_webhook_secret_mock), \
                patch('conductr_cli.resolver.resolve_bundle_version', resolved_version_mock), \
                patch('conductr_cli.resolver.continuous_delivery_uri', continuous_delivery_uri_mock), \
                patch('conductr_cli.conduct_deploy.request_deploy_confirmation', request_deploy_confirmation_mock), \
                patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_deploy.generate_hmac_signature', generate_hmac_signature_mock), \
                patch('conductr_cli.conduct_request.post', http_mock):
            self.assertIsNone(conduct_deploy.deploy(input_args))

        load_bintray_webhook_secret_mock.assert_called_with(input_args)
        resolved_version_mock.assert_not_called()
        continuous_delivery_uri_mock.assert_not_called()
        request_deploy_confirmation_mock.assert_not_called()
        url_mock.assert_not_called()
        generate_hmac_signature_mock.assert_not_called()
        http_mock.assert_not_called()

    def base_test_error_resolved_version_not_found(self):
        load_bintray_webhook_secret_mock = MagicMock(return_value=self.bintray_webhook_secret)
        resolved_version_mock = MagicMock(return_value=None)
        continuous_delivery_uri_mock = MagicMock()
        request_deploy_confirmation_mock = MagicMock()
        url_mock = MagicMock()
        generate_hmac_signature_mock = MagicMock()
        http_mock = MagicMock()

        input_args = MagicMock(**{
            'dcos_mode': False,
            'host': self.host,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file,
            'auto_deploy': False,
            'bundle': self.bundle_id,
            'tags': [],
            'custom_settings': self.custom_settings,
            'no_wait': False
        })

        with patch('conductr_cli.custom_settings.load_bintray_webhook_secret', load_bintray_webhook_secret_mock), \
                patch('conductr_cli.resolver.resolve_bundle_version', resolved_version_mock), \
                patch('conductr_cli.resolver.continuous_delivery_uri', continuous_delivery_uri_mock), \
                patch('conductr_cli.conduct_deploy.request_deploy_confirmation', request_deploy_confirmation_mock), \
                patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_deploy.generate_hmac_signature', generate_hmac_signature_mock), \
                patch('conductr_cli.conduct_request.post', http_mock):
            self.assertIsNone(conduct_deploy.deploy(input_args))

        load_bintray_webhook_secret_mock.assert_called_with(input_args)
        resolved_version_mock.assert_called_with(self.custom_settings, self.bundle_id)
        continuous_delivery_uri_mock.assert_not_called()
        request_deploy_confirmation_mock.assert_not_called()
        url_mock.assert_not_called()
        generate_hmac_signature_mock.assert_not_called()
        http_mock.assert_not_called()

    def base_test_error_deploy_uri_not_found(self):
        load_bintray_webhook_secret_mock = MagicMock(return_value=self.bintray_webhook_secret)
        resolved_version_mock = MagicMock(return_value=self.resolved_version)
        continuous_delivery_uri_mock = MagicMock(return_value=None)
        request_deploy_confirmation_mock = MagicMock()
        url_mock = MagicMock()
        generate_hmac_signature_mock = MagicMock()
        http_mock = MagicMock()

        input_args = MagicMock(**{
            'dcos_mode': False,
            'host': self.host,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file,
            'auto_deploy': False,
            'bundle': self.bundle_id,
            'tags': [],
            'custom_settings': self.custom_settings,
            'no_wait': False
        })

        with patch('conductr_cli.custom_settings.load_bintray_webhook_secret', load_bintray_webhook_secret_mock), \
                patch('conductr_cli.resolver.resolve_bundle_version', resolved_version_mock), \
                patch('conductr_cli.resolver.continuous_delivery_uri', continuous_delivery_uri_mock), \
                patch('conductr_cli.conduct_deploy.request_deploy_confirmation', request_deploy_confirmation_mock), \
                patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_deploy.generate_hmac_signature', generate_hmac_signature_mock), \
                patch('conductr_cli.conduct_request.post', http_mock):
            self.assertIsNone(conduct_deploy.deploy(input_args))

        load_bintray_webhook_secret_mock.assert_called_with(input_args)
        resolved_version_mock.assert_called_with(self.custom_settings, self.bundle_id)
        continuous_delivery_uri_mock.assert_called_with(self.custom_settings, self.resolved_version)
        request_deploy_confirmation_mock.assert_not_called()
        url_mock.assert_not_called()
        generate_hmac_signature_mock.assert_not_called()
        http_mock.assert_not_called()

    def base_test_http_post_error(self):
        load_bintray_webhook_secret_mock = MagicMock(return_value=self.bintray_webhook_secret)
        resolved_version_mock = MagicMock(return_value=self.resolved_version)
        continuous_delivery_uri_mock = MagicMock(return_value=self.deploy_uri)
        request_deploy_confirmation_mock = MagicMock()
        url_mock = MagicMock(return_value=self.url_mock)
        generate_hmac_signature_mock = MagicMock(return_value=self.hmac_mock)
        http_mock = self.respond_with(status_code=404)

        input_args = MagicMock(**{
            'dcos_mode': False,
            'host': self.host,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file,
            'auto_deploy': True,
            'bundle': self.bundle_id,
            'tags': [],
            'custom_settings': self.custom_settings,
            'no_wait': False
        })

        with patch('conductr_cli.custom_settings.load_bintray_webhook_secret', load_bintray_webhook_secret_mock), \
                patch('conductr_cli.resolver.resolve_bundle_version', resolved_version_mock), \
                patch('conductr_cli.resolver.continuous_delivery_uri', continuous_delivery_uri_mock), \
                patch('conductr_cli.conduct_deploy.request_deploy_confirmation', request_deploy_confirmation_mock), \
                patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_deploy.generate_hmac_signature', generate_hmac_signature_mock), \
                patch('conductr_cli.conduct_request.post', http_mock):
            self.assertFalse(conduct_deploy.deploy(input_args))

        load_bintray_webhook_secret_mock.assert_called_with(input_args)
        resolved_version_mock.assert_called_with(self.custom_settings, self.bundle_id)
        continuous_delivery_uri_mock.assert_called_with(self.custom_settings, self.resolved_version)
        request_deploy_confirmation_mock.assert_not_called()
        url_mock.assert_called_with(self.deploy_uri, input_args)
        generate_hmac_signature_mock.assert_called_with(self.bintray_webhook_secret, 'cassandra')
        http_mock.assert_called_with(False, self.host, self.url_mock,
                                     json={
                                         'package': 'cassandra',
                                         'version': 'v1-abcabc'
                                     },
                                     headers={'X-Bintray-Hook-Hmac': self.hmac_mock},
                                     auth=self.conductr_auth,
                                     verify=self.server_verification_file)
