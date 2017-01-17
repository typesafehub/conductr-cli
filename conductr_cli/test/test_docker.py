from unittest.mock import patch, MagicMock
from subprocess import CalledProcessError
from conductr_cli import logging_setup, docker
from conductr_cli.test.cli_test_case import CliTestCase, as_error, as_warn, strip_margin
from conductr_cli.docker import DockerVmType


class TestDocker(CliTestCase):
    def test_docker_not_running(self):
        stdout_mock = MagicMock()
        docker_info_mock = MagicMock(side_effect=CalledProcessError(-1, 'test only'))

        logging_setup.configure_logging(MagicMock(), err_output=stdout_mock)

        with \
                patch('conductr_cli.terminal.docker_info', docker_info_mock), \
                self.assertRaises(SystemExit) as system_exit:
            docker.validate_docker_vm(DockerVmType.DOCKER_ENGINE)

        docker_info_mock.assert_called_with()
        self.assertEqual(
            as_error(strip_margin(
                """|Error: Docker is installed but not running.
                   |Error: Please start Docker with one of the Docker flavors based on your OS:
                   |Error:   Linux:   Docker service
                   |Error:   MacOS:   Docker for Mac
                   |Error: A successful Docker startup can be verified with: docker info
                   |""")),
            self.output(stdout_mock))
        self.assertEqual(system_exit.exception.code, 1)

    def test_docker_insufficient_ram(self):
        stdout_mock = MagicMock()
        docker_info_mock = MagicMock(return_value=b'\nTotal Memory: 2 GiB\nCPUs: 4')

        logging_setup.configure_logging(MagicMock(), output=stdout_mock)

        with patch('conductr_cli.terminal.docker_info', docker_info_mock):
            docker.validate_docker_vm(DockerVmType.DOCKER_ENGINE)

        docker_info_mock.assert_called_with()

    def test_docker_insufficient_cpu(self):
        stdout_mock = MagicMock()
        docker_info_mock = MagicMock(return_value=b'\nTotal Memory: 3.8 GiB\nCPUs: 3')

        logging_setup.configure_logging(MagicMock(), output=stdout_mock)

        with patch('conductr_cli.terminal.docker_info', docker_info_mock):
            docker.validate_docker_vm(DockerVmType.DOCKER_ENGINE)

        docker_info_mock.assert_called_with()
        self.assertEqual(
            as_warn('Warning: Docker has an insufficient no. of CPUs 3 - please increase to a minimum of 4 CPUs\n'),
            self.output(stdout_mock))

    def test_docker_sufficient_ram_and_cpu(self):
        stdout_mock = MagicMock()
        docker_info_mock = MagicMock(return_value=b'\nTotal Memory: 3.8 GiB\nCPUs: 4')

        logging_setup.configure_logging(MagicMock(), output=stdout_mock)

        with patch('conductr_cli.terminal.docker_info', docker_info_mock):
            docker.validate_docker_vm(DockerVmType.DOCKER_ENGINE)

        docker_info_mock.assert_called_with()
        self.assertEqual('', self.output(stdout_mock))

    def test_docker_machine_vm_found(self):
        stdout_mock = MagicMock()
        logging_setup.configure_logging(MagicMock(), err_output=stdout_mock)

        with self.assertRaises(SystemExit) as system_exit:
            docker.validate_docker_vm(DockerVmType.DOCKER_MACHINE)

        self.assertEqual(
            as_error(strip_margin(
                """|Error: Docker machine envs are set but Docker machine is not supported by the conductr-cli.
                   |Error: We recommend to use one of following the Docker distributions depending on your OS:
                   |Error:   Linux:                                         Docker Engine
                   |Error:   MacOS:                                         Docker for Mac
                   |Error: For more information checkout: https://www.docker.com/products/overview
                   |""")),
            self.output(stdout_mock))
        self.assertEqual(system_exit.exception.code, 1)

    def test_no_vm_found(self):
        stdout_mock = MagicMock()
        logging_setup.configure_logging(MagicMock(), err_output=stdout_mock)

        with self.assertRaises(SystemExit) as system_exit:
            docker.validate_docker_vm(DockerVmType.NONE)

        self.assertEqual(
            as_error(strip_margin(
                """|Error: Docker is not installed.
                   |Error: We recommend to use one of following the Docker distributions depending on your OS:
                   |Error:   Linux:                                         Docker Engine
                   |Error:   MacOS:                                         Docker for Mac
                   |Error: For more information checkout: https://www.docker.com/products/overview
                   |""")),
            self.output(stdout_mock))
        self.assertEqual(system_exit.exception.code, 1)
