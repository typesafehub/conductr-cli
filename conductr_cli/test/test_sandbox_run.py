from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import logging_setup, sandbox_run
from conductr_cli.docker import DockerVmType
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

        mock_feature = MagicMock()
        features = [mock_feature]
        mock_collect_features = MagicMock(return_value=features)

        mock_sandbox_run_docker = MagicMock(return_value=self.container_names)
        mock_wait_for_conductr = MagicMock(return_value=True)
        mock_log_run_attempt = MagicMock()

        args = self.default_args
        args.update({
            'image_version': conductr_version
        })
        input_args = MagicMock(**args)

        with \
                patch('conductr_cli.sandbox_features.collect_features', mock_collect_features), \
                patch('conductr_cli.sandbox_run_docker.run', mock_sandbox_run_docker), \
                patch('conductr_cli.sandbox_run_docker.log_run_attempt', mock_log_run_attempt), \
                patch('conductr_cli.sandbox_run.wait_for_conductr', mock_wait_for_conductr):
            sandbox_run.run(input_args)

        mock_sandbox_run_docker.assert_called_once_with(input_args, features)

        mock_wait_for_conductr.assert_called_once_with(input_args, 0, DEFAULT_WAIT_RETRIES, DEFAULT_WAIT_RETRY_INTERVAL)

        mock_log_run_attempt.assert_called_with(input_args, self.container_names, True, 60)

        mock_feature.assert_not_called()

    def test_jvm_sandbox(self):
        conductr_version = '2.0.0'

        mock_feature = MagicMock()
        features = [mock_feature]
        mock_collect_features = MagicMock(return_value=features)

        mock_sandbox_run_docker = MagicMock(return_value=self.container_names)
        mock_wait_for_conductr = MagicMock(return_value=True)
        mock_start_proxy = MagicMock(return_value=True)
        mock_log_run_attempt = MagicMock()

        args = self.default_args
        args.update({
            'image_version': conductr_version
        })
        input_args = MagicMock(**args)
        with \
                patch('conductr_cli.sandbox_features.collect_features', mock_collect_features), \
                patch('conductr_cli.sandbox_run_jvm.run', mock_sandbox_run_docker), \
                patch('conductr_cli.sandbox_run_jvm.log_run_attempt', mock_log_run_attempt), \
                patch('conductr_cli.sandbox_run.wait_for_conductr', mock_wait_for_conductr), \
                patch('conductr_cli.sandbox_run.start_proxy', mock_start_proxy):
            sandbox_run.run(input_args)

        mock_sandbox_run_docker.assert_called_once_with(input_args, features)

        mock_wait_for_conductr.assert_called_once_with(input_args, 0, DEFAULT_WAIT_RETRIES, DEFAULT_WAIT_RETRY_INTERVAL)
        mock_start_proxy.assert_called_once_with(1)

        mock_log_run_attempt.assert_called_with(input_args, self.container_names, True, 60)


class TestStartProxy(CliTestCase):

    def test_start_proxy(self):
        stdout = MagicMock()
        mock_conduct_run = MagicMock()

        args = MagicMock(**{})

        with patch('conductr_cli.conduct_main.run', mock_conduct_run):
            logging_setup.configure_logging(args, stdout)
            sandbox_run.start_proxy(3)

        self.assertEqual([
            call(['load', 'conductr-haproxy', 'conductr-haproxy-dev-mode', '--disable-instructions'], configure_logging=False),
            call(['run', 'conductr-haproxy', '--scale', '3', '--disable-instructions'], configure_logging=False)
        ], mock_conduct_run.call_args_list)

        expected_output = strip_margin("""||------------------------------------------------|
                                          || Starting HAProxy                               |
                                          ||------------------------------------------------|
                                          |Deploying bundle conductr-haproxy with configuration conductr-haproxy-dev-mode
                                          |""")
        self.assertEqual(expected_output, self.output(stdout))


class TestWaitForStart(CliTestCase):
    def test_wait_for_start(self):
        stdout = MagicMock()
        mock_get_env = MagicMock(return_value=1)

        members_url = '/members'
        mock_url = MagicMock(return_value=members_url)

        mock_http_get = MagicMock(return_value='test only')

        with \
                patch('os.getenv', mock_get_env), \
                patch('conductr_cli.conduct_url.url', mock_url), \
                patch('conductr_cli.conduct_request.get', mock_http_get):
            args = MagicMock(**{
                'no_wait': False
            })
            logging_setup.configure_logging(args, stdout)
            result = sandbox_run.wait_for_start(args)
            self.assertEqual((True, 1.0), result)

        self.assertEqual([
            call('CONDUCTR_SANDBOX_WAIT_RETRIES', DEFAULT_WAIT_RETRIES),
            call('CONDUCTR_SANDBOX_WAIT_RETRY_INTERVAL', DEFAULT_WAIT_RETRY_INTERVAL)
        ], mock_get_env.call_args_list)

        mock_http_get.assert_called_once_with(dcos_mode=False, host=None, timeout=5, url='/members')

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
        mock_get_env = MagicMock(return_value=1)

        members_url = '/members'
        mock_url = MagicMock(return_value=members_url)

        mock_http_get = MagicMock(side_effect=[ConnectionError()])

        with \
                patch('os.getenv', mock_get_env), \
                patch('conductr_cli.conduct_url.url', mock_url), \
                patch('conductr_cli.conduct_request.get', mock_http_get):
            args = MagicMock(**{
                'no_wait': False
            })
            logging_setup.configure_logging(args, stdout)
            result = sandbox_run.wait_for_start(args)
            self.assertEqual((False, 1.0), result)

        self.assertEqual([
            call('CONDUCTR_SANDBOX_WAIT_RETRIES', DEFAULT_WAIT_RETRIES),
            call('CONDUCTR_SANDBOX_WAIT_RETRY_INTERVAL', DEFAULT_WAIT_RETRY_INTERVAL)
        ], mock_get_env.call_args_list)

        mock_http_get.assert_called_once_with(dcos_mode=False, host=None, timeout=5, url='/members')

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

        result = sandbox_run.wait_for_start(args)
        self.assertEqual((True, 0), result)
