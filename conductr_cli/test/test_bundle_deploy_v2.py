from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import bundle_deploy_v2, logging_setup
from conductr_cli.exceptions import ContinuousDeliveryError, WaitTimeoutError
from unittest.mock import call, patch, MagicMock
import json


class TestGetDeploymentStateIp(CliTestCase):

    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')

    def test_success(self):
        deployment_state = strip_margin(
            """|[
               |  {
               |    "eventType": "deploymentStarted",
               |    "deploymentId": "abc-def",
               |    "bundleName": "cassandra",
               |    "compatibleVersion": "v1"
               |  }
               |]
               |""")
        http_method = self.respond_with(text=deployment_state)

        args = {
            'dcos_mode': False,
            'scheme': 'http',
            'ip': '127.0.0.1',
            'port': '9005',
            'base_path': '/',
            'api_version': '1',
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        }
        input_args = MagicMock(**args)
        with patch('requests.get', http_method):
            result = bundle_deploy_v2.get_deployment_events('abc-def', input_args)
            self.assertEqual(json.loads(deployment_state), result)

        http_method.assert_called_with('http://127.0.0.1:9005/deployments/abc-def', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})

    def test_return_none_if_404(self):
        http_method = self.respond_with(status_code=404)

        args = {
            'dcos_mode': False,
            'scheme': 'http',
            'ip': '127.0.0.1',
            'port': '9005',
            'base_path': '/',
            'api_version': '1',
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        }
        input_args = MagicMock(**args)
        with patch('requests.get', http_method):
            result = bundle_deploy_v2.get_deployment_events('abc-def', input_args)
            self.assertIsNone(result)

        http_method.assert_called_with('http://127.0.0.1:9005/deployments/abc-def', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})


class TestGetDeploymentStateHost(CliTestCase):

    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')

    def test_success(self):
        deployment_state = strip_margin(
            """|[
               |  {
               |    "eventType": "deploymentStarted",
               |    "deploymentId": "abc-def",
               |    "bundleName": "cassandra",
               |    "compatibleVersion": "v1"
               |  }
               |]
               |""")
        http_method = self.respond_with(text=deployment_state)

        args = {
            'dcos_mode': False,
            'scheme': 'http',
            'host': '127.0.0.1',
            'port': '9005',
            'base_path': '/',
            'api_version': '1',
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        }
        input_args = MagicMock(**args)
        with patch('requests.get', http_method):
            result = bundle_deploy_v2.get_deployment_events('abc-def', input_args)
            self.assertEqual(json.loads(deployment_state), result)

        http_method.assert_called_with('http://127.0.0.1:9005/deployments/abc-def', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})

    def test_return_none_if_404(self):
        http_method = self.respond_with(status_code=404)

        args = {
            'dcos_mode': False,
            'scheme': 'http',
            'host': '127.0.0.1',
            'port': '9005',
            'base_path': '/',
            'api_version': '1',
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        }
        input_args = MagicMock(**args)
        with patch('requests.get', http_method):
            result = bundle_deploy_v2.get_deployment_events('abc-def', input_args)
            self.assertIsNone(result)

        http_method.assert_called_with('http://127.0.0.1:9005/deployments/abc-def', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})


class TestWaitForDeployment(CliTestCase):
    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')

    def test_wait_for_deployment(self):
        get_deployment_events_mock = MagicMock(side_effect=[
            self.events([
                self.event('deploymentStarted')
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload')
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {
                    'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
                })
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {
                    'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
                }),
                self.event('load', {'configFileName': 'cassandra-prod-config.zip'})
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {
                    'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
                }),
                self.event('load', {'configFileName': 'cassandra-prod-config.zip'}),
                self.event('deploy', {
                    'bundleOld': {'scale': 1},
                    'bundleNew': {'scale': 0}
                })
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {
                    'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
                }),
                self.event('load', {'configFileName': 'cassandra-prod-config.zip'}),
                self.event('deploy', {
                    'bundleOld': {'scale': 1},
                    'bundleNew': {'scale': 0}
                }),
                self.event('deploy', {
                    'bundleOld': {'scale': 0},
                    'bundleNew': {'scale': 1}
                })
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {
                    'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
                }),
                self.event('load', {'configFileName': 'cassandra-prod-config.zip'}),
                self.event('deploy', {
                    'bundleOld': {'scale': 1},
                    'bundleNew': {'scale': 0}
                }),
                self.event('deploy', {
                    'bundleOld': {'scale': 0},
                    'bundleNew': {'scale': 1}
                }),
                self.event('deploymentSuccess')
            ]),
        ])
        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.sse(None),
            self.sse('deploymentStarted'),
            self.sse(None),
            self.sse('bundleDownload'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('configDownload'),
            self.sse('load'),
            self.sse(None),
            self.sse('deploy'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('deploy'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('deploymentSuccess')
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
                patch('conductr_cli.bundle_deploy_v2.get_deployment_events', get_deployment_events_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('sys.stdout.isatty', is_tty_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_deploy_v2.wait_for_deployment_complete(deployment_id, args)

        self.assertEqual(get_deployment_events_mock.call_args_list, [
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args)
        ])

        url_mock.assert_called_with('deployments/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/deployments/events', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        expected_log_message = strip_margin("""|Deployment id: a101449418187d92c789d1adc240b6d6
                                               |Downloading bundle
                                               |Downloading config from bundle abf6045-a53237c
                                               |Loading bundle with config
                                               |Deploying - 1 old instance vs 0 new instance
                                               |Deploying - 0 old instance vs 1 new instance
                                               |Success
                                               |""")
        self.assertEqual(self.output(stdout), expected_log_message)

    def test_wait_for_deployment_long_ids(self):
        get_deployment_events_mock = MagicMock(side_effect=[
            self.events([
                self.event('deploymentStarted')
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload')
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {
                    'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
                })
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {
                    'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
                }),
                self.event('load', {'configFileName': 'cassandra-prod-config.zip'})
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {
                    'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
                }),
                self.event('load', {'configFileName': 'cassandra-prod-config.zip'}),
                self.event('deploy', {
                    'bundleOld': {'scale': 1},
                    'bundleNew': {'scale': 0}
                })
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {
                    'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
                }),
                self.event('load', {'configFileName': 'cassandra-prod-config.zip'}),
                self.event('deploy', {
                    'bundleOld': {'scale': 1},
                    'bundleNew': {'scale': 0}
                }),
                self.event('deploy', {
                    'bundleOld': {'scale': 0},
                    'bundleNew': {'scale': 1}
                })
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {
                    'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
                }),
                self.event('load', {'configFileName': 'cassandra-prod-config.zip'}),
                self.event('deploy', {
                    'bundleOld': {'scale': 1},
                    'bundleNew': {'scale': 0}
                }),
                self.event('deploy', {
                    'bundleOld': {'scale': 0},
                    'bundleNew': {'scale': 1}
                }),
                self.event('deploymentSuccess')
            ]),
        ])
        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.sse(None),
            self.sse('deploymentStarted'),
            self.sse(None),
            self.sse('bundleDownload'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('configDownload'),
            self.sse('load'),
            self.sse(None),
            self.sse('deploy'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('deploy'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('deploymentSuccess')
        ])

        stdout = MagicMock()
        is_tty_mock = MagicMock(return_value=True)

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
                patch('conductr_cli.bundle_deploy_v2.get_deployment_events', get_deployment_events_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('sys.stdout.isatty', is_tty_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_deploy_v2.wait_for_deployment_complete(deployment_id, args)

        self.assertEqual(get_deployment_events_mock.call_args_list, [
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args)
        ])

        url_mock.assert_called_with('deployments/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/deployments/events', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        expected_log_message = strip_margin("""|Deployment id: a101449418187d92c789d1adc240b6d6
                                               |Downloading bundle
                                               |Downloading config from bundle abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de
                                               |Loading bundle with config
                                               |Deploying - 1 old instance vs 0 new instance
                                               |Deploying - 0 old instance vs 1 new instance
                                               |Success
                                               |""")
        self.assertEqual(self.output(stdout), expected_log_message)

    def test_return_immediately_if_deployment_is_successful(self):
        get_deployment_events_mock = MagicMock(side_effect=[
            self.events([
                self.event('deploymentSuccess')
            ]),
        ])
        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock()

        stdout = MagicMock()

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
                patch('conductr_cli.bundle_deploy_v2.get_deployment_events', get_deployment_events_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_deploy_v2.wait_for_deployment_complete(deployment_id, args)

        self.assertEqual(get_deployment_events_mock.call_args_list, [
            call(deployment_id, args)
        ])

        url_mock.assert_not_called()

        conductr_host_mock.assert_not_called()

        get_events_mock.assert_not_called()

        expected_log_message = strip_margin("""|Deployment id: a101449418187d92c789d1adc240b6d6
                                               |Success
                                               |""")
        self.assertEqual(self.output(stdout), expected_log_message)

    def test_fail_immediately_if_deployment_failed(self):
        get_deployment_events_mock = MagicMock(side_effect=[
            self.events([
                self.event('deploymentFailure', {'failure': 'test only'})
            ]),
        ])
        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock()

        stdout = MagicMock()
        stderr = MagicMock()

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
                patch('conductr_cli.bundle_deploy_v2.get_deployment_events', get_deployment_events_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                self.assertRaises(ContinuousDeliveryError):
            logging_setup.configure_logging(args, stdout, stderr)
            bundle_deploy_v2.wait_for_deployment_complete(deployment_id, args)

        self.assertEqual(get_deployment_events_mock.call_args_list, [
            call(deployment_id, args)
        ])

        url_mock.assert_not_called()

        conductr_host_mock.assert_not_called()

        get_events_mock.assert_not_called()

        expected_log_message = strip_margin("""|Deployment id: a101449418187d92c789d1adc240b6d6
                                               |""")
        self.assertEqual(self.output(stdout), expected_log_message)

    def test_wait_for_deployment_with_initial_deployment_not_found(self):
        get_deployment_events_mock = MagicMock(side_effect=[
            None,
            self.events([
                self.event('deploymentStarted')
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload')
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {
                    'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
                })
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {
                    'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
                }),
                self.event('load', {'configFileName': 'cassandra-prod-config.zip'})
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {
                    'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
                }),
                self.event('load', {'configFileName': 'cassandra-prod-config.zip'}),
                self.event('deploy', {
                    'bundleOld': {'scale': 1},
                    'bundleNew': {'scale': 0}
                })
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {
                    'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
                }),
                self.event('load', {'configFileName': 'cassandra-prod-config.zip'}),
                self.event('deploy', {
                    'bundleOld': {'scale': 1},
                    'bundleNew': {'scale': 0}
                }),
                self.event('deploy', {
                    'bundleOld': {'scale': 0},
                    'bundleNew': {'scale': 1}
                })
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {
                    'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
                }),
                self.event('load', {'configFileName': 'cassandra-prod-config.zip'}),
                self.event('deploy', {
                    'bundleOld': {'scale': 1},
                    'bundleNew': {'scale': 0}
                }),
                self.event('deploy', {
                    'bundleOld': {'scale': 0},
                    'bundleNew': {'scale': 1}
                }),
                self.event('deploymentSuccess')
            ]),
        ])
        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.sse(None),
            self.sse('deploymentStarted'),
            self.sse(None),
            self.sse('bundleDownload'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('configDownload'),
            self.sse('load'),
            self.sse(None),
            self.sse('deploy'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('deploy'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('deploymentSuccess')
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
                patch('conductr_cli.bundle_deploy_v2.get_deployment_events', get_deployment_events_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('sys.stdout.isatty', is_tty_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_deploy_v2.wait_for_deployment_complete(deployment_id, args)

        self.assertEqual(get_deployment_events_mock.call_args_list, [
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args)
        ])

        url_mock.assert_called_with('deployments/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/deployments/events', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        expected_log_message = strip_margin("""|Deployment id: a101449418187d92c789d1adc240b6d6
                                               |Deployment started
                                               |Downloading bundle
                                               |Downloading config from bundle abf6045-a53237c
                                               |Loading bundle with config
                                               |Deploying - 1 old instance vs 0 new instance
                                               |Deploying - 0 old instance vs 1 new instance
                                               |Success
                                               |""")
        self.assertEqual(self.output(stdout), expected_log_message)

    def test_deployment_completed_with_failure(self):
        get_deployment_events_mock = MagicMock(side_effect=[
            self.events([
                self.event('deploymentStarted')
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload')
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {
                    'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
                })
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {
                    'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
                }),
                self.event('load', {'configFileName': 'cassandra-prod-config.zip'})
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {
                    'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
                }),
                self.event('load', {'configFileName': 'cassandra-prod-config.zip'}),
                self.event('deploy', {
                    'bundleOld': {'scale': 1},
                    'bundleNew': {'scale': 0}
                })
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {
                    'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
                }),
                self.event('load', {'configFileName': 'cassandra-prod-config.zip'}),
                self.event('deploy', {
                    'bundleOld': {'scale': 1},
                    'bundleNew': {'scale': 0}
                }),
                self.event('deploy', {
                    'bundleOld': {'scale': 0},
                    'bundleNew': {'scale': 1}
                })
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {
                    'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
                }),
                self.event('load', {'configFileName': 'cassandra-prod-config.zip'}),
                self.event('deploy', {
                    'bundleOld': {'scale': 1},
                    'bundleNew': {'scale': 0}
                }),
                self.event('deploy', {
                    'bundleOld': {'scale': 0},
                    'bundleNew': {'scale': 1}
                }),
                self.event('deploymentFailure', {'failure': 'test only'})
            ]),
        ])
        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.sse(None),
            self.sse('deploymentStarted'),
            self.sse(None),
            self.sse('bundleDownload'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('configDownload'),
            self.sse('load'),
            self.sse(None),
            self.sse('deploy'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('deploy'),
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
                patch('conductr_cli.bundle_deploy_v2.get_deployment_events', get_deployment_events_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('sys.stdout.isatty', is_tty_mock), \
                self.assertRaises(ContinuousDeliveryError):
            logging_setup.configure_logging(args, stdout)
            bundle_deploy_v2.wait_for_deployment_complete(deployment_id, args)

        self.assertEqual(get_deployment_events_mock.call_args_list, [
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args),
            call(deployment_id, args)
        ])

        url_mock.assert_called_with('deployments/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/deployments/events', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        expected_log_message = strip_margin("""|Deployment id: a101449418187d92c789d1adc240b6d6
                                               |Downloading bundle
                                               |Downloading config from bundle abf6045-a53237c
                                               |Loading bundle with config
                                               |Deploying - 1 old instance vs 0 new instance
                                               |Deploying - 0 old instance vs 1 new instance
                                               |""")
        self.assertEqual(self.output(stdout), expected_log_message)

    def test_periodic_check_between_events(self):
        get_deployment_events_mock = MagicMock(return_value=self.events([self.event('deploymentStarted')]))
        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.sse(None),
            self.sse('deploymentStarted'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('bundleDownload')
        ])

        stdout = MagicMock()

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
                patch('conductr_cli.bundle_deploy_v2.get_deployment_events', get_deployment_events_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                self.assertRaises(WaitTimeoutError):
            logging_setup.configure_logging(args, stdout)
            bundle_deploy_v2.wait_for_deployment_complete(deployment_id, args)

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

    def test_wait_timeout(self):
        get_deployment_events_mock = MagicMock(side_effect=[
            self.events([
                self.event('deploymentStarted')
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload')
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {'compatibleBundleId': 'cassandra'})
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {'compatibleBundleId': 'cassandra'}),
                self.event('load', {'configFileName': 'cassandra-prod-config.zip'})
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {'compatibleBundleId': 'cassandra'}),
                self.event('load', {'configFileName': 'cassandra-prod-config.zip'}),
                self.event('deploy', {
                    'bundleOld': {'scale': 1},
                    'bundleNew': {'scale': 0}
                })
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {'compatibleBundleId': 'cassandra'}),
                self.event('load', {'configFileName': 'cassandra-prod-config.zip'}),
                self.event('deploy', {
                    'bundleOld': {'scale': 1},
                    'bundleNew': {'scale': 0}
                }),
                self.event('deploy', {
                    'bundleOld': {'scale': 0},
                    'bundleNew': {'scale': 1}
                })
            ]),
            self.events([
                self.event('deploymentStarted'),
                self.event('bundleDownload'),
                self.event('configDownload', {'compatibleBundleId': 'cassandra'}),
                self.event('load', {'configFileName': 'cassandra-prod-config.zip'}),
                self.event('deploy', {
                    'bundleOld': {'scale': 1},
                    'bundleNew': {'scale': 0}
                }),
                self.event('deploy', {
                    'bundleOld': {'scale': 0},
                    'bundleNew': {'scale': 1}
                }),
                self.event('deploymentFailure', {'failure': 'test only'})
            ]),
        ])
        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.sse(None),
            self.sse('deploymentStarted'),
            self.sse(None),
            self.sse('bundleDownload'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('configDownload'),
            self.sse('load'),
            self.sse(None),
            self.sse('deploy'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse('deploy'),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None)
        ])

        stdout = MagicMock()

        deployment_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = False
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'long_ids': False,
            # Purposely set no timeout to invoke the error
            'wait_timeout': -1,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file

        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.bundle_deploy_v2.get_deployment_events', get_deployment_events_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                self.assertRaises(WaitTimeoutError):
            logging_setup.configure_logging(args, stdout)
            bundle_deploy_v2.wait_for_deployment_complete(deployment_id, args)

        self.assertEqual(get_deployment_events_mock.call_args_list, [
            call(deployment_id, args)
        ])

        url_mock.assert_called_with('deployments/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/deployments/events', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

    def test_no_events(self):
        get_deployment_events_mock = MagicMock(side_effect=[
            self.events([
                self.event('deploymentStarted')
            ])
        ])
        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None),
            self.sse(None)
        ])

        stdout = MagicMock()

        deployment_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = False
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'long_ids': False,
            # Purposely set no timeout to invoke the error
            'wait_timeout': -1,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file

        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.bundle_deploy_v2.get_deployment_events', get_deployment_events_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                self.assertRaises(WaitTimeoutError):
            logging_setup.configure_logging(args, stdout)
            bundle_deploy_v2.wait_for_deployment_complete(deployment_id, args)

        self.assertEqual(get_deployment_events_mock.call_args_list, [
            call(deployment_id, args)
        ])

        url_mock.assert_called_with('deployments/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/deployments/events', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

    def sse(self, event_name):
        sse_mock = MagicMock()
        sse_mock.event = event_name
        return sse_mock

    def events(self, events):
        result = []

        for idx, event in enumerate(events):
            copy = event.copy()
            copy.update({'deploymentSequence': idx})
            result.append(copy)

        return result

    def event(self, event_type, data={}):
        result = {}
        result.update({
            'eventType': event_type
        })
        result.update(data)
        return result
