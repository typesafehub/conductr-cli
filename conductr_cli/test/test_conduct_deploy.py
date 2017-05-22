from conductr_cli.test.cli_test_case import CliTestCase
from conductr_cli.test.conduct_deploy_test_base import ConductDeployTestBase
from conductr_cli import conduct_deploy
from unittest.mock import patch, MagicMock
import json


class TestConductDeployWithCDv2(ConductDeployTestBase):

    deployment_id = 'deployment_id'

    def test_success(self):
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

        http_mock = self.respond_with(text=self.deployment_id)
        wait_for_deployment_complete_mock = MagicMock()

        with patch('conductr_cli.bundle_deploy_v2.wait_for_deployment_complete', wait_for_deployment_complete_mock):
            self.base_test_success(input_args, http_mock, wait_for_deployment_complete_mock)

        http_mock.assert_called_with(False, self.host, self.url_mock,
                                     json={
                                         'package': 'cassandra',
                                         'version': 'v1-abcabc'
                                     },
                                     headers={'X-Bintray-Hook-Hmac': self.hmac_mock},
                                     auth=self.conductr_auth,
                                     verify=self.server_verification_file)

        wait_for_deployment_complete_mock.assert_called_with(self.deployment_id,
                                                             self.resolved_version,
                                                             input_args)

    def test_success_no_wait(self):
        input_args = MagicMock(**{
            'dcos_mode': False,
            'host': self.host,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file,
            'auto_deploy': True,
            'bundle': self.bundle_id,
            'tags': [],
            'custom_settings': self.custom_settings,
            'no_wait': True
        })

        http_mock = self.respond_with(text=self.deployment_id)
        wait_for_deployment_complete_mock = MagicMock()

        with patch('conductr_cli.bundle_deploy_v2.wait_for_deployment_complete', wait_for_deployment_complete_mock):
            self.base_test_success_no_wait(input_args, http_mock, wait_for_deployment_complete_mock)

        http_mock.assert_called_with(False, self.host, self.url_mock,
                                     json={
                                         'package': 'cassandra',
                                         'version': 'v1-abcabc'
                                     },
                                     headers={'X-Bintray-Hook-Hmac': self.hmac_mock},
                                     auth=self.conductr_auth,
                                     verify=self.server_verification_file)
        wait_for_deployment_complete_mock.assert_not_called()

    def test_success_with_confirmation(self):
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

        http_mock = self.respond_with(text=self.deployment_id)
        wait_for_deployment_complete_mock = MagicMock()

        with patch('conductr_cli.bundle_deploy_v2.wait_for_deployment_complete', wait_for_deployment_complete_mock):
            self.base_test_success_with_confirmation(input_args, http_mock, wait_for_deployment_complete_mock)

        http_mock.assert_called_with(False, self.host, self.url_mock,
                                     json={
                                         'package': 'cassandra',
                                         'version': 'v1-abcabc'
                                     },
                                     headers={'X-Bintray-Hook-Hmac': self.hmac_mock},
                                     auth=self.conductr_auth,
                                     verify=self.server_verification_file)
        wait_for_deployment_complete_mock.assert_called_with(self.deployment_id,
                                                             self.resolved_version,
                                                             input_args)

    def test_success_with_tags(self):
        input_args = MagicMock(**{
            'dcos_mode': False,
            'host': self.host,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file,
            'auto_deploy': True,
            'bundle': self.bundle_id,
            'tags': ['1.0.1', 'white nectarine'],
            'custom_settings': self.custom_settings,
            'no_wait': False
        })

        http_mock = self.respond_with(text=self.deployment_id)
        wait_for_deployment_complete_mock = MagicMock()

        with patch('conductr_cli.bundle_deploy_v2.wait_for_deployment_complete', wait_for_deployment_complete_mock):
            self.base_test_success_with_tags(input_args, http_mock, wait_for_deployment_complete_mock)

        http_mock.assert_called_with(False, self.host, self.url_mock,
                                     json={
                                         'package': 'cassandra',
                                         'version': 'v1-abcabc'
                                     },
                                     headers={'X-Bintray-Hook-Hmac': self.hmac_mock},
                                     auth=self.conductr_auth,
                                     verify=self.server_verification_file)
        wait_for_deployment_complete_mock.assert_called_with(self.deployment_id,
                                                             self.resolved_version,
                                                             input_args)

    def test_declined(self):
        wait_for_deployment_complete_mock = MagicMock()
        with patch('conductr_cli.bundle_deploy_v2.wait_for_deployment_complete', wait_for_deployment_complete_mock):
            self.base_test_declined()
        wait_for_deployment_complete_mock.assert_not_called()

    def test_error_bintray_webhook_secret_not_defined(self):
        wait_for_deployment_complete_mock = MagicMock()
        with patch('conductr_cli.bundle_deploy_v2.wait_for_deployment_complete', wait_for_deployment_complete_mock):
            self.base_test_error_bintray_webhook_secret_not_defined()
        wait_for_deployment_complete_mock.assert_not_called()

    def test_error_resolved_version_not_found(self):
        wait_for_deployment_complete_mock = MagicMock()
        with patch('conductr_cli.bundle_deploy_v2.wait_for_deployment_complete', wait_for_deployment_complete_mock):
            self.base_test_error_resolved_version_not_found()
        wait_for_deployment_complete_mock.assert_not_called()

    def test_error_deploy_uri_not_found(self):
        wait_for_deployment_complete_mock = MagicMock()
        with patch('conductr_cli.bundle_deploy_v2.wait_for_deployment_complete', wait_for_deployment_complete_mock):
            self.base_test_error_deploy_uri_not_found()
        wait_for_deployment_complete_mock.assert_not_called()

    def test_http_post_error(self):
        wait_for_deployment_complete_mock = MagicMock()
        with patch('conductr_cli.bundle_deploy_v2.wait_for_deployment_complete', wait_for_deployment_complete_mock):
            self.base_test_http_post_error()
        wait_for_deployment_complete_mock.assert_not_called()


class TestConductDeployWithCDv3(ConductDeployTestBase):

    deployment_batch_id = 'batchId'
    deployment_batch = {
        'value': deployment_batch_id
    }

    def test_success(self):
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

        http_mock = self.respond_with(text=json.dumps(self.deployment_batch), content_type='application/json')
        wait_for_deployment_complete_mock = MagicMock()

        with patch('conductr_cli.bundle_deploy_v3.wait_for_deployment_complete', wait_for_deployment_complete_mock):
            self.base_test_success(input_args, http_mock, wait_for_deployment_complete_mock)

        http_mock.assert_called_with(False, self.host, self.url_mock,
                                     json={
                                         'package': 'cassandra',
                                         'version': 'v1-abcabc'
                                     },
                                     headers={'X-Bintray-Hook-Hmac': self.hmac_mock},
                                     auth=self.conductr_auth,
                                     verify=self.server_verification_file)

        wait_for_deployment_complete_mock.assert_called_with(self.deployment_batch_id,
                                                             self.resolved_version,
                                                             input_args)

    def test_success_no_wait(self):
        input_args = MagicMock(**{
            'dcos_mode': False,
            'host': self.host,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file,
            'auto_deploy': True,
            'bundle': self.bundle_id,
            'tags': [],
            'custom_settings': self.custom_settings,
            'no_wait': True
        })

        http_mock = self.respond_with(text=json.dumps(self.deployment_batch), content_type='application/json')
        wait_for_deployment_complete_mock = MagicMock()

        with patch('conductr_cli.bundle_deploy_v3.wait_for_deployment_complete', wait_for_deployment_complete_mock):
            self.base_test_success_no_wait(input_args, http_mock, wait_for_deployment_complete_mock)

        http_mock.assert_called_with(False, self.host, self.url_mock,
                                     json={
                                         'package': 'cassandra',
                                         'version': 'v1-abcabc'
                                     },
                                     headers={'X-Bintray-Hook-Hmac': self.hmac_mock},
                                     auth=self.conductr_auth,
                                     verify=self.server_verification_file)
        wait_for_deployment_complete_mock.assert_not_called()

    def test_success_with_confirmation(self):
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

        http_mock = self.respond_with(text=json.dumps(self.deployment_batch), content_type='application/json')
        wait_for_deployment_complete_mock = MagicMock()

        with patch('conductr_cli.bundle_deploy_v3.wait_for_deployment_complete', wait_for_deployment_complete_mock):
            self.base_test_success_with_confirmation(input_args, http_mock, wait_for_deployment_complete_mock)

        http_mock.assert_called_with(False, self.host, self.url_mock,
                                     json={
                                         'package': 'cassandra',
                                         'version': 'v1-abcabc'
                                     },
                                     headers={'X-Bintray-Hook-Hmac': self.hmac_mock},
                                     auth=self.conductr_auth,
                                     verify=self.server_verification_file)
        wait_for_deployment_complete_mock.assert_called_with(self.deployment_batch_id,
                                                             self.resolved_version,
                                                             input_args)

    def test_success_with_tags(self):
        input_args = MagicMock(**{
            'dcos_mode': False,
            'host': self.host,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file,
            'auto_deploy': True,
            'bundle': self.bundle_id,
            'tags': ['1.0.1', 'white nectarine'],
            'custom_settings': self.custom_settings,
            'no_wait': False
        })

        http_mock = self.respond_with(text=json.dumps(self.deployment_batch), content_type='application/json')
        wait_for_deployment_complete_mock = MagicMock()

        with patch('conductr_cli.bundle_deploy_v3.wait_for_deployment_complete', wait_for_deployment_complete_mock):
            self.base_test_success_with_tags(input_args, http_mock, wait_for_deployment_complete_mock)

        http_mock.assert_called_with(False, self.host, self.url_mock,
                                     json={
                                         'package': 'cassandra',
                                         'version': 'v1-abcabc'
                                     },
                                     headers={'X-Bintray-Hook-Hmac': self.hmac_mock},
                                     auth=self.conductr_auth,
                                     verify=self.server_verification_file)
        wait_for_deployment_complete_mock.assert_called_with(self.deployment_batch_id,
                                                             self.resolved_version,
                                                             input_args)

    def test_declined(self):
        wait_for_deployment_complete_mock = MagicMock()
        with patch('conductr_cli.bundle_deploy_v3.wait_for_deployment_complete', wait_for_deployment_complete_mock):
            self.base_test_declined()
        wait_for_deployment_complete_mock.assert_not_called()

    def test_error_bintray_webhook_secret_not_defined(self):
        wait_for_deployment_complete_mock = MagicMock()
        with patch('conductr_cli.bundle_deploy_v3.wait_for_deployment_complete', wait_for_deployment_complete_mock):
            self.base_test_error_bintray_webhook_secret_not_defined()
        wait_for_deployment_complete_mock.assert_not_called()

    def test_error_resolved_version_not_found(self):
        wait_for_deployment_complete_mock = MagicMock()
        with patch('conductr_cli.bundle_deploy_v3.wait_for_deployment_complete', wait_for_deployment_complete_mock):
            self.base_test_error_resolved_version_not_found()
        wait_for_deployment_complete_mock.assert_not_called()

    def test_error_deploy_uri_not_found(self):
        wait_for_deployment_complete_mock = MagicMock()
        with patch('conductr_cli.bundle_deploy_v3.wait_for_deployment_complete', wait_for_deployment_complete_mock):
            self.base_test_error_deploy_uri_not_found()
        wait_for_deployment_complete_mock.assert_not_called()

    def test_http_post_error(self):
        wait_for_deployment_complete_mock = MagicMock()
        with patch('conductr_cli.bundle_deploy_v3.wait_for_deployment_complete', wait_for_deployment_complete_mock):
            self.base_test_http_post_error()
        wait_for_deployment_complete_mock.assert_not_called()


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
            self.assertTrue(conduct_deploy.request_deploy_confirmation(self.resolved_version, input_args))

        input_mock.assert_called_with('Deploy cassandra:v1-d073991-a53237c? [Y/n]: ')

    def test_return_true_if_empty_with_long_ids(self):
        input_mock = MagicMock(return_value='')
        input_args = MagicMock(**{
            'long_ids': True
        })

        with patch('builtins.input', input_mock):
            self.assertTrue(conduct_deploy.request_deploy_confirmation(self.resolved_version, input_args))

        input_mock.assert_called_with('Deploy cassandra:v1-d073991ab918ee22c7426af8a62a48c5-a53237c1f4a067e13ef00090627fb3de? [Y/n]: ')

    def test_return_true_if_y(self):
        input_mock = MagicMock(return_value='y')
        input_args = MagicMock(**{
            'long_ids': False
        })

        with patch('builtins.input', input_mock):
            self.assertTrue(conduct_deploy.request_deploy_confirmation(self.resolved_version, input_args))

        input_mock.assert_called_with('Deploy cassandra:v1-d073991-a53237c? [Y/n]: ')

    def test_return_true_if_yes(self):
        input_mock = MagicMock(return_value='yes')
        input_args = MagicMock(**{
            'long_ids': False
        })

        with patch('builtins.input', input_mock):
            self.assertTrue(conduct_deploy.request_deploy_confirmation(self.resolved_version, input_args))

        input_mock.assert_called_with('Deploy cassandra:v1-d073991-a53237c? [Y/n]: ')

    def test_return_false(self):
        input_mock = MagicMock(return_value='anything else')
        input_args = MagicMock(**{
            'long_ids': False
        })

        with patch('builtins.input', input_mock):
            self.assertFalse(conduct_deploy.request_deploy_confirmation(self.resolved_version, input_args))

        input_mock.assert_called_with('Deploy cassandra:v1-d073991-a53237c? [Y/n]: ')
