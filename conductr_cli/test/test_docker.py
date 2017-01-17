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
                """|Error: Docker native is installed but not running.
                   |Error: Please start Docker with one of the Docker flavors based on your OS:
                   |Error:   Linux:   Docker service
                   |Error:   MacOS:   Docker for Mac
                   |Error:   Windows: Docker for Windows
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

    def test_docker_machine_vm_not_exist(self):
        docker_info_mock = MagicMock(return_value='test_only')
        docker_machine_vm_name_mock = MagicMock(return_value='vm_name')
        # Once VM is created, it will be in the running state
        docker_machine_status_mock = MagicMock(side_effect=CalledProcessError(-1, 'test only'))
        docker_machine_running_check_mock = MagicMock(return_value=True)
        # Default RAM size when VM is created is 1024MB
        vbox_manage_get_ram_size_mock = MagicMock(return_value=1024)
        # Default no of CPU when VM is created is 1
        vbox_manage_get_cpu_count_mock = MagicMock(return_value=1)
        docker_machine_create_vm_mock = MagicMock()
        docker_machine_stop_vm_mock = MagicMock()
        vbox_manage_increase_ram_mock = MagicMock()
        vbox_manage_increase_cpu_mock = MagicMock()
        docker_machine_start_vm_mock = MagicMock()

        with \
                patch('conductr_cli.terminal.docker_info', docker_info_mock), \
                patch('conductr_cli.docker_machine.vm_name', docker_machine_vm_name_mock), \
                patch('conductr_cli.docker_machine.running_check', docker_machine_running_check_mock), \
                patch('conductr_cli.terminal.docker_machine_status', docker_machine_status_mock), \
                patch('conductr_cli.terminal.vbox_manage_get_ram_size', vbox_manage_get_ram_size_mock), \
                patch('conductr_cli.terminal.vbox_manage_get_cpu_count', vbox_manage_get_cpu_count_mock), \
                patch('conductr_cli.terminal.docker_machine_create_vm', docker_machine_create_vm_mock), \
                patch('conductr_cli.terminal.docker_machine_stop_vm', docker_machine_stop_vm_mock), \
                patch('conductr_cli.terminal.vbox_manage_increase_ram', vbox_manage_increase_ram_mock), \
                patch('conductr_cli.terminal.vbox_manage_increase_cpu', vbox_manage_increase_cpu_mock), \
                patch('conductr_cli.terminal.docker_machine_start_vm', docker_machine_start_vm_mock):
            docker.validate_docker_vm(DockerVmType.DOCKER_MACHINE)

        docker_machine_vm_name_mock.assert_called_with()
        docker_machine_status_mock.assert_called_with('vm_name')
        docker_machine_create_vm_mock.assert_called_with('vm_name')
        vbox_manage_get_ram_size_mock.assert_called_with('vm_name')
        vbox_manage_get_cpu_count_mock.assert_called_with('vm_name')
        docker_machine_stop_vm_mock.assert_called_with('vm_name')
        vbox_manage_increase_ram_mock.assert_called_with('vm_name', '4096')
        vbox_manage_increase_cpu_mock.assert_called_with('vm_name', '4')
        docker_machine_start_vm_mock.assert_called_with('vm_name')

    def test_docker_machine_vm_not_exist_in_docker_machine(self):
        docker_info_mock = MagicMock(return_value='test_only')
        docker_machine_vm_name_mock = MagicMock(return_value='vm_name')
        # Once VM is created, it will be in the running state
        docker_machine_status_mock = MagicMock(return_value='Error')
        docker_machine_running_check_mock = MagicMock(return_value=True)
        # Default RAM size when VM is created is 1024MB
        vbox_manage_get_ram_size_mock = MagicMock(return_value=1024)
        # Default no of CPU when VM is created is 1
        vbox_manage_get_cpu_count_mock = MagicMock(return_value=1)
        docker_machine_create_vm_mock = MagicMock()
        docker_machine_stop_vm_mock = MagicMock()
        vbox_manage_increase_ram_mock = MagicMock()
        vbox_manage_increase_cpu_mock = MagicMock()
        docker_machine_start_vm_mock = MagicMock()

        with \
                patch('conductr_cli.terminal.docker_info', docker_info_mock), \
                patch('conductr_cli.docker_machine.vm_name', docker_machine_vm_name_mock), \
                patch('conductr_cli.docker_machine.running_check', docker_machine_running_check_mock), \
                patch('conductr_cli.terminal.docker_machine_status', docker_machine_status_mock), \
                patch('conductr_cli.terminal.vbox_manage_get_ram_size', vbox_manage_get_ram_size_mock), \
                patch('conductr_cli.terminal.vbox_manage_get_cpu_count', vbox_manage_get_cpu_count_mock), \
                patch('conductr_cli.terminal.docker_machine_create_vm', docker_machine_create_vm_mock), \
                patch('conductr_cli.terminal.docker_machine_stop_vm', docker_machine_stop_vm_mock), \
                patch('conductr_cli.terminal.vbox_manage_increase_ram', vbox_manage_increase_ram_mock), \
                patch('conductr_cli.terminal.vbox_manage_increase_cpu', vbox_manage_increase_cpu_mock), \
                patch('conductr_cli.terminal.docker_machine_start_vm', docker_machine_start_vm_mock):
            docker.validate_docker_vm(DockerVmType.DOCKER_MACHINE)

        docker_machine_vm_name_mock.assert_called_with()
        docker_machine_status_mock.assert_called_with('vm_name')
        docker_machine_create_vm_mock.assert_called_with('vm_name')
        vbox_manage_get_ram_size_mock.assert_called_with('vm_name')
        vbox_manage_get_cpu_count_mock.assert_called_with('vm_name')
        docker_machine_stop_vm_mock.assert_called_with('vm_name')
        vbox_manage_increase_ram_mock.assert_called_with('vm_name', '4096')
        vbox_manage_increase_cpu_mock.assert_called_with('vm_name', '4')
        docker_machine_start_vm_mock.assert_called_with('vm_name')

    def test_docker_machine_stopped(self):
        docker_info_mock = MagicMock(return_value='test_only')
        docker_machine_vm_name_mock = MagicMock(return_value='vm_name')
        docker_machine_status_mock = MagicMock(return_value='Stopped')
        vbox_manage_get_ram_size_mock = MagicMock(return_value=4096)
        vbox_manage_get_cpu_count_mock = MagicMock(return_value=4)
        docker_machine_start_vm_mock = MagicMock()

        with \
                patch('conductr_cli.terminal.docker_info', docker_info_mock), \
                patch('conductr_cli.docker_machine.vm_name', docker_machine_vm_name_mock), \
                patch('conductr_cli.terminal.vbox_manage_get_ram_size', vbox_manage_get_ram_size_mock), \
                patch('conductr_cli.terminal.vbox_manage_get_cpu_count', vbox_manage_get_cpu_count_mock), \
                patch('conductr_cli.terminal.docker_machine_status', docker_machine_status_mock), \
                patch('conductr_cli.terminal.docker_machine_start_vm', docker_machine_start_vm_mock):
            docker.validate_docker_vm(DockerVmType.DOCKER_MACHINE)

        docker_machine_vm_name_mock.assert_called_with()
        docker_machine_status_mock.assert_called_with('vm_name')
        vbox_manage_get_ram_size_mock.assert_called_with('vm_name')
        vbox_manage_get_cpu_count_mock.assert_called_with('vm_name')
        docker_machine_start_vm_mock.assert_called_with('vm_name')

    def test_docker_machine_insufficient_ram(self):
        docker_info_mock = MagicMock(return_value='test_only')
        docker_machine_vm_name_mock = MagicMock(return_value='vm_name')
        docker_machine_status_mock = MagicMock(return_value='Running')
        vbox_manage_get_ram_size_mock = MagicMock(return_value=1024)
        vbox_manage_get_cpu_count_mock = MagicMock(return_value=4)
        docker_machine_stop_vm_mock = MagicMock()
        vbox_manage_increase_ram_mock = MagicMock()
        docker_machine_start_vm_mock = MagicMock()

        with \
                patch('conductr_cli.terminal.docker_info', docker_info_mock), \
                patch('conductr_cli.docker_machine.vm_name', docker_machine_vm_name_mock), \
                patch('conductr_cli.terminal.vbox_manage_get_ram_size', vbox_manage_get_ram_size_mock), \
                patch('conductr_cli.terminal.vbox_manage_get_cpu_count', vbox_manage_get_cpu_count_mock), \
                patch('conductr_cli.terminal.docker_machine_status', docker_machine_status_mock), \
                patch('conductr_cli.terminal.docker_machine_stop_vm', docker_machine_stop_vm_mock), \
                patch('conductr_cli.terminal.vbox_manage_increase_ram', vbox_manage_increase_ram_mock), \
                patch('conductr_cli.terminal.docker_machine_start_vm', docker_machine_start_vm_mock):
            docker.validate_docker_vm(DockerVmType.DOCKER_MACHINE)

        docker_machine_vm_name_mock.assert_called_with()
        docker_machine_status_mock.assert_called_with('vm_name')
        vbox_manage_get_ram_size_mock.assert_called_with('vm_name')
        vbox_manage_get_cpu_count_mock.assert_called_with('vm_name')
        docker_machine_stop_vm_mock.assert_called_with('vm_name')
        vbox_manage_increase_ram_mock.assert_called_with('vm_name', '4096')
        docker_machine_start_vm_mock.assert_called_with('vm_name')

    def test_docker_machine_insufficient_cpu(self):
        docker_info_mock = MagicMock(return_value='test_only')
        docker_machine_vm_name_mock = MagicMock(return_value='vm_name')
        docker_machine_status_mock = MagicMock(return_value='Running')
        vbox_manage_get_ram_size_mock = MagicMock(return_value=4096)
        vbox_manage_get_cpu_count_mock = MagicMock(return_value=1)
        docker_machine_stop_vm_mock = MagicMock()
        vbox_manage_increase_cpu_mock = MagicMock()
        docker_machine_start_vm_mock = MagicMock()

        with \
                patch('conductr_cli.terminal.docker_info', docker_info_mock), \
                patch('conductr_cli.docker_machine.vm_name', docker_machine_vm_name_mock), \
                patch('conductr_cli.terminal.vbox_manage_get_ram_size', vbox_manage_get_ram_size_mock), \
                patch('conductr_cli.terminal.vbox_manage_get_cpu_count', vbox_manage_get_cpu_count_mock), \
                patch('conductr_cli.terminal.docker_machine_status', docker_machine_status_mock), \
                patch('conductr_cli.terminal.docker_machine_stop_vm', docker_machine_stop_vm_mock), \
                patch('conductr_cli.terminal.vbox_manage_increase_cpu', vbox_manage_increase_cpu_mock), \
                patch('conductr_cli.terminal.docker_machine_start_vm', docker_machine_start_vm_mock):
            docker.validate_docker_vm(DockerVmType.DOCKER_MACHINE)

        docker_machine_vm_name_mock.assert_called_with()
        docker_machine_status_mock.assert_called_with('vm_name')
        vbox_manage_get_ram_size_mock.assert_called_with('vm_name')
        vbox_manage_get_cpu_count_mock.assert_called_with('vm_name')
        docker_machine_stop_vm_mock.assert_called_with('vm_name')
        vbox_manage_increase_cpu_mock.assert_called_with('vm_name', '4')
        docker_machine_start_vm_mock.assert_called_with('vm_name')

    def test_docker_machine_installed_and_running_with_sufficient_ram_and_cpu(self):
        docker_info_mock = MagicMock(return_value='test_only')
        docker_machine_vm_name_mock = MagicMock(return_value='vm_name')
        docker_machine_status_mock = MagicMock(return_value='Running')
        vbox_manage_get_ram_size_mock = MagicMock(return_value=4096)
        vbox_manage_get_cpu_count_mock = MagicMock(return_value=4)

        with \
                patch('conductr_cli.terminal.docker_info', docker_info_mock), \
                patch('conductr_cli.docker_machine.vm_name', docker_machine_vm_name_mock), \
                patch('conductr_cli.terminal.vbox_manage_get_ram_size', vbox_manage_get_ram_size_mock), \
                patch('conductr_cli.terminal.vbox_manage_get_cpu_count', vbox_manage_get_cpu_count_mock), \
                patch('conductr_cli.terminal.docker_machine_status', docker_machine_status_mock):
            docker.validate_docker_vm(DockerVmType.DOCKER_MACHINE)

        docker_machine_vm_name_mock.assert_called_with()
        docker_machine_status_mock.assert_called_with('vm_name')
        vbox_manage_get_ram_size_mock.assert_called_with('vm_name')
        vbox_manage_get_cpu_count_mock.assert_called_with('vm_name')

    def test_no_vm_found(self):
        stdout_mock = MagicMock()
        logging_setup.configure_logging(MagicMock(), err_output=stdout_mock)

        with self.assertRaises(SystemExit) as system_exit:
            docker.validate_docker_vm(DockerVmType.NONE)

        self.assertEqual(
            as_error(strip_margin(
                """|Error: Neither Docker native is installed nor the Docker machine environment variables are set.
                   |Error: We recommend to use one of following the Docker distributions depending on your OS:
                   |Error:   Linux:                                         Docker Engine
                   |Error:   MacOS:                                         Docker for Mac
                   |Error:   Windows 10+ Professional or Enterprise 64-bit: Docker for Windows
                   |Error:   Other Windows:                                 Docker machine via Docker Toolbox
                   |Error: For more information checkout: https://www.docker.com/products/overview
                   |""")),
            self.output(stdout_mock))
        self.assertEqual(system_exit.exception.code, 1)
