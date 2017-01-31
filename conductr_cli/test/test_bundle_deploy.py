from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import bundle_deploy, logging_setup
from conductr_cli.exceptions import ContinuousDeliveryError, WaitTimeoutError
from conductr_cli.resolvers import bintray_resolver
from unittest import TestCase
from unittest.mock import call, patch, MagicMock

import json


class TestGenerateHmac(TestCase):
    def test_success(self):
        result = bundle_deploy.generate_hmac_signature('secret', 'reactive-maps-backend-summary')
        self.assertEqual('2un791uBDf59/fHrIOWMqt0mhwEoH0yqkZXmz//4alQ=', result)


class TestGetDeploymentStateIp(CliTestCase):

    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')

    def test_success(self):
        deployment_state = strip_margin(
            """|{
               |  "eventType": "deploymentStarted",
               |  "deploymentId": "abc-def",
               |  "bundleName": "cassandra",
               |  "compatibleVersion": "v1"
               |}
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
            result = bundle_deploy.get_deployment_state('abc-def', input_args)
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
            result = bundle_deploy.get_deployment_state('abc-def', input_args)
            self.assertIsNone(result)

        http_method.assert_called_with('http://127.0.0.1:9005/deployments/abc-def', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})


class TestGetDeploymentStateHost(CliTestCase):

    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')

    def test_success(self):
        deployment_state = strip_margin(
            """|{
               |  "eventType": "deploymentStarted",
               |  "deploymentId": "abc-def",
               |  "bundleName": "cassandra",
               |  "compatibleVersion": "v1"
               |}
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
            result = bundle_deploy.get_deployment_state('abc-def', input_args)
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
            result = bundle_deploy.get_deployment_state('abc-def', input_args)
            self.assertIsNone(result)

        http_method.assert_called_with('http://127.0.0.1:9005/deployments/abc-def', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})


class TestWaitForDeployment(CliTestCase):
    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')

    def test_wait_for_deployment(self):
        get_deployment_state_mock = MagicMock(side_effect=[
            self.create_deployment_state('deploymentStarted'),
            self.create_deployment_state('bundleDownload'),
            self.create_deployment_state('configDownload', {
                'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
            }),
            self.create_deployment_state('load', {'configFileName': 'cassandra-prod-config.zip'}),
            self.create_deployment_state('deploy', {
                'bundleOld': {'scale': 1},
                'bundleNew': {'scale': 0}
            }),
            self.create_deployment_state('deploy', {
                'bundleOld': {'scale': 0},
                'bundleNew': {'scale': 1}
            }),
            self.create_deployment_state('deploymentSuccess'),
        ])
        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.create_test_event(None),
            self.create_test_event('deploymentStarted'),
            self.create_test_event(None),
            self.create_test_event('bundleDownload'),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event('configDownload'),
            self.create_test_event('load'),
            self.create_test_event(None),
            self.create_test_event('deploy'),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event('deploy'),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event('deploymentSuccess')
        ])

        stdout = MagicMock()

        deployment_id = 'a101449418187d92c789d1adc240b6d6'
        resolved_version = {
            'org': 'typesafe',
            'repo': 'bundle',
            'package_name': 'cassandra',
            'compatibility_version': 'v1',
            'digest': 'd073991ab918ee22c7426af8a62a48c5-a53237c1f4a067e13ef00090627fb3de',
            'resolver': bintray_resolver.__name__
        }
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
                patch('conductr_cli.bundle_deploy.get_deployment_state', get_deployment_state_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_deploy.wait_for_deployment_complete(deployment_id, resolved_version, args)

        self.assertEqual(get_deployment_state_mock.call_args_list, [
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

        self.assertEqual(stdout.method_calls, [
            call.write('Deploying cassandra:v1-d073991-a53237c'),
            call.write('\n'),
            call.flush(),
            call.write('Downloading bundle\r'),
            call.write(''),
            call.flush(),
            call.write('Downloading bundle\n'),
            call.write(''),
            call.flush(),
            call.write('Downloading config from bundle abf6045-a53237c\r'),
            call.write(''),
            call.flush(),
            call.write('Downloading config from bundle abf6045-a53237c\n'),
            call.write(''),
            call.flush(),
            call.write('Loading bundle with config\r'),
            call.write(''),
            call.flush(),
            call.write('Loading bundle with config\n'),
            call.write(''),
            call.flush(),
            call.write('Deploying - 1 old instance vs 0 new instance\r'),
            call.write(''),
            call.flush(),
            call.write('Deploying - 1 old instance vs 0 new instance\n'),
            call.write(''),
            call.flush(),
            call.write('Deploying - 0 old instance vs 1 new instance\r'),
            call.write(''),
            call.flush(),
            call.write('Deploying - 0 old instance vs 1 new instance\n'),
            call.write(''),
            call.flush(),
            call.write('Success'),
            call.write('\n'),
            call.flush()
        ])

    def test_wait_for_deployment_long_ids(self):
        get_deployment_state_mock = MagicMock(side_effect=[
            self.create_deployment_state('deploymentStarted'),
            self.create_deployment_state('bundleDownload'),
            self.create_deployment_state('configDownload', {
                'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
            }),
            self.create_deployment_state('load', {'configFileName': 'cassandra-prod-config.zip'}),
            self.create_deployment_state('deploy', {
                'bundleOld': {'scale': 1},
                'bundleNew': {'scale': 0}
            }),
            self.create_deployment_state('deploy', {
                'bundleOld': {'scale': 0},
                'bundleNew': {'scale': 1}
            }),
            self.create_deployment_state('deploymentSuccess'),
        ])
        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.create_test_event(None),
            self.create_test_event('deploymentStarted'),
            self.create_test_event(None),
            self.create_test_event('bundleDownload'),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event('configDownload'),
            self.create_test_event('load'),
            self.create_test_event(None),
            self.create_test_event('deploy'),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event('deploy'),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event('deploymentSuccess')
        ])

        stdout = MagicMock()

        deployment_id = 'a101449418187d92c789d1adc240b6d6'
        resolved_version = {
            'org': 'typesafe',
            'repo': 'bundle',
            'package_name': 'cassandra',
            'compatibility_version': 'v1',
            'digest': 'd073991ab918ee22c7426af8a62a48c5-a53237c1f4a067e13ef00090627fb3de',
            'resolver': bintray_resolver.__name__
        }
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
                patch('conductr_cli.bundle_deploy.get_deployment_state', get_deployment_state_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_deploy.wait_for_deployment_complete(deployment_id, resolved_version, args)

        self.assertEqual(get_deployment_state_mock.call_args_list, [
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

        self.assertEqual(stdout.method_calls, [
            call.write('Deploying cassandra:v1-d073991ab918ee22c7426af8a62a48c5-a53237c1f4a067e13ef00090627fb3de'),
            call.write('\n'),
            call.flush(),
            call.write('Downloading bundle\r'),
            call.write(''),
            call.flush(),
            call.write('Downloading bundle\n'),
            call.write(''),
            call.flush(),
            call.write('Downloading config from bundle abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de\r'),
            call.write(''),
            call.flush(),
            call.write('Downloading config from bundle abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de\n'),
            call.write(''),
            call.flush(),
            call.write('Loading bundle with config\r'),
            call.write(''),
            call.flush(),
            call.write('Loading bundle with config\n'),
            call.write(''),
            call.flush(),
            call.write('Deploying - 1 old instance vs 0 new instance\r'),
            call.write(''),
            call.flush(),
            call.write('Deploying - 1 old instance vs 0 new instance\n'),
            call.write(''),
            call.flush(),
            call.write('Deploying - 0 old instance vs 1 new instance\r'),
            call.write(''),
            call.flush(),
            call.write('Deploying - 0 old instance vs 1 new instance\n'),
            call.write(''),
            call.flush(),
            call.write('Success'),
            call.write('\n'),
            call.flush()
        ])

    def test_return_immediately_if_deployment_is_successful(self):
        get_deployment_state_mock = MagicMock(side_effect=[
            self.create_deployment_state('deploymentSuccess'),
        ])
        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock()

        stdout = MagicMock()

        deployment_id = 'a101449418187d92c789d1adc240b6d6'
        resolved_version = {
            'org': 'typesafe',
            'repo': 'bundle',
            'package_name': 'cassandra',
            'compatibility_version': 'v1',
            'digest': 'abcdef',
            'resolver': bintray_resolver.__name__
        }
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
                patch('conductr_cli.bundle_deploy.get_deployment_state', get_deployment_state_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_deploy.wait_for_deployment_complete(deployment_id, resolved_version, args)

        self.assertEqual(get_deployment_state_mock.call_args_list, [
            call(deployment_id, args)
        ])

        url_mock.assert_not_called()

        conductr_host_mock.assert_not_called()

        get_events_mock.assert_not_called()

        self.assertEqual(stdout.method_calls, [
            call.write('Deploying cassandra:v1-abcdef'),
            call.write('\n'),
            call.flush(),
            call.write('Success'),
            call.write('\n'),
            call.flush()
        ])

    def test_fail_immediately_if_deployment_failed(self):
        get_deployment_state_mock = MagicMock(side_effect=[
            self.create_deployment_state('deploymentFailure', {'failure': 'test only'}),
        ])
        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock()

        stdout = MagicMock()
        stderr = MagicMock()

        deployment_id = 'a101449418187d92c789d1adc240b6d6'
        resolved_version = {
            'org': 'typesafe',
            'repo': 'bundle',
            'package_name': 'cassandra',
            'compatibility_version': 'v1',
            'digest': 'abcdef',
            'resolver': bintray_resolver.__name__
        }
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
                patch('conductr_cli.bundle_deploy.get_deployment_state', get_deployment_state_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout, stderr)
            self.assertRaises(ContinuousDeliveryError, bundle_deploy.wait_for_deployment_complete, deployment_id,
                              resolved_version, args)

        self.assertEqual(get_deployment_state_mock.call_args_list, [
            call(deployment_id, args)
        ])

        url_mock.assert_not_called()

        conductr_host_mock.assert_not_called()

        get_events_mock.assert_not_called()

        self.assertEqual(stdout.method_calls, [
            call.write('Deploying cassandra:v1-abcdef'),
            call.write('\n'),
            call.flush()
        ])

    def test_wait_for_deployment_with_initial_deployment_not_found(self):
        get_deployment_state_mock = MagicMock(side_effect=[
            None,
            self.create_deployment_state('deploymentStarted'),
            self.create_deployment_state('bundleDownload'),
            self.create_deployment_state('configDownload', {
                'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
            }),
            self.create_deployment_state('load', {'configFileName': 'cassandra-prod-config.zip'}),
            self.create_deployment_state('deploy', {
                'bundleOld': {'scale': 1},
                'bundleNew': {'scale': 0}
            }),
            self.create_deployment_state('deploy', {
                'bundleOld': {'scale': 0},
                'bundleNew': {'scale': 1}
            }),
            self.create_deployment_state('deploymentSuccess'),
        ])
        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.create_test_event(None),
            self.create_test_event('deploymentStarted'),
            self.create_test_event(None),
            self.create_test_event('bundleDownload'),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event('configDownload'),
            self.create_test_event('load'),
            self.create_test_event(None),
            self.create_test_event('deploy'),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event('deploy'),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event('deploymentSuccess')
        ])

        stdout = MagicMock()

        deployment_id = 'a101449418187d92c789d1adc240b6d6'
        resolved_version = {
            'org': 'typesafe',
            'repo': 'bundle',
            'package_name': 'cassandra',
            'compatibility_version': 'v1',
            'digest': 'abcdef',
            'resolver': bintray_resolver.__name__
        }
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
                patch('conductr_cli.bundle_deploy.get_deployment_state', get_deployment_state_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_deploy.wait_for_deployment_complete(deployment_id, resolved_version, args)

        self.assertEqual(get_deployment_state_mock.call_args_list, [
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

        self.assertEqual(stdout.method_calls, [
            call.write('Deploying cassandra:v1-abcdef'),
            call.write('\n'),
            call.flush(),
            call.write('Deployment started\r'),
            call.write(''),
            call.flush(),
            call.write('Deployment started\n'),
            call.write(''),
            call.flush(),
            call.write('Downloading bundle\r'),
            call.write(''),
            call.flush(),
            call.write('Downloading bundle\n'),
            call.write(''),
            call.flush(),
            call.write('Downloading config from bundle abf6045-a53237c\r'),
            call.write(''),
            call.flush(),
            call.write('Downloading config from bundle abf6045-a53237c\n'),
            call.write(''),
            call.flush(),
            call.write('Loading bundle with config\r'),
            call.write(''),
            call.flush(),
            call.write('Loading bundle with config\n'),
            call.write(''),
            call.flush(),
            call.write('Deploying - 1 old instance vs 0 new instance\r'),
            call.write(''),
            call.flush(),
            call.write('Deploying - 1 old instance vs 0 new instance\n'),
            call.write(''),
            call.flush(),
            call.write('Deploying - 0 old instance vs 1 new instance\r'),
            call.write(''),
            call.flush(),
            call.write('Deploying - 0 old instance vs 1 new instance\n'),
            call.write(''),
            call.flush(),
            call.write('Success'),
            call.write('\n'),
            call.flush()
        ])

    def test_deployment_completed_with_failure(self):
        get_deployment_state_mock = MagicMock(side_effect=[
            self.create_deployment_state('deploymentStarted'),
            self.create_deployment_state('bundleDownload'),
            self.create_deployment_state('configDownload', {
                'compatibleBundleId': 'abf60451c6af18adcc851d67b369b7f5-a53237c1f4a067e13ef00090627fb3de'
            }),
            self.create_deployment_state('load', {'configFileName': 'cassandra-prod-config.zip'}),
            self.create_deployment_state('deploy', {
                'bundleOld': {'scale': 1},
                'bundleNew': {'scale': 0}
            }),
            self.create_deployment_state('deploy', {
                'bundleOld': {'scale': 0},
                'bundleNew': {'scale': 1}
            }),
            self.create_deployment_state('deploymentFailure', {'failure': 'test only'}),
        ])
        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.create_test_event(None),
            self.create_test_event('deploymentStarted'),
            self.create_test_event(None),
            self.create_test_event('bundleDownload'),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event('configDownload'),
            self.create_test_event('load'),
            self.create_test_event(None),
            self.create_test_event('deploy'),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event('deploy'),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event('deploymentFailure')
        ])

        stdout = MagicMock()

        deployment_id = 'a101449418187d92c789d1adc240b6d6'
        resolved_version = {
            'org': 'typesafe',
            'repo': 'bundle',
            'package_name': 'cassandra',
            'compatibility_version': 'v1',
            'digest': 'abcdef',
            'resolver': bintray_resolver.__name__
        }
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
                patch('conductr_cli.bundle_deploy.get_deployment_state', get_deployment_state_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            self.assertRaises(ContinuousDeliveryError, bundle_deploy.wait_for_deployment_complete, deployment_id,
                              resolved_version, args)

        self.assertEqual(get_deployment_state_mock.call_args_list, [
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

        self.assertEqual(stdout.method_calls, [
            call.write('Deploying cassandra:v1-abcdef'),
            call.write('\n'),
            call.flush(),
            call.write('Downloading bundle\r'),
            call.write(''),
            call.flush(),
            call.write('Downloading bundle\n'),
            call.write(''),
            call.flush(),
            call.write('Downloading config from bundle abf6045-a53237c\r'),
            call.write(''),
            call.flush(),
            call.write('Downloading config from bundle abf6045-a53237c\n'),
            call.write(''),
            call.flush(),
            call.write('Loading bundle with config\r'),
            call.write(''),
            call.flush(),
            call.write('Loading bundle with config\n'),
            call.write(''),
            call.flush(),
            call.write('Deploying - 1 old instance vs 0 new instance\r'),
            call.write(''),
            call.flush(),
            call.write('Deploying - 1 old instance vs 0 new instance\n'),
            call.write(''),
            call.flush(),
            call.write('Deploying - 0 old instance vs 1 new instance\r'),
            call.write(''),
            call.flush(),
            call.write('Deploying - 0 old instance vs 1 new instance\n'),
            call.write(''),
            call.flush()
        ])

    def test_periodic_check_between_events(self):
        get_deployment_state_mock = MagicMock(return_value=self.create_deployment_state('deploymentStarted'))
        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.create_test_event(None),
            self.create_test_event('deploymentStarted'),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event('bundleDownload')
        ])

        stdout = MagicMock()

        deployment_id = 'a101449418187d92c789d1adc240b6d6'
        resolved_version = {
            'org': 'typesafe',
            'repo': 'bundle',
            'package_name': 'cassandra',
            'compatibility_version': 'v1',
            'digest': 'abcdef',
            'resolver': bintray_resolver.__name__
        }
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
                patch('conductr_cli.bundle_deploy.get_deployment_state', get_deployment_state_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            self.assertRaises(WaitTimeoutError, bundle_deploy.wait_for_deployment_complete,
                              deployment_id, resolved_version, args)

        self.assertEqual(get_deployment_state_mock.call_args_list, [
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
        get_deployment_state_mock = MagicMock(side_effect=[
            self.create_deployment_state('deploymentStarted'),
            self.create_deployment_state('bundleDownload'),
            self.create_deployment_state('configDownload', {'compatibleBundleId': 'cassandra'}),
            self.create_deployment_state('load', {'configFileName': 'cassandra-prod-config.zip'}),
            self.create_deployment_state('deploy', {
                'bundleOld': {'scale': 1},
                'bundleNew': {'scale': 0}
            }),
            self.create_deployment_state('deploy', {
                'bundleOld': {'scale': 0},
                'bundleNew': {'scale': 1}
            }),
            self.create_deployment_state('deploymentFailure', {'failure': 'test only'}),
        ])
        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.create_test_event(None),
            self.create_test_event('deploymentStarted'),
            self.create_test_event(None),
            self.create_test_event('bundleDownload'),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event('configDownload'),
            self.create_test_event('load'),
            self.create_test_event(None),
            self.create_test_event('deploy'),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event('deploy'),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None)
        ])

        stdout = MagicMock()

        deployment_id = 'a101449418187d92c789d1adc240b6d6'
        resolved_version = {
            'org': 'typesafe',
            'repo': 'bundle',
            'package_name': 'cassandra',
            'compatibility_version': 'v1',
            'digest': 'abcdef',
            'resolver': bintray_resolver.__name__
        }
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
                patch('conductr_cli.bundle_deploy.get_deployment_state', get_deployment_state_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            self.assertRaises(WaitTimeoutError, bundle_deploy.wait_for_deployment_complete, deployment_id,
                              resolved_version, args)

        self.assertEqual(get_deployment_state_mock.call_args_list, [
            call(deployment_id, args)
        ])

        url_mock.assert_called_with('deployments/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/deployments/events', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

    def test_no_events(self):
        get_deployment_state_mock = MagicMock(side_effect=[
            self.create_deployment_state('deploymentStarted')
        ])
        url_mock = MagicMock(return_value='/deployments/events')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None)
        ])

        stdout = MagicMock()

        deployment_id = 'a101449418187d92c789d1adc240b6d6'
        resolved_version = {
            'org': 'typesafe',
            'repo': 'bundle',
            'package_name': 'cassandra',
            'compatibility_version': 'v1',
            'digest': 'abcdef',
            'resolver': bintray_resolver.__name__
        }
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
                patch('conductr_cli.bundle_deploy.get_deployment_state', get_deployment_state_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            self.assertRaises(WaitTimeoutError, bundle_deploy.wait_for_deployment_complete, deployment_id,
                              resolved_version, args)

        self.assertEqual(get_deployment_state_mock.call_args_list, [
            call(deployment_id, args)
        ])

        url_mock.assert_called_with('deployments/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/deployments/events', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

    def create_test_event(self, event_name):
        sse_mock = MagicMock()
        sse_mock.event = event_name
        return sse_mock

    def create_deployment_state(self, event_type, data={}):
        result = {}
        result.update({'eventType': event_type})
        result.update(data)
        return result
