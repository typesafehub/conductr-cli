from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import bundle_deploy_v3, logging_setup
from conductr_cli.exceptions import ContinuousDeliveryError, WaitTimeoutError
from requests.exceptions import HTTPError
from unittest.mock import call, patch, MagicMock
import json


class TestGetBatchEvents(CliTestCase):
    dcos_mode = False
    host = '10.0.1.1'
    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock()

    input_args = {
        'dcos_mode': dcos_mode,
        'scheme': 'http',
        'host': host,
        'port': 9005,
        'base_path': '/',
        'api_version': '2',
        'conductr_auth': conductr_auth,
        'server_verification_file': server_verification_file
    }

    deployment_batch_id = 'test'

    def test_success(self):
        events = [
            {'eventType': 'test'}
        ]
        mock_get = self.respond_with(200, json.dumps(events), 'application/json')

        args = MagicMock(**self.input_args)

        with patch('conductr_cli.conduct_request.get', mock_get):
            result = bundle_deploy_v3.get_batch_events(self.deployment_batch_id, args)
            self.assertEqual(events, result)

        mock_get.assert_called_once_with(self.dcos_mode,
                                         self.host,
                                         'http://10.0.1.1:9005/v2/deployments/batches/{}'.format(self.deployment_batch_id),
                                         auth=self.conductr_auth,
                                         verify=self.server_verification_file)

    def test_return_none(self):
        mock_get = self.respond_with(404)

        args = MagicMock(**self.input_args)

        with patch('conductr_cli.conduct_request.get', mock_get):
            result = bundle_deploy_v3.get_batch_events(self.deployment_batch_id, args)
            self.assertIsNone(result)

        mock_get.assert_called_once_with(self.dcos_mode,
                                         self.host,
                                         'http://10.0.1.1:9005/v2/deployments/batches/{}'.format(self.deployment_batch_id),
                                         auth=self.conductr_auth,
                                         verify=self.server_verification_file)

    def test_raise_error(self):
        mock_get = self.respond_with(500)

        args = MagicMock(**self.input_args)

        with patch('conductr_cli.conduct_request.get', mock_get),\
                self.assertRaises(HTTPError):
            bundle_deploy_v3.get_batch_events(self.deployment_batch_id, args)

        mock_get.assert_called_once_with(self.dcos_mode,
                                         self.host,
                                         'http://10.0.1.1:9005/v2/deployments/batches/{}'.format(self.deployment_batch_id),
                                         auth=self.conductr_auth,
                                         verify=self.server_verification_file)


class TestGetDeploymentEvents(CliTestCase):
    dcos_mode = False
    host = '10.0.1.1'
    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock()

    input_args = {
        'dcos_mode': dcos_mode,
        'scheme': 'http',
        'host': host,
        'port': 9005,
        'base_path': '/',
        'api_version': '2',
        'conductr_auth': conductr_auth,
        'server_verification_file': server_verification_file
    }

    deployment_batch_id = 'test'

    def test_success(self):
        events = [
            {'eventType': 'test'}
        ]
        mock_get = self.respond_with(200, json.dumps(events), 'application/json')

        args = MagicMock(**self.input_args)

        with patch('conductr_cli.conduct_request.get', mock_get):
            result = bundle_deploy_v3.get_deployment_events(self.deployment_batch_id, args)
            self.assertEqual(events, result)

        mock_get.assert_called_once_with(
            self.dcos_mode,
            self.host,
            'http://10.0.1.1:9005/v2/deployments/batches/{}/deployments'.format(self.deployment_batch_id),
            auth=self.conductr_auth,
            verify=self.server_verification_file
        )

    def test_return_none(self):
        mock_get = self.respond_with(404)

        args = MagicMock(**self.input_args)

        with patch('conductr_cli.conduct_request.get', mock_get):
            result = bundle_deploy_v3.get_deployment_events(self.deployment_batch_id, args)
            self.assertIsNone(result)

        mock_get.assert_called_once_with(
            self.dcos_mode,
            self.host,
            'http://10.0.1.1:9005/v2/deployments/batches/{}/deployments'.format(self.deployment_batch_id),
            auth=self.conductr_auth,
            verify=self.server_verification_file
        )

    def test_raise_error(self):
        mock_get = self.respond_with(500)

        args = MagicMock(**self.input_args)

        with patch('conductr_cli.conduct_request.get', mock_get), \
                self.assertRaises(HTTPError):
            bundle_deploy_v3.get_deployment_events(self.deployment_batch_id, args)

        mock_get.assert_called_once_with(
            self.dcos_mode,
            self.host,
            'http://10.0.1.1:9005/v2/deployments/batches/{}/deployments'.format(self.deployment_batch_id),
            auth=self.conductr_auth,
            verify=self.server_verification_file
        )


class TestWaitForDeployment(CliTestCase):
    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')

    deployment_batch_id = 'batch-id'

    deployment_1_id = 'deployment-1'
    deployment_1_target_bundle = 'target-bundle-1'

    deployment_2_id = 'deployment-2'
    deployment_2_target_bundle = 'target-bundle-2'

    def test_wait_for_lock_step_deployment(self):
        get_batch_events_mock = MagicMock(side_effect=[
            self.batch_events([
                self.batch_event('requestAccepted'),
            ]),
            self.batch_events([
                self.batch_event('requestAccepted'),
                self.batch_event('scheduleLockStepDeployments', {
                    'scheduledDeployments': [
                        {
                            "deploymentKey": {
                                "deploymentBatchId": self.deployment_batch_id,
                                "deploymentId": self.deployment_1_id
                            },
                            "targetBundleId": self.deployment_1_target_bundle
                        },
                        {
                            "deploymentKey": {
                                "deploymentBatchId": self.deployment_batch_id,
                                "deploymentId": self.deployment_2_id
                            },
                            "targetBundleId": self.deployment_2_target_bundle
                        }
                    ]
                }),
            ]),
        ])

        get_deployment_events_mock = MagicMock(side_effect=[
            self.deployment_events([
                self.deployment_1_event('deploymentScheduled'),
                self.deployment_2_event('deploymentScheduled'),
            ]),
            self.deployment_events([
                self.deployment_1_event('deploymentScheduled'),
                self.deployment_2_event('deploymentScheduled'),
                self.deployment_1_event('deploymentSuccess'),
            ]),
            self.deployment_events([
                self.deployment_1_event('deploymentScheduled'),
                self.deployment_2_event('deploymentScheduled'),
                self.deployment_1_event('deploymentSuccess'),
                self.deployment_2_event('deploymentSuccess'),
            ]),
        ])

        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)

        stdout = MagicMock()
        is_tty_mock = MagicMock(return_value=True)

        get_events_mock = MagicMock(return_value=[
            self.sse(None),
            self.sse('requestAccepted'),
            self.sse(None),
            self.sse('scheduleDeployments'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('deploymentScheduled'),
            self.sse('deploymentScheduled'),
            self.sse(None),
            self.sse('deploymentSuccess'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('deploymentSuccess')
        ])

        deployment_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = False
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'long_ids': True,
            'wait_timeout': 10,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file

        })

        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.bundle_deploy_v3.get_batch_events', get_batch_events_mock), \
                patch('conductr_cli.bundle_deploy_v3.get_deployment_events', get_deployment_events_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('sys.stdout.isatty', is_tty_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_deploy_v3.wait_for_deployment_complete(deployment_id, args)

        self.assertEqual(get_batch_events_mock.call_args_list, [
            call(deployment_id, args),
            call(deployment_id, args)
        ])

        self.assertEqual(get_deployment_events_mock.call_args_list, [
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args)
        ])

        url_mock.assert_called_with('deployments/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/deployments/events', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        expected_log_message = strip_margin("""|Deployment batch id: a101449418187d92c789d1adc240b6d6
                                               |Targeting the following bundles
                                               |  target-bundle-1
                                               |  target-bundle-2
                                               |[target-bundle-1] Deployment scheduled
                                               |[target-bundle-2] Deployment scheduled
                                               |[target-bundle-1] Success
                                               |Success
                                               |""")
        self.assertEqual(self.output(stdout), expected_log_message)

    def test_wait_for_simple_deployment(self):
        get_batch_events_mock = MagicMock(side_effect=[
            self.batch_events([
                self.batch_event('requestAccepted'),
            ]),
            self.batch_events([
                self.batch_event('requestAccepted'),
            ]),
            self.batch_events([
                self.batch_event('requestAccepted'),
                self.batch_event('scheduleSimpleDeployment'),
            ]),
        ])

        get_deployment_events_mock = MagicMock(side_effect=[
            self.deployment_events([
                {
                    'eventType': 'deploymentScheduled',
                    'deploymentKey': {
                        'deploymentBatchId': self.deployment_batch_id,
                        'deploymentId': self.deployment_1_id,
                    },
                    'deploymentSequence': 0,
                    'timestamp': 101
                }
            ]),
            self.deployment_events([
                {
                    'eventType': 'deploymentScheduled',
                    'deploymentKey': {
                        'deploymentBatchId': self.deployment_batch_id,
                        'deploymentId': self.deployment_1_id,
                    },
                    'deploymentSequence': 0,
                    'timestamp': 101
                },
                {
                    'eventType': 'deploymentSuccess',
                    'deploymentKey': {
                        'deploymentBatchId': self.deployment_batch_id,
                        'deploymentId': self.deployment_1_id,
                    },
                    'deploymentSequence': 2,
                    'timestamp': 201
                }
            ]),
        ])

        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)

        stdout = MagicMock()
        is_tty_mock = MagicMock(return_value=True)

        get_events_mock = MagicMock(return_value=[
            self.sse('requestAccepted'),
            self.sse('scheduleSimpleDeployments'),
            self.sse('deploymentScheduled'),
            self.sse(None),
            self.sse(None),
            self.sse('deploymentSuccess')
        ])

        deployment_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = False
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'long_ids': True,
            'wait_timeout': 10,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file

        })

        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.bundle_deploy_v3.get_batch_events', get_batch_events_mock), \
                patch('conductr_cli.bundle_deploy_v3.get_deployment_events', get_deployment_events_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('sys.stdout.isatty', is_tty_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_deploy_v3.wait_for_deployment_complete(deployment_id, args)

        self.assertEqual(get_batch_events_mock.call_args_list, [
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args)
        ])

        self.assertEqual(get_deployment_events_mock.call_args_list, [
            call(deployment_id, args),
            call(deployment_id, args)
        ])

        url_mock.assert_called_with('deployments/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/deployments/events', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        expected_log_message = strip_margin("""|Deployment batch id: a101449418187d92c789d1adc240b6d6
                                               |Deployment request accepted
                                               |Deployment scheduled
                                               |Deployment scheduled
                                               |Success
                                               |""")
        self.assertEqual(self.output(stdout), expected_log_message)

    def test_return_immediately_if_deployment_failed(self):
        get_batch_events_mock = MagicMock(side_effect=[
            self.batch_events([
                self.batch_event('requestAccepted'),
            ]),
            self.batch_events([
                self.batch_event('requestAccepted'),
                self.batch_event('bundleDownload'),
            ]),
            self.batch_events([
                self.batch_event('requestAccepted'),
                self.batch_event('bundleDownload'),
                self.batch_event('deploymentFailure', {'failure': 'test only'}),
            ])
        ])

        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.sse(None),
            self.sse('requestAccepted'),
            self.sse(None),
            self.sse('bundleDownload'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('deploymentFailure')
        ])

        stdout = MagicMock()
        is_tty_mock = MagicMock(return_value=True)

        deployment_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = False
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'long_ids': False,
            'wait_timeout': 10,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file

        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.bundle_deploy_v3.get_batch_events', get_batch_events_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('sys.stdout.isatty', is_tty_mock), \
                self.assertRaises(ContinuousDeliveryError) as e:
            logging_setup.configure_logging(args, stdout)
            bundle_deploy_v3.wait_for_deployment_complete(deployment_id, args)

        self.assertEqual('Failure: test only', e.exception.value)
        self.assertEqual(get_batch_events_mock.call_args_list, [
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args)
        ])

        url_mock.assert_called_with('deployments/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/deployments/events', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        expected_log_message = strip_margin("""|Deployment batch id: a101449418187d92c789d1adc240b6d6
                                               |Downloading bundle
                                               |""")
        self.assertEqual(self.output(stdout), expected_log_message)

    def test_wait_for_deployment_with_initial_state_not_found(self):
        get_batch_events_mock = MagicMock(side_effect=[
            None,
            self.batch_events([
                self.batch_event('requestAccepted'),
            ]),
            self.batch_events([
                self.batch_event('requestAccepted'),
                self.batch_event('scheduleLockStepDeployments', {
                    'scheduledDeployments': [
                        {
                            "deploymentKey": {
                                "deploymentBatchId": self.deployment_batch_id,
                                "deploymentId": self.deployment_1_id
                            },
                            "targetBundleId": self.deployment_1_target_bundle
                        },
                        {
                            "deploymentKey": {
                                "deploymentBatchId": self.deployment_batch_id,
                                "deploymentId": self.deployment_2_id
                            },
                            "targetBundleId": self.deployment_2_target_bundle
                        }
                    ]
                }),
            ]),
        ])

        get_deployment_events_mock = MagicMock(side_effect=[
            None,
            self.deployment_events([
                self.deployment_1_event('deploymentScheduled'),
                self.deployment_2_event('deploymentScheduled'),
            ]),
            self.deployment_events([
                self.deployment_1_event('deploymentScheduled'),
                self.deployment_2_event('deploymentScheduled'),
                self.deployment_1_event('deploymentSuccess'),
            ]),
            self.deployment_events([
                self.deployment_1_event('deploymentScheduled'),
                self.deployment_2_event('deploymentScheduled'),
                self.deployment_1_event('deploymentSuccess'),
                self.deployment_2_event('deploymentSuccess'),
            ]),
        ])

        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)

        stdout = MagicMock()
        is_tty_mock = MagicMock(return_value=True)

        get_events_mock = MagicMock(return_value=[
            self.sse(None),
            self.sse('requestAccepted'),
            self.sse(None),
            self.sse('scheduleDeployments'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('deploymentScheduled'),
            self.sse('deploymentScheduled'),
            self.sse(None),
            self.sse('deploymentSuccess'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('deploymentSuccess')
        ])

        deployment_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = False
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'long_ids': True,
            'wait_timeout': 10,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file

        })

        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.bundle_deploy_v3.get_batch_events', get_batch_events_mock), \
                patch('conductr_cli.bundle_deploy_v3.get_deployment_events', get_deployment_events_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('sys.stdout.isatty', is_tty_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_deploy_v3.wait_for_deployment_complete(deployment_id, args)

        self.assertEqual(get_batch_events_mock.call_args_list, [
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args)
        ])

        self.assertEqual(get_deployment_events_mock.call_args_list, [
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args)
        ])

        url_mock.assert_called_with('deployments/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/deployments/events', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        expected_log_message = strip_margin("""|Deployment batch id: a101449418187d92c789d1adc240b6d6
                                               |Deployment request accepted
                                               |Targeting the following bundles
                                               |  target-bundle-1
                                               |  target-bundle-2
                                               |[target-bundle-1] Deployment scheduled
                                               |[target-bundle-2] Deployment scheduled
                                               |[target-bundle-1] Success
                                               |Success
                                               |""")
        self.assertEqual(self.output(stdout), expected_log_message)

    def test_deployment_batch_failure(self):
        get_batch_events_mock = MagicMock(side_effect=[
            None,
            self.batch_events([
                self.batch_event('requestAccepted'),
            ]),
            self.batch_events([
                self.batch_event('requestAccepted'),
                self.batch_event('deploymentFailure', {'failure': 'test only'}),
            ])
        ])

        get_deployment_events_mock = MagicMock()

        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)

        stdout = MagicMock()
        is_tty_mock = MagicMock(return_value=True)

        get_events_mock = MagicMock(return_value=[
            self.sse(None),
            self.sse('requestAccepted'),
            self.sse(None),
            self.sse('scheduleDeployments'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('deploymentScheduled'),
            self.sse('deploymentScheduled'),
            self.sse(None),
            self.sse('deploymentSuccess'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('deploymentSuccess')
        ])

        deployment_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = False
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'long_ids': True,
            'wait_timeout': 10,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file

        })

        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.bundle_deploy_v3.get_batch_events', get_batch_events_mock), \
                patch('conductr_cli.bundle_deploy_v3.get_deployment_events', get_deployment_events_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('sys.stdout.isatty', is_tty_mock), \
                self.assertRaises(ContinuousDeliveryError):
            logging_setup.configure_logging(args, stdout)
            bundle_deploy_v3.wait_for_deployment_complete(deployment_id, args)

        self.assertEqual(get_batch_events_mock.call_args_list, [
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args)
        ])

        get_deployment_events_mock.assert_not_called()

        url_mock.assert_called_with('deployments/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/deployments/events', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        expected_log_message = strip_margin("""|Deployment batch id: a101449418187d92c789d1adc240b6d6
                                               |Deployment request accepted
                                               |""")
        self.assertEqual(self.output(stdout), expected_log_message)

    def test_deployment_failure(self):
        get_batch_events_mock = MagicMock(side_effect=[
            self.batch_events([
                self.batch_event('requestAccepted'),
            ]),
            self.batch_events([
                self.batch_event('requestAccepted'),
                self.batch_event('scheduleLockStepDeployments', {
                    'scheduledDeployments': [
                        {
                            "deploymentKey": {
                                "deploymentBatchId": self.deployment_batch_id,
                                "deploymentId": self.deployment_1_id
                            },
                            "targetBundleId": self.deployment_1_target_bundle
                        },
                        {
                            "deploymentKey": {
                                "deploymentBatchId": self.deployment_batch_id,
                                "deploymentId": self.deployment_2_id
                            },
                            "targetBundleId": self.deployment_2_target_bundle
                        }
                    ]
                }),
            ]),
        ])

        get_deployment_events_mock = MagicMock(side_effect=[
            self.deployment_events([
                self.deployment_1_event('deploymentScheduled'),
                self.deployment_2_event('deploymentScheduled'),
            ]),
            self.deployment_events([
                self.deployment_1_event('deploymentScheduled'),
                self.deployment_2_event('deploymentScheduled'),
                self.deployment_1_event('deploymentFailure', {'failure': 'test only'}),
            ]),
        ])

        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)

        stdout = MagicMock()
        is_tty_mock = MagicMock(return_value=True)

        get_events_mock = MagicMock(return_value=[
            self.sse(None),
            self.sse('requestAccepted'),
            self.sse(None),
            self.sse('scheduleDeployments'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('deploymentScheduled'),
            self.sse('deploymentScheduled'),
            self.sse(None),
            self.sse('deploymentFailure'),
        ])

        deployment_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = False
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'long_ids': True,
            'wait_timeout': 10,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file

        })

        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.bundle_deploy_v3.get_batch_events', get_batch_events_mock), \
                patch('conductr_cli.bundle_deploy_v3.get_deployment_events', get_deployment_events_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('sys.stdout.isatty', is_tty_mock), \
                self.assertRaises(ContinuousDeliveryError):
            logging_setup.configure_logging(args, stdout)
            bundle_deploy_v3.wait_for_deployment_complete(deployment_id, args)

        self.assertEqual(get_batch_events_mock.call_args_list, [
            call(deployment_id, args),
            call(deployment_id, args)
        ])

        self.assertEqual(get_deployment_events_mock.call_args_list, [
            call(deployment_id, args),
            call(deployment_id, args)
        ])

        url_mock.assert_called_with('deployments/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/deployments/events', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        expected_log_message = strip_margin("""|Deployment batch id: a101449418187d92c789d1adc240b6d6
                                               |Targeting the following bundles
                                               |  target-bundle-1
                                               |  target-bundle-2
                                               |[target-bundle-1] Deployment scheduled
                                               |[target-bundle-2] Deployment scheduled
                                               |""")
        self.assertEqual(self.output(stdout), expected_log_message)

    def test_wait_timeout(self):
        get_batch_events_mock = MagicMock(side_effect=[
            self.batch_events([
                self.batch_event('requestAccepted'),
            ]),
            self.batch_events([
                self.batch_event('requestAccepted'),
                self.batch_event('scheduleLockStepDeployments', {
                    'scheduledDeployments': [
                        {
                            "deploymentKey": {
                                "deploymentBatchId": self.deployment_batch_id,
                                "deploymentId": self.deployment_1_id
                            },
                            "targetBundleId": self.deployment_1_target_bundle
                        },
                        {
                            "deploymentKey": {
                                "deploymentBatchId": self.deployment_batch_id,
                                "deploymentId": self.deployment_2_id
                            },
                            "targetBundleId": self.deployment_2_target_bundle
                        }
                    ]
                }),
            ]),
        ])

        get_deployment_events_mock = MagicMock(side_effect=[
            self.deployment_events([
                self.deployment_1_event('deploymentScheduled'),
                self.deployment_2_event('deploymentScheduled'),
            ]),
            self.deployment_events([
                self.deployment_1_event('deploymentScheduled'),
                self.deployment_2_event('deploymentScheduled'),
                self.deployment_1_event('deploymentSuccess'),
            ]),
            self.deployment_events([
                self.deployment_1_event('deploymentScheduled'),
                self.deployment_2_event('deploymentScheduled'),
                self.deployment_1_event('deploymentSuccess'),
                self.deployment_2_event('deploymentSuccess'),
            ]),
        ])

        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)

        stdout = MagicMock()
        is_tty_mock = MagicMock(return_value=True)

        get_events_mock = MagicMock(return_value=[
            self.sse(None),
            self.sse('requestAccepted'),
            self.sse(None),
            self.sse('scheduleDeployments'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('deploymentScheduled'),
            self.sse('deploymentScheduled'),
            self.sse(None),
            self.sse('deploymentSuccess'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('deploymentSuccess')
        ])

        deployment_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = False
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'long_ids': True,
            'wait_timeout': -1,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file

        })

        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.bundle_deploy_v3.get_batch_events', get_batch_events_mock), \
                patch('conductr_cli.bundle_deploy_v3.get_deployment_events', get_deployment_events_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('sys.stdout.isatty', is_tty_mock),\
                self.assertRaises(WaitTimeoutError):
            logging_setup.configure_logging(args, stdout)
            bundle_deploy_v3.wait_for_deployment_complete(deployment_id, args)

        self.assertEqual(get_batch_events_mock.call_args_list, [
            call(deployment_id, args),
        ])

        get_deployment_events_mock.assert_not_called()

        url_mock.assert_called_with('deployments/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/deployments/events', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        expected_log_message = strip_margin("""|Deployment batch id: a101449418187d92c789d1adc240b6d6
                                               |""")
        self.assertEqual(self.output(stdout), expected_log_message)

    def sse(self, event_name):
        sse_mock = MagicMock()
        sse_mock.event = event_name
        return sse_mock

    def batch_events(self, events):
        result = []

        for idx, event in enumerate(events):
            copy = event.copy()
            copy.update({'deploymentBatchSequence': idx})
            result.append(copy)

        return result

    def batch_event(self, event_type, data={}):
        result = {}
        result.update({
            'eventType': event_type,
            'deploymentBatchId': self.deployment_batch_id
        })
        result.update(data)
        return result

    def deployment_events(self, events):
        # Append timestamp
        timestamp = 0
        events_with_timestamp = []
        for event in events:
            copy = event.copy()
            copy.update({'timestamp': timestamp})
            timestamp += 1
            events_with_timestamp.append(copy)

        # Append deployment sequence for each deployment
        entries_by_deployment_id = {}
        sequence = 0
        for event in events_with_timestamp:
            deployment_id = event['deploymentKey']['deploymentId']

            if deployment_id not in entries_by_deployment_id:
                entries_by_deployment_id[deployment_id] = []
                sequence = 0

            copy = event.copy()
            copy.update({'deploymentSequence': sequence})
            entries_by_deployment_id[deployment_id].append(copy)
            sequence += 1

        # Return as expected structure from the get deployment endpoint
        result = []
        for deployment_id in entries_by_deployment_id:
            events = entries_by_deployment_id[deployment_id]
            result.append({
                'deploymentKey': '{}-{}'.format(self.deployment_batch_id, deployment_id),
                'events': events
            })

        return result

    def deployment_event(self, deployment_id, target_bundle_id, event_type, data={}):
        result = {}
        result.update({
            'eventType': event_type,
            'deploymentKey': {
                'deploymentBatchId': self.deployment_batch_id,
                'deploymentId': deployment_id,
            },
            'deploymentTarget': {
                'bundleId': target_bundle_id
            }
        })
        result.update(data)
        return result

    def deployment_1_event(self, event_type, data={}):
        return self.deployment_event(self.deployment_1_id, self.deployment_1_target_bundle, event_type, data)

    def deployment_2_event(self, event_type, data={}):
        return self.deployment_event(self.deployment_2_id, self.deployment_2_target_bundle, event_type, data)


class TestDisplayBatchEvent(CliTestCase):
    def test_display(self):
        self.assertEqual('Deployment request accepted',
                         bundle_deploy_v3.display_batch_event({'eventType': 'requestAccepted'}))
        self.assertEqual('Downloading bundle',
                         bundle_deploy_v3.display_batch_event({'eventType': 'bundleDownload'}))
        self.assertEqual('Resolving compatible bundle',
                         bundle_deploy_v3.display_batch_event({'eventType': 'resolveCompatibleBundle'}))
        self.assertEqual('Failure: test',
                         bundle_deploy_v3.display_batch_event({'eventType': 'deploymentFailure', 'failure': 'test'}))
        self.assertEqual('Batch event {\'eventType\': \'unknown\'}',
                         bundle_deploy_v3.display_batch_event({'eventType': 'unknown'}))


class TestDisplayDeployEvent(CliTestCase):
    def test_display(self):
        bundle_id = '45e0c477d3e5ea92aa8d85c0d8f3e25c'
        args = MagicMock(**{'long_ids': False})

        self.assertEqual('[45e0c47] Deployment scheduled',
                         bundle_deploy_v3.display_deploy_event(args,
                                                               self.create_event('deploymentScheduled', bundle_id)))

        self.assertEqual('Deployment scheduled',
                         bundle_deploy_v3.display_deploy_event(args,
                                                               self.create_event('deploymentScheduled')))

        self.assertEqual('[45e0c47] Deployment started',
                         bundle_deploy_v3.display_deploy_event(args,
                                                               self.create_event('deploymentStarted', bundle_id)))

        self.assertEqual('Deployment started',
                         bundle_deploy_v3.display_deploy_event(args,
                                                               self.create_event('deploymentStarted')))

        self.assertEqual('[45e0c47] Downloading config',
                         bundle_deploy_v3.display_deploy_event(args,
                                                               self.create_event('configDownload', bundle_id)))

        self.assertEqual('[45e0c47] Deploying - 1 old instance vs 0 new instance',
                         bundle_deploy_v3.display_deploy_event(args,
                                                               self.create_event('deployLockStep',
                                                                                 bundle_id,
                                                                                 {
                                                                                     'bundleOld': {'scale': 1},
                                                                                     'bundleNew': {'scale': 0},
                                                                                 })))
        self.assertEqual('Deploying new instance',
                         bundle_deploy_v3.display_deploy_event(args,
                                                               self.create_event('deploySimple',
                                                                                 deployment_target=None,
                                                                                 props={
                                                                                     'bundleNew': {'scale': 0},
                                                                                 })))
        self.assertEqual('[45e0c47] Success',
                         bundle_deploy_v3.display_deploy_event(args,
                                                               self.create_event('deploymentSuccess', bundle_id)))

        self.assertEqual('Success',
                         bundle_deploy_v3.display_deploy_event(args,
                                                               self.create_event('deploymentSuccess')))

        self.assertEqual('[45e0c47] Failure: test only',
                         bundle_deploy_v3.display_deploy_event(args,
                                                               self.create_event('deploymentFailure',
                                                                                 bundle_id,
                                                                                 {
                                                                                     'failure': 'test only'
                                                                                 })))

    def create_event(self, event_type, deployment_target=None, props={}):
        result = {'eventType': event_type}
        if deployment_target:
            result.update({
                'deploymentTarget': {
                    'bundleId': deployment_target
                }
            })
        result.update(props)
        return result
