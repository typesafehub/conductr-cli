from conductr_cli.test.cli_test_case import CliTestCase, as_error, strip_margin
from conductr_cli import logging_setup, sandbox_run, sandbox_run_docker, sandbox_run_jvm, sandbox_features
from conductr_cli.docker import DockerVmType
from conductr_cli.exceptions import InstanceCountError, JavaCallError, JavaUnsupportedVendorError, \
    JavaUnsupportedVersionError, JavaVersionParseError
from conductr_cli.sandbox_common import CONDUCTR_DEV_IMAGE
from conductr_cli.sandbox_run import DEFAULT_WAIT_RETRIES, DEFAULT_WAIT_RETRY_INTERVAL
from unittest.mock import call, patch, MagicMock
from requests.exceptions import ConnectionError


class TestSandboxRunCommand(CliTestCase):

    default_args = {
        'vm_type': DockerVmType.DOCKER_ENGINE,
        'conductr_roles': [],
        'envs': [],
        'image': CONDUCTR_DEV_IMAGE,
        'log_level': 'info',
        'nr_of_containers': 1,
        'offline_mode': False,
        'ports': [],
        'bundle_http_port': 9000,
        'features': [],
        'no_wait': False,
        'local_connection': True
    }

    def default_general_args(self, container_name):
        return ['-d', '--name', container_name]

    default_env_args = ['-e', 'CONDUCTR_INSTANCE=0', '-e', 'CONDUCTR_NR_OF_INSTANCES=1', '-e', 'AKKA_LOGLEVEL=info']
    default_port_args = ['-p', '9000:9000',
                         '-p', '9004:9004',
                         '-p', '9005:9005',
                         '-p', '9006:9006']
    default_positional_args = ['--discover-host-ip']

    container_names = ['cond-0']

    def test_docker_sandbox(self):
        conductr_version = '1.1.11'

        bundle_start_result = []
        mock_feature_attrs = {'start.return_value': bundle_start_result}
        mock_feature = MagicMock(**mock_feature_attrs)
        features = [mock_feature]
        mock_collect_features = MagicMock(return_value=features)

        sandbox_run_result = sandbox_run_docker.SandboxRunResult(self.container_names, '192.168.99.100')
        mock_sandbox_run_docker = MagicMock(return_value=sandbox_run_result)
        mock_wait_for_conductr = MagicMock(return_value=True)
        mock_log_run_attempt = MagicMock()

        args = self.default_args.copy()
        args.update({
            'image_version': conductr_version
        })
        input_args = MagicMock(**args)

        with \
                patch('conductr_cli.sandbox_features.collect_features', mock_collect_features), \
                patch('conductr_cli.sandbox_run_docker.run', mock_sandbox_run_docker), \
                patch('conductr_cli.sandbox_run_docker.log_run_attempt', mock_log_run_attempt), \
                patch('conductr_cli.sandbox_run.wait_for_conductr', mock_wait_for_conductr):
            self.assertTrue(sandbox_run.run(input_args))

        mock_sandbox_run_docker.assert_called_once_with(input_args, features)

        mock_wait_for_conductr.assert_called_once_with(input_args, sandbox_run_result, 0, DEFAULT_WAIT_RETRIES,
                                                       DEFAULT_WAIT_RETRY_INTERVAL)

        mock_log_run_attempt.assert_called_with(input_args, sandbox_run_result, bundle_start_result, True, False, 60)

        mock_feature.assert_not_called()

    def test_jvm_sandbox(self):
        conductr_version = '2.0.0'

        bundle_start_result = [sandbox_features.BundleStartResult('bundle-a', 1001)]
        mock_feature_attrs = {'start.return_value': bundle_start_result}
        mock_feature = MagicMock(**mock_feature_attrs)
        mock_feature.ports = [10001]
        features = [mock_feature]
        mock_collect_features = MagicMock(return_value=features)

        sandbox_run_result = sandbox_run_jvm.SandboxRunResult([1001], ['192.168.1.1'], [1002], ['192.168.1.1'])
        mock_sandbox_run_jvm = MagicMock(return_value=sandbox_run_result)
        mock_wait_for_conductr = MagicMock(return_value=True)
        mock_start_proxy = MagicMock(return_value=True)
        mock_log_run_attempt = MagicMock()

        args = self.default_args.copy()
        args.update({
            'image_version': conductr_version,
            'ports': [5001, 3553]
        })
        input_args = MagicMock(**args)
        with \
                patch('conductr_cli.sandbox_features.collect_features', mock_collect_features), \
                patch('conductr_cli.sandbox_run_jvm.run', mock_sandbox_run_jvm), \
                patch('conductr_cli.sandbox_run_jvm.log_run_attempt', mock_log_run_attempt), \
                patch('conductr_cli.sandbox_run.wait_for_conductr', mock_wait_for_conductr), \
                patch('conductr_cli.sandbox_proxy.start_proxy', mock_start_proxy):
            self.assertTrue(sandbox_run.run(input_args))

        mock_sandbox_run_jvm.assert_called_once_with(input_args, features)

        mock_wait_for_conductr.assert_called_once_with(input_args, sandbox_run_result, 0,
                                                       DEFAULT_WAIT_RETRIES,
                                                       DEFAULT_WAIT_RETRY_INTERVAL)
        mock_start_proxy.assert_called_once_with(proxy_bind_addr='192.168.1.1', proxy_ports=[3553, 5001])

        mock_log_run_attempt.assert_called_with(input_args, sandbox_run_result, bundle_start_result, True, True, 60)

    def test_docker_sandbox_instance_count_error(self):
        conductr_version = '1.1.11'

        stdout = MagicMock()
        stderr = MagicMock()

        mock_feature = MagicMock()
        features = [mock_feature]
        mock_collect_features = MagicMock(return_value=features)

        nr_of_containers = '2:3'

        mock_sandbox_run_docker = MagicMock(side_effect=[InstanceCountError(conductr_version, nr_of_containers,
                                                                            'Test only')])

        args = self.default_args.copy()
        args.update({
            'image_version': conductr_version,
            'nr_of_containers': nr_of_containers
        })
        input_args = MagicMock(**args)

        with \
                patch('conductr_cli.sandbox_features.collect_features', mock_collect_features), \
                patch('conductr_cli.sandbox_run_docker.run', mock_sandbox_run_docker):
            logging_setup.configure_logging(input_args, stdout, stderr)
            self.assertFalse(sandbox_run.run(input_args))

        mock_sandbox_run_docker.assert_called_once_with(input_args, features)

        expected_output = strip_margin(as_error("""|Error: Invalid number of containers 2:3 for ConductR version 1.1.11
                                                   |Error: Test only
                                                   |"""))
        self.assertEqual(expected_output, self.output(stderr))

        mock_feature.assert_not_called()

    def test_jvm_validation_call_error(self):
        conductr_version = '2.0.0'

        stdout = MagicMock()
        stderr = MagicMock()

        mock_feature = MagicMock()
        features = [mock_feature]
        mock_collect_features = MagicMock(return_value=features)
        mock_sandbox_run_jvm = MagicMock(side_effect=JavaCallError('test'))

        args = self.default_args.copy()
        args.update({
            'image_version': conductr_version
        })
        input_args = MagicMock(**args)
        with \
                patch('conductr_cli.sandbox_features.collect_features', mock_collect_features), \
                patch('conductr_cli.sandbox_run_jvm.run', mock_sandbox_run_jvm):
            logging_setup.configure_logging(input_args, stdout, stderr)
            self.assertFalse(sandbox_run.run(input_args))

        mock_sandbox_run_jvm.assert_called_once_with(input_args, features)

        expected_output = strip_margin(as_error("""|Error: Unable to obtain java version.
                                                   |Error: test
                                                   |Error: Please ensure Oracle JVM 1.8 and above is installed.
                                                   |"""))
        self.assertEqual(expected_output, self.output(stderr))

    def test_jvm_validation_unsupported_vendor(self):
        conductr_version = '2.0.0'

        stdout = MagicMock()
        stderr = MagicMock()

        mock_feature = MagicMock()
        features = [mock_feature]
        mock_collect_features = MagicMock(return_value=features)
        mock_sandbox_run_jvm = MagicMock(side_effect=JavaUnsupportedVendorError('test'))

        args = self.default_args.copy()
        args.update({
            'image_version': conductr_version
        })
        input_args = MagicMock(**args)
        with \
                patch('conductr_cli.sandbox_features.collect_features', mock_collect_features), \
                patch('conductr_cli.sandbox_run_jvm.run', mock_sandbox_run_jvm):
            logging_setup.configure_logging(input_args, stdout, stderr)
            self.assertFalse(sandbox_run.run(input_args))

        mock_sandbox_run_jvm.assert_called_once_with(input_args, features)

        expected_output = strip_margin(as_error("""|Error: Unsupported JVM vendor: test
                                                   |Error: Please ensure Oracle JVM 1.8 and above is installed.
                                                   |"""))
        self.assertEqual(expected_output, self.output(stderr))

    def test_jvm_validation_unsupported_version(self):
        conductr_version = '2.0.0'

        stdout = MagicMock()
        stderr = MagicMock()

        mock_feature = MagicMock()
        features = [mock_feature]
        mock_collect_features = MagicMock(return_value=features)
        mock_sandbox_run_jvm = MagicMock(side_effect=JavaUnsupportedVersionError('1.4'))

        args = self.default_args.copy()
        args.update({
            'image_version': conductr_version
        })
        input_args = MagicMock(**args)
        with \
                patch('conductr_cli.sandbox_features.collect_features', mock_collect_features), \
                patch('conductr_cli.sandbox_run_jvm.run', mock_sandbox_run_jvm):
            logging_setup.configure_logging(input_args, stdout, stderr)
            self.assertFalse(sandbox_run.run(input_args))

        mock_sandbox_run_jvm.assert_called_once_with(input_args, features)

        expected_output = strip_margin(as_error("""|Error: Unsupported JVM version: 1.4
                                                   |Error: Please ensure Oracle JVM 1.8 and above is installed.
                                                   |"""))
        self.assertEqual(expected_output, self.output(stderr))

    def test_jvm_validation_java_version_parse_error(self):
        conductr_version = '2.0.0'

        stdout = MagicMock()
        stderr = MagicMock()

        mock_feature = MagicMock()
        features = [mock_feature]
        mock_collect_features = MagicMock(return_value=features)
        mock_sandbox_run_jvm = MagicMock(side_effect=JavaVersionParseError('this is the output from java -version'))

        args = self.default_args.copy()
        args.update({
            'image_version': conductr_version
        })
        input_args = MagicMock(**args)
        with \
                patch('conductr_cli.sandbox_features.collect_features', mock_collect_features), \
                patch('conductr_cli.sandbox_run_jvm.run', mock_sandbox_run_jvm):
            logging_setup.configure_logging(input_args, stdout, stderr)
            self.assertFalse(sandbox_run.run(input_args))

        mock_sandbox_run_jvm.assert_called_once_with(input_args, features)

        expected_output = strip_margin(as_error("""|Error: Unable to obtain java version from the `java -version` command.
                                                   |Error: Please ensure Oracle JVM 1.8 and above is installed.
                                                   |"""))
        self.assertEqual(expected_output, self.output(stderr))


class TestWaitForStart(CliTestCase):
    def test_wait_for_start(self):
        stdout = MagicMock()
        is_tty_mock = MagicMock(return_value=True)
        mock_get_env = MagicMock(return_value=1)

        members_url = '/members'
        mock_url = MagicMock(return_value=members_url)

        mock_http_get = MagicMock(return_value='test only')

        with \
                patch('os.getenv', mock_get_env), \
                patch('conductr_cli.conduct_url.url', mock_url), \
                patch('conductr_cli.conduct_request.get', mock_http_get), \
                patch('sys.stdout.isatty', is_tty_mock):
            args = MagicMock(**{
                'no_wait': False
            })
            logging_setup.configure_logging(args, stdout)
            run_result = MagicMock(**{
                'host': '10.0.0.1'
            })
            result = sandbox_run.wait_for_start(args, run_result)
            self.assertEqual((True, 1.0), result)

        self.assertEqual([
            call('CONDUCTR_SANDBOX_WAIT_RETRIES', DEFAULT_WAIT_RETRIES),
            call('CONDUCTR_SANDBOX_WAIT_RETRY_INTERVAL', DEFAULT_WAIT_RETRY_INTERVAL)
        ], mock_get_env.call_args_list)

        mock_http_get.assert_called_once_with(dcos_mode=False, host='10.0.0.1', timeout=5, url='/members')

        self.assertEqual([
            call.write('Waiting for ConductR to start\r'),
            call.write(''),
            call.flush(),
            call.write('Waiting for ConductR to start.\r'),
            call.write(''),
            call.flush(),
            call.write('Waiting for ConductR to start.\n'),
            call.write(''),
            call.flush()
        ], stdout.method_calls)

    def test_wait_for_start_timeout(self):
        stdout = MagicMock()
        is_tty_mock = MagicMock(return_value=True)
        mock_get_env = MagicMock(return_value=1)

        members_url = '/members'
        mock_url = MagicMock(return_value=members_url)

        mock_http_get = MagicMock(side_effect=[ConnectionError()])

        with \
                patch('os.getenv', mock_get_env), \
                patch('conductr_cli.conduct_url.url', mock_url), \
                patch('conductr_cli.conduct_request.get', mock_http_get), \
                patch('sys.stdout.isatty', is_tty_mock):
            args = MagicMock(**{
                'no_wait': False
            })
            logging_setup.configure_logging(args, stdout)
            run_result = MagicMock(**{
                'host': '10.0.0.1'
            })
            result = sandbox_run.wait_for_start(args, run_result)
            self.assertEqual((False, 1.0), result)

        self.assertEqual([
            call('CONDUCTR_SANDBOX_WAIT_RETRIES', DEFAULT_WAIT_RETRIES),
            call('CONDUCTR_SANDBOX_WAIT_RETRY_INTERVAL', DEFAULT_WAIT_RETRY_INTERVAL)
        ], mock_get_env.call_args_list)

        mock_http_get.assert_called_once_with(dcos_mode=False, host='10.0.0.1', timeout=5, url='/members')

        self.assertEqual([
            call.write('Waiting for ConductR to start\r'),
            call.write(''),
            call.flush(),
            call.write('Waiting for ConductR to start.\r'),
            call.write(''),
            call.flush(),
            call.write('Waiting for ConductR to start.\n'),
            call.write(''),
            call.flush()
        ], stdout.method_calls)

    def test_no_wait(self):
        args = MagicMock(**{
            'no_wait': True
        })
        run_result = MagicMock(**{
            'host': '10.0.0.1'
        })
        result = sandbox_run.wait_for_start(args, run_result)
        self.assertEqual((True, 0), result)
