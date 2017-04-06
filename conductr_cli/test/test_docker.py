from unittest.mock import patch, MagicMock
from subprocess import CalledProcessError
from conductr_cli import logging_setup, docker
from conductr_cli.exceptions import DockerValidationError
from conductr_cli.test.cli_test_case import CliTestCase, as_warn
from conductr_cli.docker import DockerVmType


class TestDocker(CliTestCase):
    def test_docker_not_running(self):
        stdout_mock = MagicMock()
        docker_info_mock = MagicMock(side_effect=CalledProcessError(-1, 'test only'))

        logging_setup.configure_logging(MagicMock(), err_output=stdout_mock)

        with \
                patch('conductr_cli.terminal.docker_info', docker_info_mock), \
                self.assertRaises(DockerValidationError) as error:
            docker.validate_docker_vm(DockerVmType.DOCKER_ENGINE)

        docker_info_mock.assert_called_with()
        self.assertEqual([
            'Docker is installed but not running.',
            'Please start Docker with one of the Docker flavors based on your OS:',
            '  Linux:   Docker service',
            '  MacOS:   Docker for Mac',
            'A successful Docker startup can be verified with: docker info',
        ], error.exception.messages)

    def test_docker_insufficient_ram(self):
        stdout_mock = MagicMock()
        docker_info_mock = MagicMock(return_value=b'\nTotal Memory: 2 GiB\nCPUs: 4')

        logging_setup.configure_logging(MagicMock(), output=stdout_mock)

        with patch('conductr_cli.terminal.docker_info', docker_info_mock):
            docker.validate_docker_vm(DockerVmType.DOCKER_ENGINE)

        docker_info_mock.assert_called_with()

    def test_docker_insufficient_cpu(self):
        stdout_mock = MagicMock()
        docker_info_mock = MagicMock(return_value=b'\nTotal Memory: 3.8 GiB\nCPUs: 1')

        logging_setup.configure_logging(MagicMock(), output=stdout_mock)

        with patch('conductr_cli.terminal.docker_info', docker_info_mock):
            docker.validate_docker_vm(DockerVmType.DOCKER_ENGINE)

        docker_info_mock.assert_called_with()
        self.assertEqual(
            as_warn('Warning: Docker has an insufficient no. of CPUs 1 - please increase to a minimum of 2 CPUs\n'),
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

        with self.assertRaises(DockerValidationError) as error:
            docker.validate_docker_vm(DockerVmType.DOCKER_MACHINE)

        self.assertEqual([
            'Docker machine envs are set but Docker machine is not supported by the conductr-cli.',
            'We recommend to use one of following the Docker distributions depending on your OS:',
            '  Linux:                                         Docker Engine',
            '  MacOS:                                         Docker for Mac',
            'For more information checkout: https://www.docker.com/products/overview'
        ], error.exception.messages)

    def test_no_vm_found(self):
        stdout_mock = MagicMock()
        logging_setup.configure_logging(MagicMock(), err_output=stdout_mock)

        with self.assertRaises(DockerValidationError) as error:
            docker.validate_docker_vm(DockerVmType.NONE)

        self.assertEqual([
            'Docker is not installed.',
            'We recommend to use one of following the Docker distributions depending on your OS:',
            '  Linux:                                         Docker Engine',
            '  MacOS:                                         Docker for Mac',
            'For more information checkout: https://www.docker.com/products/overview'
        ], error.exception.messages)

    def test_present(self):
        mock_vm_type = MagicMock(return_value=docker.DockerVmType.DOCKER_ENGINE)
        mock_validate_docker_vm = MagicMock()

        with \
                patch('conductr_cli.docker.vm_type', mock_vm_type), \
                patch('conductr_cli.docker.validate_docker_vm', mock_validate_docker_vm):
            self.assertTrue(docker.is_docker_present())

        mock_vm_type.assert_called_once_with()
        mock_validate_docker_vm.assert_called_once_with(docker.DockerVmType.DOCKER_ENGINE)

    def test_not_present(self):
        mock_vm_type = MagicMock(return_value=docker.DockerVmType.DOCKER_ENGINE)
        mock_validate_docker_vm = MagicMock(side_effect=DockerValidationError([]))

        with \
                patch('conductr_cli.docker.vm_type', mock_vm_type), \
                patch('conductr_cli.docker.validate_docker_vm', mock_validate_docker_vm):
            self.assertFalse(docker.is_docker_present())

        mock_vm_type.assert_called_once_with()
        mock_validate_docker_vm.assert_called_once_with(docker.DockerVmType.DOCKER_ENGINE)
