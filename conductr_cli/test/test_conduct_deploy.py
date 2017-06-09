from conductr_cli.test.cli_test_case import CliTestCase, as_error, strip_margin
from conductr_cli import conduct_deploy, logging_setup
from conductr_cli.exceptions import BintrayResolutionError, BintrayCredentialsNotFoundError, BundleResolutionError, \
    InsecureFilePermissions, MalformedBundleError, MalformedBintrayCredentialsError, WaitTimeoutError
from pyhocon.exceptions import ConfigException
from requests.exceptions import ConnectionError, HTTPError, ReadTimeout
from urllib.error import URLError
from unittest.mock import patch, MagicMock
from zipfile import BadZipFile
import json
import urllib


class TestConductDeploy(CliTestCase):
    deployment_batch_id = 'deployment-batch-id'
    deployment_batch = {'value': deployment_batch_id}
    deployment_batch_json = json.dumps(deployment_batch)

    bundle = 'cassandra'
    args = {
        'webhook': None,
        'bundle': bundle,
        'no_wait': False
    }

    def test_success_deploy_bundle_v3(self):
        bintray_deploy = MagicMock()
        bundle_deploy = self.respond_with(200, self.deployment_batch_json, content_type='application/json')

        wait_for_deployment_complete_v3 = MagicMock()
        wait_for_deployment_complete_v2 = MagicMock()

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.conduct_deploy_bintray.deploy', bintray_deploy), \
                patch('conductr_cli.conduct_deploy_bundle.deploy', bundle_deploy), \
                patch('conductr_cli.bundle_deploy_v3.wait_for_deployment_complete', wait_for_deployment_complete_v3), \
                patch('conductr_cli.bundle_deploy_v2.wait_for_deployment_complete', wait_for_deployment_complete_v2):
            self.assertTrue(conduct_deploy.deploy(input_args))

        bintray_deploy.assert_not_called()
        bundle_deploy.assert_called_once_with(input_args)
        wait_for_deployment_complete_v3.assert_called_once_with(self.deployment_batch_id, input_args)
        wait_for_deployment_complete_v2.assert_not_called()

    def test_success_no_wait(self):
        bintray_deploy = MagicMock()
        bundle_deploy = self.respond_with(200, self.deployment_batch_json, content_type='application/json')

        wait_for_deployment_complete_v3 = MagicMock()
        wait_for_deployment_complete_v2 = MagicMock()

        args = self.args.copy()
        args.update({'no_wait': True})
        input_args = MagicMock(**args)

        with patch('conductr_cli.conduct_deploy_bintray.deploy', bintray_deploy), \
                patch('conductr_cli.conduct_deploy_bundle.deploy', bundle_deploy), \
                patch('conductr_cli.bundle_deploy_v3.wait_for_deployment_complete', wait_for_deployment_complete_v3), \
                patch('conductr_cli.bundle_deploy_v2.wait_for_deployment_complete', wait_for_deployment_complete_v2):
            self.assertTrue(conduct_deploy.deploy(input_args))

        bintray_deploy.assert_not_called()
        bundle_deploy.assert_called_once_with(input_args)
        wait_for_deployment_complete_v3.assert_not_called()
        wait_for_deployment_complete_v2.assert_not_called()

    def test_success_deploy_webhook_v3(self):
        bintray_deploy = self.respond_with(200, self.deployment_batch_json, content_type='application/json')
        bundle_deploy = MagicMock()

        wait_for_deployment_complete_v3 = MagicMock()
        wait_for_deployment_complete_v2 = MagicMock()

        args = self.args.copy()
        args.update({'webhook': 'bintray'})
        input_args = MagicMock(**args)

        with patch('conductr_cli.conduct_deploy_bintray.deploy', bintray_deploy), \
                patch('conductr_cli.conduct_deploy_bundle.deploy', bundle_deploy), \
                patch('conductr_cli.bundle_deploy_v3.wait_for_deployment_complete', wait_for_deployment_complete_v3), \
                patch('conductr_cli.bundle_deploy_v2.wait_for_deployment_complete', wait_for_deployment_complete_v2):
            self.assertTrue(conduct_deploy.deploy(input_args))

        bintray_deploy.assert_called_once_with(input_args)
        bundle_deploy.assert_not_called()
        wait_for_deployment_complete_v3.assert_called_once_with(self.deployment_batch_id, input_args)
        wait_for_deployment_complete_v2.assert_not_called()

    def test_success_deploy_webhook_v2(self):
        deployment_id = 'deployment-id'

        bintray_deploy = self.respond_with(200, deployment_id, content_type='text/plain')
        bundle_deploy = MagicMock()

        wait_for_deployment_complete_v3 = MagicMock()
        wait_for_deployment_complete_v2 = MagicMock()

        args = self.args.copy()
        args.update({'webhook': 'bintray'})
        input_args = MagicMock(**args)

        with patch('conductr_cli.conduct_deploy_bintray.deploy', bintray_deploy), \
                patch('conductr_cli.conduct_deploy_bundle.deploy', bundle_deploy), \
                patch('conductr_cli.bundle_deploy_v3.wait_for_deployment_complete', wait_for_deployment_complete_v3), \
                patch('conductr_cli.bundle_deploy_v2.wait_for_deployment_complete', wait_for_deployment_complete_v2):
            self.assertTrue(conduct_deploy.deploy(input_args))

        bintray_deploy.assert_called_once_with(input_args)
        bundle_deploy.assert_not_called()
        wait_for_deployment_complete_v3.assert_not_called()
        wait_for_deployment_complete_v2.assert_called_once_with(deployment_id, input_args)

    def test_failure_deploy_bundle(self):
        bintray_deploy = MagicMock()
        bundle_deploy = MagicMock(return_value=False)

        wait_for_deployment_complete_v3 = MagicMock()
        wait_for_deployment_complete_v2 = MagicMock()

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.conduct_deploy_bintray.deploy', bintray_deploy), \
                patch('conductr_cli.conduct_deploy_bundle.deploy', bundle_deploy), \
                patch('conductr_cli.bundle_deploy_v3.wait_for_deployment_complete', wait_for_deployment_complete_v3), \
                patch('conductr_cli.bundle_deploy_v2.wait_for_deployment_complete', wait_for_deployment_complete_v2):
            self.assertFalse(conduct_deploy.deploy(input_args))

        bintray_deploy.assert_not_called()
        bundle_deploy.assert_called_once_with(input_args)
        wait_for_deployment_complete_v3.assert_not_called()
        wait_for_deployment_complete_v2.assert_not_called()

    def test_failure_deploy_webhook(self):
        bintray_deploy = MagicMock(return_value=False)
        bundle_deploy = MagicMock()

        wait_for_deployment_complete_v3 = MagicMock()
        wait_for_deployment_complete_v2 = MagicMock()

        args = self.args.copy()
        args.update({'webhook': 'bintray'})
        input_args = MagicMock(**args)

        with patch('conductr_cli.conduct_deploy_bintray.deploy', bintray_deploy), \
                patch('conductr_cli.conduct_deploy_bundle.deploy', bundle_deploy), \
                patch('conductr_cli.bundle_deploy_v3.wait_for_deployment_complete', wait_for_deployment_complete_v3), \
                patch('conductr_cli.bundle_deploy_v2.wait_for_deployment_complete', wait_for_deployment_complete_v2):
            self.assertFalse(conduct_deploy.deploy(input_args))

        bintray_deploy.assert_called_once_with(input_args)
        bundle_deploy.assert_not_called()
        wait_for_deployment_complete_v3.assert_not_called()
        wait_for_deployment_complete_v2.assert_not_called()

    def test_error_wait_timeout(self):
        bintray_deploy = MagicMock()
        bundle_deploy = self.respond_with(200, self.deployment_batch_json, content_type='application/json')

        wait_for_deployment_complete_v3 = MagicMock(side_effect=WaitTimeoutError('test only'))
        wait_for_deployment_complete_v2 = MagicMock()

        input_args = MagicMock(**self.args)

        stdout = MagicMock()
        stderr = MagicMock()
        with patch('conductr_cli.conduct_deploy_bintray.deploy', bintray_deploy), \
                patch('conductr_cli.conduct_deploy_bundle.deploy', bundle_deploy), \
                patch('conductr_cli.bundle_deploy_v3.wait_for_deployment_complete', wait_for_deployment_complete_v3), \
                patch('conductr_cli.bundle_deploy_v2.wait_for_deployment_complete', wait_for_deployment_complete_v2):
            logging_setup.configure_logging(input_args, stdout, stderr)
            self.assertFalse(conduct_deploy.deploy(input_args))

        bintray_deploy.assert_not_called()
        bundle_deploy.assert_called_once_with(input_args)
        wait_for_deployment_complete_v3.assert_called_once_with(self.deployment_batch_id, input_args)
        wait_for_deployment_complete_v2.assert_not_called()

        self.assertEqual('', self.output(stdout))
        self.assertEqual(as_error('Error: Timed out: test only\n'), self.output(stderr))

    def test_error_unsupported_webhook(self):
        bintray_deploy = MagicMock()
        bundle_deploy = MagicMock()

        wait_for_deployment_complete_v3 = MagicMock()
        wait_for_deployment_complete_v2 = MagicMock()

        args = self.args.copy()
        args.update({'webhook': 'foo'})
        input_args = MagicMock(**args)

        stdout = MagicMock()
        stderr = MagicMock()

        with patch('conductr_cli.conduct_deploy_bintray.deploy', bintray_deploy), \
                patch('conductr_cli.conduct_deploy_bundle.deploy', bundle_deploy), \
                patch('conductr_cli.bundle_deploy_v3.wait_for_deployment_complete', wait_for_deployment_complete_v3), \
                patch('conductr_cli.bundle_deploy_v2.wait_for_deployment_complete', wait_for_deployment_complete_v2):
            logging_setup.configure_logging(input_args, stdout, stderr)
            self.assertFalse(conduct_deploy.deploy(input_args))

        bintray_deploy.assert_not_called()
        bundle_deploy.assert_not_called()
        wait_for_deployment_complete_v3.assert_not_called()
        wait_for_deployment_complete_v2.assert_not_called()

        self.assertEqual('', self.output(stdout))

        expected_error = as_error(strip_margin("""|Error: Unsupported webhook foo
                                                  |"""))
        self.assertEqual(expected_error, self.output(stderr))

    def test_error_connection_error(self):
        expected_error = as_error(strip_margin("""|Error: Unable to contact ConductR.
                                                  |Error: Reason: test only
                                                  |Error: Start the ConductR sandbox with: sandbox run IMAGE_VERSION
                                                  |"""))
        self.conduct_deploy_bundle_error_scenario(ConnectionError('test only'), expected_error)

    def test_error_http_error(self):
        expected_error = as_error(strip_margin("""|Error: 500 test only
                                                  |Error: test http error
                                                  |"""))
        self.conduct_deploy_bundle_error_scenario(HTTPError(response=MagicMock(reason='test only',
                                                                               text='test http error',
                                                                               status_code=500)),
                                                  expected_error)

    def test_error_invalid_config(self):
        expected_error = as_error(strip_margin("""|Error: Unable to parse bundle.conf.
                                                  |Error: test only.
                                                  |"""))
        self.conduct_deploy_bundle_error_scenario(ConfigException('test only'), expected_error)

    def test_error_no_file_url_error(self):
        expected_error = as_error(strip_margin("""|Error: File not found: test only
                                                  |"""))
        self.conduct_deploy_bundle_error_scenario(URLError('test only'), expected_error)

    def test_error_no_file_urllib_http_error(self):
        mock_file = MagicMock()
        expected_error = as_error(strip_margin("""|Error: Resource not found: url
                                                  |"""))
        self.conduct_deploy_bundle_error_scenario(urllib.error.HTTPError('url', 'code', 'msg', 'hdrs', mock_file),
                                                  expected_error)

    def test_error_bad_zip_file(self):
        expected_error = as_error(strip_margin("""|Error: Problem with the bundle: test only
                                                  |"""))
        self.conduct_deploy_bundle_error_scenario(BadZipFile('test only'), expected_error)

    def test_error_malformed_bundle(self):
        expected_error = as_error(strip_margin("""|Error: Problem with the bundle: test only
                                                  |"""))
        self.conduct_deploy_bundle_error_scenario(MalformedBundleError('test only'), expected_error)

    def test_error_bundle_resolution(self):
        expected_error = as_error(strip_margin("""|Error: test only
                                                  |"""))
        self.conduct_deploy_bundle_error_scenario(BundleResolutionError('test only', [], []), expected_error)

    def test_error_load_read_timeout(self):
        expected_error = as_error(strip_margin(
            """|Error: Timed out waiting for response from the server: test only
               |Error: One possible issue may be that there are not enough resources or machines with the roles that your bundle requires
               |"""))
        self.conduct_deploy_bundle_error_scenario(ReadTimeout('test only'), expected_error)

    def test_error_insecure_file_permissions(self):
        expected_error = as_error(strip_margin("""|Error: File permissions are not secure: test only
                                                  |Error: Please choose a file where only the owner has access, e.g. 700
                                                  |"""))
        self.conduct_deploy_bundle_error_scenario(InsecureFilePermissions('test only'), expected_error)

    def test_error_bintray_resolutions(self):
        expected_error = as_error(strip_margin("""|Error: test only
                                                  |"""))
        self.conduct_deploy_bundle_error_scenario(BintrayResolutionError('test only'), expected_error)

    def test_error_bintray_credentials_not_found(self):
        expected_error = as_error(strip_margin("""|Error: Nearly there! The ConductR artifacts are hosted on private Bintray repository.
                                                  |Error: It is therefore necessary to create a Bintray credentials file at test only
                                                  |Error: For more information how to setup the Lightbend Bintray credentials please follow:
                                                  |Error:   http://developers.lightbend.com/docs/reactive-platform/2.0/setup/setup-sbt.html
                                                  |"""))
        self.conduct_deploy_bundle_error_scenario(BintrayCredentialsNotFoundError('test only'), expected_error)

    def test_error_bintray_credentials_malformed(self):
        expected_error = as_error(strip_margin("""|Error: Malformed Bintray credentials in test only
                                                  |Error: Please follow the instructions to setup the Lightbend Bintray credentials:
                                                  |Error:   http://developers.lightbend.com/docs/reactive-platform/2.0/setup/setup-sbt.html
                                                  |"""))
        self.conduct_deploy_bundle_error_scenario(MalformedBintrayCredentialsError('test only'), expected_error)

    def conduct_deploy_bundle_error_scenario(self, error_raised, expected_stderr):
        bintray_deploy = MagicMock()
        bundle_deploy = MagicMock(side_effect=error_raised)

        wait_for_deployment_complete_v3 = MagicMock()
        wait_for_deployment_complete_v2 = MagicMock()

        input_args = MagicMock(**self.args)

        stdout = MagicMock()
        stderr = MagicMock()
        with patch('conductr_cli.conduct_deploy_bintray.deploy', bintray_deploy), \
                patch('conductr_cli.conduct_deploy_bundle.deploy', bundle_deploy), \
                patch('conductr_cli.bundle_deploy_v3.wait_for_deployment_complete', wait_for_deployment_complete_v3), \
                patch('conductr_cli.bundle_deploy_v2.wait_for_deployment_complete', wait_for_deployment_complete_v2):
            logging_setup.configure_logging(input_args, stdout, stderr)
            self.assertFalse(conduct_deploy.deploy(input_args))

        bintray_deploy.assert_not_called()
        bundle_deploy.assert_called_once_with(input_args)
        wait_for_deployment_complete_v3.assert_not_called()
        wait_for_deployment_complete_v2.assert_not_called()

        self.assertEqual('', self.output(stdout))
        self.assertEqual(expected_stderr, self.output(stderr))
