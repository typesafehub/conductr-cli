from conductr_cli.test.cli_test_case import CliTestCase
from conductr_cli import conduct_deploy_bintray
from unittest.mock import patch, MagicMock
from requests.exceptions import HTTPError
import json


class TestDeploy(CliTestCase):
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
    bundle_name = 'cass'
    custom_settings = MagicMock(name='custom_settings')
    url_mock = MagicMock(name='url_mock')
    hmac_mock = MagicMock(name='hmac_mock')

    deployment_batch_id = 'batchId'
    deployment_batch = {
        'value': deployment_batch_id
    }

    dcos_mode = False
    args = {
        'dcos_mode': dcos_mode,
        'host': host,
        'conductr_auth': conductr_auth,
        'server_verification_file': server_verification_file,
        'auto_deploy': True,
        'bundle': bundle_name,
        'target_tags': [],
        'custom_settings': custom_settings,
        'no_wait': False
    }

    def test_success(self):
        load_bintray_webhook_secret_mock = MagicMock(return_value=self.bintray_webhook_secret)
        resolved_version_mock = MagicMock(return_value=self.resolved_version)
        continuous_delivery_uri_mock = MagicMock(return_value=self.deploy_uri)
        request_deploy_confirmation_mock = MagicMock(return_value=True)
        url_mock = MagicMock(return_value=self.url_mock)
        generate_hmac_signature_mock = MagicMock(return_value=self.hmac_mock)
        http_mock = self.respond_with(text=json.dumps(self.deployment_batch), content_type='application/json')

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.custom_settings.load_bintray_webhook_secret', load_bintray_webhook_secret_mock), \
                patch('conductr_cli.resolver.resolve_bundle_version', resolved_version_mock), \
                patch('conductr_cli.resolver.continuous_delivery_uri', continuous_delivery_uri_mock), \
                patch('conductr_cli.conduct_deploy_bintray.request_deploy_confirmation', request_deploy_confirmation_mock), \
                patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_deploy.generate_hmac_signature', generate_hmac_signature_mock), \
                patch('conductr_cli.conduct_request.post', http_mock):
            self.assertTrue(conduct_deploy_bintray.deploy(input_args))

        load_bintray_webhook_secret_mock.assert_called_with(input_args)
        resolved_version_mock.assert_called_with(self.custom_settings, self.bundle_name)
        continuous_delivery_uri_mock.assert_called_with(self.custom_settings, self.resolved_version)
        request_deploy_confirmation_mock.assert_not_called()
        url_mock.assert_called_with(self.deploy_uri, input_args)
        generate_hmac_signature_mock.assert_called_with(self.bintray_webhook_secret, 'cassandra')
        http_mock.assert_called_once_with(self.dcos_mode,
                                          self.host,
                                          self.url_mock,
                                          auth=self.conductr_auth,
                                          headers={'X-Bintray-Hook-Hmac': self.hmac_mock},
                                          json={
                                              'package': 'cassandra',
                                              'version': 'v1-abcabc',
                                          },
                                          verify=self.server_verification_file)

    def test_declined(self):
        load_bintray_webhook_secret_mock = MagicMock(return_value=self.bintray_webhook_secret)
        resolved_version_mock = MagicMock(return_value=self.resolved_version)
        continuous_delivery_uri_mock = MagicMock(return_value=self.deploy_uri)
        request_deploy_confirmation_mock = MagicMock(return_value=False)
        url_mock = MagicMock(return_value=self.url_mock)
        generate_hmac_signature_mock = MagicMock(return_value=self.hmac_mock)
        http_mock = self.respond_with(text=json.dumps(self.deployment_batch), content_type='application/json')

        args = self.args.copy()
        args.update({'auto_deploy': False})
        input_args = MagicMock(**args)

        with patch('conductr_cli.custom_settings.load_bintray_webhook_secret', load_bintray_webhook_secret_mock), \
                patch('conductr_cli.resolver.resolve_bundle_version', resolved_version_mock), \
                patch('conductr_cli.resolver.continuous_delivery_uri', continuous_delivery_uri_mock), \
                patch('conductr_cli.conduct_deploy_bintray.request_deploy_confirmation', request_deploy_confirmation_mock), \
                patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_deploy.generate_hmac_signature', generate_hmac_signature_mock), \
                patch('conductr_cli.conduct_request.post', http_mock):
            self.assertFalse(conduct_deploy_bintray.deploy(input_args))

        load_bintray_webhook_secret_mock.assert_called_with(input_args)
        resolved_version_mock.assert_called_with(self.custom_settings, self.bundle_name)
        continuous_delivery_uri_mock.assert_called_with(self.custom_settings, self.resolved_version)
        request_deploy_confirmation_mock.assert_called_once_with(self.resolved_version, input_args)
        url_mock.assert_not_called()
        generate_hmac_signature_mock.assert_not_called()
        http_mock.assert_not_called()

    def test_error_bintray_webhook_secret_not_defined(self):
        load_bintray_webhook_secret_mock = MagicMock(return_value=None)
        resolved_version_mock = MagicMock(return_value=self.resolved_version)
        continuous_delivery_uri_mock = MagicMock(return_value=self.deploy_uri)
        request_deploy_confirmation_mock = MagicMock(return_value=True)
        url_mock = MagicMock(return_value=self.url_mock)
        generate_hmac_signature_mock = MagicMock(return_value=self.hmac_mock)
        http_mock = self.respond_with(text=json.dumps(self.deployment_batch), content_type='application/json')

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.custom_settings.load_bintray_webhook_secret', load_bintray_webhook_secret_mock), \
                patch('conductr_cli.resolver.resolve_bundle_version', resolved_version_mock), \
                patch('conductr_cli.resolver.continuous_delivery_uri', continuous_delivery_uri_mock), \
                patch('conductr_cli.conduct_deploy_bintray.request_deploy_confirmation', request_deploy_confirmation_mock), \
                patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_deploy.generate_hmac_signature', generate_hmac_signature_mock), \
                patch('conductr_cli.conduct_request.post', http_mock):
            self.assertFalse(conduct_deploy_bintray.deploy(input_args))

        load_bintray_webhook_secret_mock.assert_called_with(input_args)
        resolved_version_mock.assert_not_called()
        continuous_delivery_uri_mock.assert_not_called()
        request_deploy_confirmation_mock.assert_not_called()
        url_mock.assert_not_called()
        generate_hmac_signature_mock.assert_not_called()
        http_mock.assert_not_called()

    def test_error_resolved_version_not_found(self):
        load_bintray_webhook_secret_mock = MagicMock(return_value=self.bintray_webhook_secret)
        resolved_version_mock = MagicMock(return_value=None)
        continuous_delivery_uri_mock = MagicMock(return_value=self.deploy_uri)
        request_deploy_confirmation_mock = MagicMock(return_value=True)
        url_mock = MagicMock(return_value=self.url_mock)
        generate_hmac_signature_mock = MagicMock(return_value=self.hmac_mock)
        http_mock = self.respond_with(text=json.dumps(self.deployment_batch), content_type='application/json')

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.custom_settings.load_bintray_webhook_secret', load_bintray_webhook_secret_mock), \
                patch('conductr_cli.resolver.resolve_bundle_version', resolved_version_mock), \
                patch('conductr_cli.resolver.continuous_delivery_uri', continuous_delivery_uri_mock), \
                patch('conductr_cli.conduct_deploy_bintray.request_deploy_confirmation', request_deploy_confirmation_mock), \
                patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_deploy.generate_hmac_signature', generate_hmac_signature_mock), \
                patch('conductr_cli.conduct_request.post', http_mock):
            self.assertFalse(conduct_deploy_bintray.deploy(input_args))

        load_bintray_webhook_secret_mock.assert_called_with(input_args)
        resolved_version_mock.assert_called_with(self.custom_settings, self.bundle_name)
        continuous_delivery_uri_mock.assert_not_called()
        request_deploy_confirmation_mock.assert_not_called()
        url_mock.assert_not_called()
        generate_hmac_signature_mock.assert_not_called()
        http_mock.assert_not_called()

    def test_error_deploy_uri_not_found(self):
        load_bintray_webhook_secret_mock = MagicMock(return_value=self.bintray_webhook_secret)
        resolved_version_mock = MagicMock(return_value=self.resolved_version)
        continuous_delivery_uri_mock = MagicMock(return_value=None)
        request_deploy_confirmation_mock = MagicMock(return_value=True)
        url_mock = MagicMock(return_value=self.url_mock)
        generate_hmac_signature_mock = MagicMock(return_value=self.hmac_mock)
        http_mock = self.respond_with(text=json.dumps(self.deployment_batch), content_type='application/json')

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.custom_settings.load_bintray_webhook_secret', load_bintray_webhook_secret_mock), \
                patch('conductr_cli.resolver.resolve_bundle_version', resolved_version_mock), \
                patch('conductr_cli.resolver.continuous_delivery_uri', continuous_delivery_uri_mock), \
                patch('conductr_cli.conduct_deploy_bintray.request_deploy_confirmation', request_deploy_confirmation_mock), \
                patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_deploy.generate_hmac_signature', generate_hmac_signature_mock), \
                patch('conductr_cli.conduct_request.post', http_mock):
            self.assertFalse(conduct_deploy_bintray.deploy(input_args))

        load_bintray_webhook_secret_mock.assert_called_with(input_args)
        resolved_version_mock.assert_called_with(self.custom_settings, self.bundle_name)
        continuous_delivery_uri_mock.assert_called_with(self.custom_settings, self.resolved_version)
        request_deploy_confirmation_mock.assert_not_called()
        url_mock.assert_not_called()
        generate_hmac_signature_mock.assert_not_called()
        http_mock.assert_not_called()

    def test_http_error(self):
        load_bintray_webhook_secret_mock = MagicMock(return_value=self.bintray_webhook_secret)
        resolved_version_mock = MagicMock(return_value=self.resolved_version)
        continuous_delivery_uri_mock = MagicMock(return_value=self.deploy_uri)
        request_deploy_confirmation_mock = MagicMock(return_value=True)
        url_mock = MagicMock(return_value=self.url_mock)
        generate_hmac_signature_mock = MagicMock(return_value=self.hmac_mock)
        http_mock = self.respond_with(status_code=500)

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.custom_settings.load_bintray_webhook_secret', load_bintray_webhook_secret_mock), \
                patch('conductr_cli.resolver.resolve_bundle_version', resolved_version_mock), \
                patch('conductr_cli.resolver.continuous_delivery_uri', continuous_delivery_uri_mock), \
                patch('conductr_cli.conduct_deploy_bintray.request_deploy_confirmation', request_deploy_confirmation_mock), \
                patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_deploy.generate_hmac_signature', generate_hmac_signature_mock), \
                patch('conductr_cli.conduct_request.post', http_mock),\
                self.assertRaises(HTTPError):
            conduct_deploy_bintray.deploy(input_args)

        load_bintray_webhook_secret_mock.assert_called_with(input_args)
        resolved_version_mock.assert_called_with(self.custom_settings, self.bundle_name)
        continuous_delivery_uri_mock.assert_called_with(self.custom_settings, self.resolved_version)
        request_deploy_confirmation_mock.assert_not_called()
        url_mock.assert_called_with(self.deploy_uri, input_args)
        generate_hmac_signature_mock.assert_called_with(self.bintray_webhook_secret, 'cassandra')
        http_mock.assert_called_once_with(self.dcos_mode,
                                          self.host,
                                          self.url_mock,
                                          auth=self.conductr_auth,
                                          headers={'X-Bintray-Hook-Hmac': self.hmac_mock},
                                          json={
                                              'package': 'cassandra',
                                              'version': 'v1-abcabc',
                                          },
                                          verify=self.server_verification_file)


class TestDeployConfirmation(CliTestCase):

    resolved_version = {
        'org': 'typesafe',
        'repo': 'bundle',
        'package_name': 'cassandra',
        'tag': 'v1',
        'digest': 'd073991ab918ee22c7426af8a62a48c5-a53237c1f4a067e13ef00090627fb3de'
    }

    def test_return_true_if_empty(self):
        input_mock = MagicMock(return_value='')
        input_args = MagicMock(**{
            'long_ids': False
        })

        with patch('builtins.input', input_mock):
            self.assertTrue(conduct_deploy_bintray.request_deploy_confirmation(self.resolved_version, input_args))

        input_mock.assert_called_with('Deploy cassandra:v1-d073991-a53237c? [Y/n]: ')

    def test_return_true_if_empty_with_long_ids(self):
        input_mock = MagicMock(return_value='')
        input_args = MagicMock(**{
            'long_ids': True
        })

        with patch('builtins.input', input_mock):
            self.assertTrue(conduct_deploy_bintray.request_deploy_confirmation(self.resolved_version, input_args))

        input_mock.assert_called_with('Deploy cassandra:v1-d073991ab918ee22c7426af8a62a48c5-a53237c1f4a067e13ef00090627fb3de? [Y/n]: ')

    def test_return_true_if_y(self):
        input_mock = MagicMock(return_value='y')
        input_args = MagicMock(**{
            'long_ids': False
        })

        with patch('builtins.input', input_mock):
            self.assertTrue(conduct_deploy_bintray.request_deploy_confirmation(self.resolved_version, input_args))

        input_mock.assert_called_with('Deploy cassandra:v1-d073991-a53237c? [Y/n]: ')

    def test_return_true_if_yes(self):
        input_mock = MagicMock(return_value='yes')
        input_args = MagicMock(**{
            'long_ids': False
        })

        with patch('builtins.input', input_mock):
            self.assertTrue(conduct_deploy_bintray.request_deploy_confirmation(self.resolved_version, input_args))

        input_mock.assert_called_with('Deploy cassandra:v1-d073991-a53237c? [Y/n]: ')

    def test_return_false(self):
        input_mock = MagicMock(return_value='anything else')
        input_args = MagicMock(**{
            'long_ids': False
        })

        with patch('builtins.input', input_mock):
            self.assertFalse(conduct_deploy_bintray.request_deploy_confirmation(self.resolved_version, input_args))

        input_mock.assert_called_with('Deploy cassandra:v1-d073991-a53237c? [Y/n]: ')
