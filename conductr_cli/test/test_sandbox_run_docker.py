from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import sandbox_run_docker, logging_setup
from conductr_cli.constants import FEATURE_PROVIDE_PROXYING
from conductr_cli.docker import DockerVmType
from conductr_cli.exceptions import InstanceCountError
from conductr_cli.sandbox_common import CONDUCTR_DEV_IMAGE
from conductr_cli.sandbox_features import VisualizationFeature, LoggingFeature
from conductr_cli.test.data.test_constants import LATEST_CONDUCTR_VERSION
from unittest.mock import patch, MagicMock
import os


class TestRun(CliTestCase):

    default_args = {
        'vm_type': DockerVmType.DOCKER_ENGINE,
        'image_version': LATEST_CONDUCTR_VERSION,
        'conductr_roles': [],
        'envs': [],
        'image': CONDUCTR_DEV_IMAGE,
        'log_level': 'info',
        'nr_of_containers': 1,
        'ports': [],
        'bundle_http_port': 9000,
        'features': [],
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

    def test_default_args(self):
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        features = []
        with \
                patch('conductr_cli.terminal.docker_images', return_value=''), \
                patch('conductr_cli.terminal.docker_pull', return_value=''), \
                patch('conductr_cli.terminal.docker_ps', return_value=''), \
                patch('conductr_cli.terminal.docker_inspect', return_value='10.10.10.10'), \
                patch('conductr_cli.terminal.docker_run', return_value='') as mock_docker_run, \
                patch('conductr_cli.sandbox_features.stop_features') as mock_stop_proxy, \
                patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=[]):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            sandbox_run_docker.run(input_args, features)

        expected_stdout = strip_margin("""|Pulling down the ConductR development image..
                                          ||------------------------------------------------|
                                          || Starting ConductR                              |
                                          ||------------------------------------------------|
                                          |Starting container cond-0..
                                          |""")
        expected_optional_args = self.default_general_args('cond-0') + self.default_env_args + self.default_port_args
        expected_image = '{}:{}'.format(CONDUCTR_DEV_IMAGE, LATEST_CONDUCTR_VERSION)
        expected_positional_args = self.default_positional_args

        self.assertEqual(expected_stdout, self.output(stdout))
        mock_docker_run.assert_called_once_with(expected_optional_args, expected_image, expected_positional_args)

        mock_stop_proxy.assert_called_once_with()

    def test_multiple_container(self):
        stdout = MagicMock()
        nr_of_instances = 3

        with \
                patch('conductr_cli.terminal.docker_images', return_value='some-image'), \
                patch('conductr_cli.terminal.docker_ps', return_value=''), \
                patch('conductr_cli.terminal.docker_inspect', return_value='10.10.10.10'), \
                patch('conductr_cli.terminal.docker_run', return_value='') as mock_docker_run, \
                patch('conductr_cli.sandbox_features.stop_features') as mock_stop_proxy, \
                patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=[]):
            args = self.default_args.copy()
            args.update({'nr_of_instances': nr_of_instances})
            input_args = MagicMock(**args)
            logging_setup.configure_logging(input_args, stdout)
            features = []
            sandbox_run_docker.run(input_args, features)

        expected_stdout = strip_margin("""||------------------------------------------------|
                                          || Starting ConductR                              |
                                          ||------------------------------------------------|
                                          |Starting container cond-0..
                                          |Starting container cond-1..
                                          |Starting container cond-2..
                                          |""")
        expected_image = '{}:{}'.format(CONDUCTR_DEV_IMAGE, LATEST_CONDUCTR_VERSION)

        self.assertEqual(expected_stdout, self.output(stdout))
        # Assert cond-0
        mock_docker_run.assert_any_call(
            ['-d', '--name', 'cond-0',
             '-e', 'CONDUCTR_INSTANCE=0', '-e', 'CONDUCTR_NR_OF_INSTANCES=3',
             '-e', 'AKKA_LOGLEVEL=info',
             '-p', '9000:9000', '-p', '9004:9004', '-p', '9005:9005', '-p', '9006:9006'],
            expected_image,
            self.default_positional_args
        )
        # Assert cond-1
        mock_docker_run.assert_any_call(
            ['-d', '--name', 'cond-1',
             '-e', 'CONDUCTR_INSTANCE=1', '-e', 'CONDUCTR_NR_OF_INSTANCES=3',
             '-e', 'AKKA_LOGLEVEL=info', '-e', 'SYSLOG_IP=10.10.10.10',
             '-p', '9010:9000', '-p', '9014:9004', '-p', '9015:9005', '-p', '9016:9006'],
            expected_image,
            self.default_positional_args + ['--seed', '10.10.10.10:9004']
        )
        # Assert cond-2
        mock_docker_run.assert_any_call(
            ['-d', '--name', 'cond-2',
             '-e', 'CONDUCTR_INSTANCE=2', '-e', 'CONDUCTR_NR_OF_INSTANCES=3',
             '-e', 'AKKA_LOGLEVEL=info', '-e', 'SYSLOG_IP=10.10.10.10',
             '-p', '9020:9000', '-p', '9024:9004', '-p', '9025:9005', '-p', '9026:9006'],
            expected_image,
            self.default_positional_args + ['--seed', '10.10.10.10:9004']
        )

        mock_stop_proxy.assert_called_once_with()

    def test_with_custom_args(self):
        stdout = MagicMock()
        image_version = '1.1.0'
        conductr_roles = [['role1', 'role2']]
        envs = ['key1=value1', 'key2=value2']
        image = 'my-image'
        log_level = 'debug'
        nr_of_containers = 1
        ports = [3000, 3001]
        features = [
            VisualizationFeature(version_args=[], image_version=image_version, offline_mode=False),
            LoggingFeature(version_args=[], image_version=image_version, offline_mode=False)
        ]

        with \
                patch('conductr_cli.terminal.docker_images', return_value='some-image'), \
                patch('conductr_cli.terminal.docker_ps', return_value=''), \
                patch('conductr_cli.terminal.docker_inspect', return_value='10.10.10.10'), \
                patch('conductr_cli.terminal.docker_run', return_value='') as mock_docker_run, \
                patch('conductr_cli.sandbox_features.stop_features') as mock_stop_proxy, \
                patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=[]):
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
            input_args = MagicMock(**args)
            logging_setup.configure_logging(input_args, stdout)
            sandbox_run_docker.run(input_args, features)

        expected_stdout = strip_margin("""||------------------------------------------------|
                                          || Starting ConductR                              |
                                          ||------------------------------------------------|
                                          |Starting container cond-0 exposing 127.0.0.1:3000, 127.0.0.1:3001, 127.0.0.1:5601, 127.0.0.1:9200, 127.0.0.1:9999..
                                          |""")

        self.assertEqual(expected_stdout, self.output(stdout))
        mock_docker_run.assert_called_once_with(
            ['-d', '--name', 'cond-0', '-e', 'key1=value1', '-e', 'key2=value2',
             '-e', 'CONDUCTR_INSTANCE=0', '-e', 'CONDUCTR_NR_OF_INSTANCES=1', '-e', 'AKKA_LOGLEVEL=debug',
             '-e', 'CONDUCTR_FEATURES=visualization,logging', '-e', 'CONDUCTR_ROLES=role1,role2',
             '-p', '5601:5601', '-p', '9004:9004', '-p', '9005:9005', '-p', '9006:9006',
             '-p', '9999:9999', '-p', '9200:9200', '-p', '7222:7222', '-p', '3000:3000',
             '-p', '3001:3001'],
            '{}:{}'.format(image, image_version),
            self.default_positional_args
        )

        mock_stop_proxy.assert_called_once_with()

    def test_roles(self):
        stdout = MagicMock()
        nr_of_instances = 3
        conductr_roles = [['role1', 'role2'], ['role3']]
        features = []

        with \
                patch('conductr_cli.terminal.docker_images', return_value='some-image'), \
                patch('conductr_cli.terminal.docker_ps', return_value=''), \
                patch('conductr_cli.terminal.docker_inspect', return_value='10.10.10.10'), \
                patch('conductr_cli.terminal.docker_run', return_value='') as mock_docker_run, \
                patch('conductr_cli.sandbox_features.stop_features') as mock_stop_proxy, \
                patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=[]):
            args = self.default_args.copy()
            args.update({
                'nr_of_instances': nr_of_instances,
                'conductr_roles': conductr_roles
            })
            input_args = MagicMock(**args)
            logging_setup.configure_logging(input_args, stdout)
            sandbox_run_docker.run(input_args, features)

        expected_stdout = strip_margin("""||------------------------------------------------|
                                          || Starting ConductR                              |
                                          ||------------------------------------------------|
                                          |Starting container cond-0..
                                          |Starting container cond-1..
                                          |Starting container cond-2..
                                          |""")
        expected_image = '{}:{}'.format(CONDUCTR_DEV_IMAGE, LATEST_CONDUCTR_VERSION)

        self.assertEqual(expected_stdout, self.output(stdout))
        # Assert cond-0
        mock_docker_run.assert_any_call(
            ['-d', '--name', 'cond-0',
             '-e', 'CONDUCTR_INSTANCE=0', '-e', 'CONDUCTR_NR_OF_INSTANCES=3',
             '-e', 'AKKA_LOGLEVEL=info', '-e', 'CONDUCTR_ROLES=role1,role2',
             '-p', '9000:9000', '-p', '9004:9004', '-p', '9005:9005', '-p', '9006:9006'],
            expected_image,
            self.default_positional_args
        )
        # Assert cond-1
        mock_docker_run.assert_any_call(
            ['-d', '--name', 'cond-1',
             '-e', 'CONDUCTR_INSTANCE=1', '-e', 'CONDUCTR_NR_OF_INSTANCES=3',
             '-e', 'AKKA_LOGLEVEL=info', '-e', 'SYSLOG_IP=10.10.10.10',
             '-e', 'CONDUCTR_ROLES=role3',
             '-p', '9010:9000', '-p', '9014:9004', '-p', '9015:9005', '-p', '9016:9006'],
            expected_image,
            self.default_positional_args + ['--seed', '10.10.10.10:9004']
        )
        # Assert cond-2
        mock_docker_run.assert_any_call(
            ['-d', '--name', 'cond-2',
             '-e', 'CONDUCTR_INSTANCE=2', '-e', 'CONDUCTR_NR_OF_INSTANCES=3',
             '-e', 'AKKA_LOGLEVEL=info', '-e', 'SYSLOG_IP=10.10.10.10',
             '-e', 'CONDUCTR_ROLES=role1,role2',
             '-p', '9020:9000', '-p', '9024:9004', '-p', '9025:9005', '-p', '9026:9006'],
            expected_image,
            self.default_positional_args + ['--seed', '10.10.10.10:9004']
        )

        mock_stop_proxy.assert_called_once_with()

    def test_containers_already_running(self):
        stdout = MagicMock()

        features = []
        running_containers = ['cond-0']

        input_args = MagicMock(**self.default_args)
        with \
                patch('conductr_cli.terminal.docker_images', return_value='some-image'), \
                patch('conductr_cli.terminal.docker_pull', return_value=''), \
                patch('conductr_cli.terminal.docker_ps', return_value=''), \
                patch('conductr_cli.terminal.docker_inspect', return_value='10.10.10.10'), \
                patch('conductr_cli.terminal.docker_run', return_value=''), \
                patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=running_containers), \
                patch('conductr_cli.sandbox_features.stop_features') as mock_stop_proxy, \
                patch('conductr_cli.terminal.docker_rm') as mock_docker_rm:
            logging_setup.configure_logging(input_args, stdout)
            sandbox_run_docker.run(input_args, features)

        expected_stdout = strip_margin("""||------------------------------------------------|
                                          || Stopping ConductR                              |
                                          ||------------------------------------------------|
                                          |ConductR has been successfully stopped
                                          ||------------------------------------------------|
                                          || Starting ConductR                              |
                                          ||------------------------------------------------|
                                          |Starting container cond-0..
                                          |""")

        self.assertEqual(expected_stdout, self.output(stdout))
        mock_stop_proxy.assert_called_once_with()
        mock_docker_rm.assert_called_once_with(running_containers)

    def test_run_options(self):
        stdout = MagicMock()
        run_options = {'CONDUCTR_DOCKER_RUN_OPTS': "-v /etc/haproxy:/usr/local/etc/haproxy"}

        def run_env(key, default=None):
            return run_options[key] if key in run_options else os.environ.get(key, default)

        input_args = MagicMock(**self.default_args)
        features = []
        with \
                patch('conductr_cli.terminal.docker_images', return_value=''), \
                patch('conductr_cli.terminal.docker_pull', return_value=''), \
                patch('conductr_cli.terminal.docker_ps', return_value=''), \
                patch('conductr_cli.terminal.docker_inspect', return_value='10.10.10.10'), \
                patch('conductr_cli.terminal.docker_run', return_value='') as mock_docker_run, \
                patch('conductr_cli.sandbox_features.stop_features') as mock_stop_proxy, \
                patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=[]), \
                patch('os.getenv', side_effect=run_env) as mock_get_env:
            logging_setup.configure_logging(input_args, stdout)
            sandbox_run_docker.run(input_args, features)

        expected_stdout = strip_margin("""|Pulling down the ConductR development image..
                                          ||------------------------------------------------|
                                          || Starting ConductR                              |
                                          ||------------------------------------------------|
                                          |Starting container cond-0..
                                          |""")
        expected_optional_args = self.default_general_args('cond-0') + self.default_env_args + self.default_port_args
        expected_image = '{}:{}'.format(CONDUCTR_DEV_IMAGE, LATEST_CONDUCTR_VERSION)
        expected_positional_args = self.default_positional_args

        self.assertEqual(expected_stdout, self.output(stdout))
        mock_get_env.assert_any_call('CONDUCTR_DOCKER_RUN_OPTS')
        mock_docker_run.assert_called_once_with(expected_optional_args + ['-v', '/etc/haproxy:/usr/local/etc/haproxy'],
                                                expected_image, expected_positional_args)
        mock_stop_proxy.assert_called_once_with()

    def test_invalid_nr_of_instances(self):
        args = self.default_args.copy()
        args.update({
            'nr_of_instances': 'FOO'
        })
        input_args = MagicMock(**args)
        features = []

        self.assertRaises(InstanceCountError, sandbox_run_docker.run, input_args, features)


class TestLogRunAttempt(CliTestCase):
    wait_timeout = 60
    container_names = ['cond-0', 'cond-1', 'cond-2']
    hostname = '10.0.0.1'
    run_result = sandbox_run_docker.SandboxRunResult(container_names, hostname, wait_for_conductr=False)
    feature_results = []

    def test_log_output(self):
        stdout = MagicMock()
        input_args = MagicMock(**{})

        logging_setup.configure_logging(input_args, stdout)
        sandbox_run_docker.log_run_attempt(
            input_args,
            run_result=self.run_result,
            feature_results=self.feature_results,
            feature_provided=[FEATURE_PROVIDE_PROXYING]
        )

        expected_stdout = strip_margin("""||------------------------------------------------|
                                          || Summary                                        |
                                          ||------------------------------------------------|
                                          |ConductR has been started
                                          |Check resource consumption of Docker containers that run the ConductR nodes with:
                                          |  docker stats cond-0 cond-1 cond-2
                                          |Check current bundle status with:
                                          |  conduct info
                                          |""")
        self.assertEqual(expected_stdout, self.output(stdout))

    def test_log_output_single_container(self):
        stdout = MagicMock()
        input_args = MagicMock(**{})

        logging_setup.configure_logging(input_args, stdout)
        sandbox_run_docker.log_run_attempt(
            input_args,
            run_result=sandbox_run_docker.SandboxRunResult(['cond-0'], self.hostname, wait_for_conductr=False),
            feature_results=self.feature_results,
            feature_provided=[FEATURE_PROVIDE_PROXYING]
        )

        expected_stdout = strip_margin("""||------------------------------------------------|
                                          || Summary                                        |
                                          ||------------------------------------------------|
                                          |ConductR has been started
                                          |Check resource consumption of Docker container that run the ConductR node with:
                                          |  docker stats cond-0
                                          |Check current bundle status with:
                                          |  conduct info
                                          |""")
        self.assertEqual(expected_stdout, self.output(stdout))
