from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import sandbox_run, logging_setup
from conductr_cli.sandbox_common import CONDUCTR_DEV_IMAGE, LATEST_CONDUCTR_VERSION
from conductr_cli.sandbox_run import DEFAULT_WAIT_RETRIES, DEFAULT_WAIT_RETRY_INTERVAL
import os


try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestSandboxRunCommand(CliTestCase):

    default_args = {
        'image_version': LATEST_CONDUCTR_VERSION,
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

    default_env_args = ['-e', 'AKKA_LOGLEVEL=info']
    default_port_args = ['-p', '9000:9000',
                         '-p', '9004:9004',
                         '-p', '9005:9005',
                         '-p', '9006:9006']
    default_positional_args = ['--discover-host-ip']

    def test_default_args(self):
        stdout = MagicMock()
        mock_wait_for_conductr = MagicMock()

        with \
                patch('conductr_cli.terminal.docker_images', return_value=''), \
                patch('conductr_cli.terminal.docker_pull', return_value=''), \
                patch('conductr_cli.terminal.docker_ps', return_value=''), \
                patch('conductr_cli.terminal.docker_inspect', return_value='10.10.10.10'), \
                patch('conductr_cli.terminal.docker_run', return_value='') as mock_docker_run, \
                patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=[]), \
                patch('conductr_cli.sandbox_common.resolve_host_ip', return_value='192.168.99.100'), \
                patch('conductr_cli.sandbox_run.wait_for_conductr', mock_wait_for_conductr):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            sandbox_run.run(MagicMock(**self.default_args))

        expected_stdout = strip_margin("""|Pulling down the ConductR development image..
                                          |Starting ConductR nodes..
                                          |Starting container cond-0..
                                          |ConductR has been started. Check current bundle status with: conduct info
                                          |""")
        expected_optional_args = self.default_general_args('cond-0') + self.default_env_args + self.default_port_args
        expected_image = '{}:{}'.format(CONDUCTR_DEV_IMAGE, LATEST_CONDUCTR_VERSION)
        expected_positional_args = self.default_positional_args

        self.assertEqual(expected_stdout, self.output(stdout))
        mock_docker_run.assert_called_once_with(expected_optional_args, expected_image, expected_positional_args)
        mock_wait_for_conductr.assert_called_once_with(0, DEFAULT_WAIT_RETRIES, DEFAULT_WAIT_RETRY_INTERVAL)

    def test_multiple_container(self):
        stdout = MagicMock()
        mock_wait_for_conductr = MagicMock()
        nr_of_containers = 3

        with \
                patch('conductr_cli.terminal.docker_images', return_value='some-image'), \
                patch('conductr_cli.terminal.docker_ps', return_value=''), \
                patch('conductr_cli.terminal.docker_inspect', return_value='10.10.10.10'), \
                patch('conductr_cli.terminal.docker_run', return_value='') as mock_docker_run, \
                patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=[]), \
                patch('conductr_cli.sandbox_common.resolve_host_ip', return_value='192.168.99.100'), \
                patch('conductr_cli.sandbox_run.wait_for_conductr', mock_wait_for_conductr):
            args = self.default_args.copy()
            args.update({'nr_of_containers': nr_of_containers})
            logging_setup.configure_logging(MagicMock(**args), stdout)
            sandbox_run.run(MagicMock(**args))

        expected_stdout = strip_margin("""|Starting ConductR nodes..
                                          |Starting container cond-0..
                                          |Starting container cond-1..
                                          |Starting container cond-2..
                                          |ConductR has been started. Check current bundle status with: conduct info
                                          |""")
        expected_image = '{}:{}'.format(CONDUCTR_DEV_IMAGE, LATEST_CONDUCTR_VERSION)

        self.assertEqual(expected_stdout, self.output(stdout))
        # Assert cond-0
        mock_docker_run.assert_any_call(
            ['-d', '--name', 'cond-0', '-e', 'AKKA_LOGLEVEL=info',
             '-p', '9000:9000', '-p', '9004:9004', '-p', '9005:9005', '-p', '9006:9006'],
            expected_image,
            self.default_positional_args
        )
        # Assert cond-1
        mock_docker_run.assert_any_call(
            ['-d', '--name', 'cond-1', '-e', 'AKKA_LOGLEVEL=info', '-e', 'SYSLOG_IP=10.10.10.10',
             '-p', '9010:9000', '-p', '9014:9004', '-p', '9015:9005', '-p', '9016:9006'],
            expected_image,
            self.default_positional_args + ['--seed', '10.10.10.10:9004']
        )
        # Assert cond-2
        mock_docker_run.assert_any_call(
            ['-d', '--name', 'cond-2', '-e', 'AKKA_LOGLEVEL=info', '-e', 'SYSLOG_IP=10.10.10.10',
             '-p', '9020:9000', '-p', '9024:9004', '-p', '9025:9005', '-p', '9026:9006'],
            expected_image,
            self.default_positional_args + ['--seed', '10.10.10.10:9004']
        )
        mock_wait_for_conductr.assert_called_once_with(0, DEFAULT_WAIT_RETRIES, DEFAULT_WAIT_RETRY_INTERVAL)

    def test_with_custom_args(self):
        stdout = MagicMock()
        mock_wait_for_conductr = MagicMock()
        image_version = '1.1.0'
        conductr_roles = [['role1', 'role2']]
        envs = ['key1=value1', 'key2=value2']
        image = 'my-image'
        log_level = 'debug'
        nr_of_containers = 1
        ports = [3000, 3001]
        features = ['visualization', 'logging']

        with \
                patch('conductr_cli.terminal.docker_images', return_value='some-image'), \
                patch('conductr_cli.terminal.docker_ps', return_value=''), \
                patch('conductr_cli.terminal.docker_inspect', return_value='10.10.10.10'), \
                patch('conductr_cli.terminal.docker_run', return_value='') as mock_docker_run, \
                patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=[]), \
                patch('conductr_cli.sandbox_common.resolve_host_ip', return_value='192.168.99.100'), \
                patch('conductr_cli.sandbox_run.wait_for_conductr', mock_wait_for_conductr):
            args = self.default_args.copy()
            args.update({
                'image_version': image_version,
                'conductr_roles': conductr_roles,
                'envs': envs,
                'image': image,
                'log_level': log_level,
                'nr_of_containers': nr_of_containers,
                'ports': ports,
                'bundle_http_port': 7222,
                'features': features
            })
            logging_setup.configure_logging(MagicMock(**args), stdout)
            sandbox_run.run(MagicMock(**args))

        expected_stdout = strip_margin("""|Starting ConductR nodes..
                                          |Starting container cond-0 exposing 192.168.99.100:3000, 192.168.99.100:3001, 192.168.99.100:5601, 192.168.99.100:9200, 192.168.99.100:9999..
                                          |ConductR has been started. Check current bundle status with: conduct info
                                          |""")

        self.assertEqual(expected_stdout, self.output(stdout))
        mock_docker_run.assert_called_once_with(
            ['-d', '--name', 'cond-0', '-e', 'key1=value1', '-e', 'key2=value2', '-e', 'AKKA_LOGLEVEL=debug',
             '-e', 'CONDUCTR_FEATURES=visualization,logging', '-e', 'CONDUCTR_ROLES=role1,role2',
             '-p', '5601:5601', '-p', '9004:9004', '-p', '9005:9005', '-p', '9006:9006',
             '-p', '9999:9999', '-p', '9200:9200', '-p', '7222:7222', '-p', '3000:3000',
             '-p', '3001:3001'],
            '{}:{}'.format(image, image_version),
            self.default_positional_args
        )
        mock_wait_for_conductr.assert_called_once_with(0, DEFAULT_WAIT_RETRIES, DEFAULT_WAIT_RETRY_INTERVAL)

    def test_roles(self):
        stdout = MagicMock()
        mock_wait_for_conductr = MagicMock()
        nr_of_containers = 3
        conductr_roles = [['role1', 'role2'], ['role3']]

        with \
                patch('conductr_cli.terminal.docker_images', return_value='some-image'), \
                patch('conductr_cli.terminal.docker_ps', return_value=''), \
                patch('conductr_cli.terminal.docker_inspect', return_value='10.10.10.10'), \
                patch('conductr_cli.terminal.docker_run', return_value='') as mock_docker_run, \
                patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=[]), \
                patch('conductr_cli.sandbox_common.resolve_host_ip', return_value='192.168.99.100'), \
                patch('conductr_cli.sandbox_run.wait_for_conductr', mock_wait_for_conductr):
            args = self.default_args.copy()
            args.update({
                'nr_of_containers': nr_of_containers,
                'conductr_roles': conductr_roles
            })
            logging_setup.configure_logging(MagicMock(**args), stdout)
            sandbox_run.run(MagicMock(**args))

        expected_stdout = strip_margin("""|Starting ConductR nodes..
                                          |Starting container cond-0..
                                          |Starting container cond-1..
                                          |Starting container cond-2..
                                          |ConductR has been started. Check current bundle status with: conduct info
                                          |""")
        expected_image = '{}:{}'.format(CONDUCTR_DEV_IMAGE, LATEST_CONDUCTR_VERSION)

        self.assertEqual(expected_stdout, self.output(stdout))
        # Assert cond-0
        mock_docker_run.assert_any_call(
            ['-d', '--name', 'cond-0', '-e', 'AKKA_LOGLEVEL=info', '-e', 'CONDUCTR_ROLES=role1,role2',
             '-p', '9000:9000', '-p', '9004:9004', '-p', '9005:9005', '-p', '9006:9006'],
            expected_image,
            self.default_positional_args
        )
        # Assert cond-1
        mock_docker_run.assert_any_call(
            ['-d', '--name', 'cond-1', '-e', 'AKKA_LOGLEVEL=info', '-e', 'SYSLOG_IP=10.10.10.10',
             '-e', 'CONDUCTR_ROLES=role3',
             '-p', '9010:9000', '-p', '9014:9004', '-p', '9015:9005', '-p', '9016:9006'],
            expected_image,
            self.default_positional_args + ['--seed', '10.10.10.10:9004']
        )
        # Assert cond-2
        mock_docker_run.assert_any_call(
            ['-d', '--name', 'cond-2', '-e', 'AKKA_LOGLEVEL=info', '-e', 'SYSLOG_IP=10.10.10.10',
             '-e', 'CONDUCTR_ROLES=role1,role2',
             '-p', '9020:9000', '-p', '9024:9004', '-p', '9025:9005', '-p', '9026:9006'],
            expected_image,
            self.default_positional_args + ['--seed', '10.10.10.10:9004']
        )
        mock_wait_for_conductr.assert_called_once_with(0, DEFAULT_WAIT_RETRIES, DEFAULT_WAIT_RETRY_INTERVAL)

    def test_containers_already_running(self):
        stdout = MagicMock()
        mock_wait_for_conductr = MagicMock()

        running_containers = ['cond-0']

        with \
                patch('conductr_cli.terminal.docker_images', return_value='some-image'), \
                patch('conductr_cli.terminal.docker_pull', return_value=''), \
                patch('conductr_cli.terminal.docker_ps', return_value=''), \
                patch('conductr_cli.terminal.docker_inspect', return_value='10.10.10.10'), \
                patch('conductr_cli.terminal.docker_run', return_value=''), \
                patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=running_containers), \
                patch('conductr_cli.sandbox_common.resolve_host_ip', return_value='192.168.99.100'), \
                patch('conductr_cli.sandbox_run.wait_for_conductr', mock_wait_for_conductr), \
                patch('conductr_cli.terminal.docker_rm') as mock_docker_rm:
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            sandbox_run.run(MagicMock(**self.default_args))

        expected_stdout = strip_margin("""|Stopping ConductR..
                                          |Starting ConductR nodes..
                                          |Starting container cond-0..
                                          |ConductR has been started. Check current bundle status with: conduct info
                                          |""")

        self.assertEqual(expected_stdout, self.output(stdout))
        mock_docker_rm.assert_called_once_with(running_containers)
        mock_wait_for_conductr.assert_called_once_with(0, DEFAULT_WAIT_RETRIES, DEFAULT_WAIT_RETRY_INTERVAL)

    def test_run_options(self):
        stdout = MagicMock()
        mock_wait_for_conductr = MagicMock()
        run_options = {'CONDUCTR_DOCKER_RUN_OPTS': "-v /etc/haproxy:/usr/local/etc/haproxy"}

        def run_env(key, default=None):
            return run_options[key] if key in run_options else os.environ.get(key, default)

        with \
                patch('conductr_cli.terminal.docker_images', return_value=''), \
                patch('conductr_cli.terminal.docker_pull', return_value=''), \
                patch('conductr_cli.terminal.docker_ps', return_value=''), \
                patch('conductr_cli.terminal.docker_inspect', return_value='10.10.10.10'), \
                patch('conductr_cli.terminal.docker_run', return_value='') as mock_docker_run, \
                patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=[]), \
                patch('conductr_cli.sandbox_common.resolve_host_ip', return_value='192.168.99.100'), \
                patch('conductr_cli.sandbox_run.wait_for_conductr', mock_wait_for_conductr), \
                patch('os.getenv', side_effect=run_env) as mock_get_env:
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            sandbox_run.run(MagicMock(**self.default_args))

        expected_stdout = strip_margin("""|Pulling down the ConductR development image..
                                          |Starting ConductR nodes..
                                          |Starting container cond-0..
                                          |ConductR has been started. Check current bundle status with: conduct info
                                          |""")
        expected_optional_args = self.default_general_args('cond-0') + self.default_env_args + self.default_port_args
        expected_image = '{}:{}'.format(CONDUCTR_DEV_IMAGE, LATEST_CONDUCTR_VERSION)
        expected_positional_args = self.default_positional_args

        self.assertEqual(expected_stdout, self.output(stdout))
        mock_get_env.assert_any_call('CONDUCTR_DOCKER_RUN_OPTS')
        mock_docker_run.assert_called_once_with(expected_optional_args + ['-v', '/etc/haproxy:/usr/local/etc/haproxy'],
                                                expected_image, expected_positional_args)
        mock_wait_for_conductr.assert_called_once_with(0, DEFAULT_WAIT_RETRIES, DEFAULT_WAIT_RETRY_INTERVAL)

    def test_no_wait(self):
        stdout = MagicMock()
        mock_wait_for_conductr = MagicMock()

        with \
                patch('conductr_cli.terminal.docker_images', return_value=''), \
                patch('conductr_cli.terminal.docker_pull', return_value=''), \
                patch('conductr_cli.terminal.docker_ps', return_value=''), \
                patch('conductr_cli.terminal.docker_inspect', return_value='10.10.10.10'), \
                patch('conductr_cli.terminal.docker_run', return_value='') as mock_docker_run, \
                patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=[]), \
                patch('conductr_cli.sandbox_common.resolve_host_ip', return_value='192.168.99.100'), \
                patch('conductr_cli.sandbox_run.wait_for_conductr', mock_wait_for_conductr):
            args = self.default_args.copy()
            args.update({'no_wait': True})
            logging_setup.configure_logging(MagicMock(**args), stdout)
            sandbox_run.run(MagicMock(**args))

        expected_stdout = strip_margin("""|Pulling down the ConductR development image..
                                          |Starting ConductR nodes..
                                          |Starting container cond-0..
                                          |""")
        expected_optional_args = self.default_general_args('cond-0') + self.default_env_args + self.default_port_args
        expected_image = '{}:{}'.format(CONDUCTR_DEV_IMAGE, LATEST_CONDUCTR_VERSION)
        expected_positional_args = self.default_positional_args

        self.assertEqual(expected_stdout, self.output(stdout))
        mock_docker_run.assert_called_once_with(expected_optional_args, expected_image, expected_positional_args)
        mock_wait_for_conductr.assert_not_called()

    def test_wait_options(self):
        stdout = MagicMock()
        mock_wait_for_conductr = MagicMock()
        wait_retries = 3
        wait_retry_interval = 1.0
        wait_options = {
            'CONDUCTR_SANDBOX_WAIT_RETRIES': str(wait_retries),
            'CONDUCTR_SANDBOX_WAIT_RETRY_INTERVAL': str(wait_retry_interval)
        }

        def wait_env(key, default=None):
            return wait_options[key] if key in wait_options else os.environ.get(key, default)

        with \
                patch('conductr_cli.terminal.docker_images', return_value=''), \
                patch('conductr_cli.terminal.docker_pull', return_value=''), \
                patch('conductr_cli.terminal.docker_ps', return_value=''), \
                patch('conductr_cli.terminal.docker_inspect', return_value='10.10.10.10'), \
                patch('conductr_cli.terminal.docker_run', return_value='') as mock_docker_run, \
                patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=[]), \
                patch('conductr_cli.sandbox_common.resolve_host_ip', return_value='192.168.99.100'), \
                patch('conductr_cli.sandbox_run.wait_for_conductr', mock_wait_for_conductr), \
                patch('os.getenv', side_effect=wait_env) as mock_getenv:
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            sandbox_run.run(MagicMock(**self.default_args))

        expected_stdout = strip_margin("""|Pulling down the ConductR development image..
                                          |Starting ConductR nodes..
                                          |Starting container cond-0..
                                          |ConductR has been started. Check current bundle status with: conduct info
                                          |""")
        expected_optional_args = self.default_general_args('cond-0') + self.default_env_args + self.default_port_args
        expected_image = '{}:{}'.format(CONDUCTR_DEV_IMAGE, LATEST_CONDUCTR_VERSION)
        expected_positional_args = self.default_positional_args

        self.assertEqual(expected_stdout, self.output(stdout))
        mock_getenv.assert_any_call('CONDUCTR_SANDBOX_WAIT_RETRIES', DEFAULT_WAIT_RETRIES)
        mock_getenv.assert_any_call('CONDUCTR_SANDBOX_WAIT_RETRY_INTERVAL', DEFAULT_WAIT_RETRY_INTERVAL)
        mock_docker_run.assert_called_once_with(expected_optional_args, expected_image, expected_positional_args)
        mock_wait_for_conductr.assert_called_once_with(0, wait_retries, wait_retry_interval)
