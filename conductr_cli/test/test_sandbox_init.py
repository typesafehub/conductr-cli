from conductr_cli.test.cli_test_case import CliTestCase, as_warn
from conductr_cli import sandbox_init, logging_setup
from subprocess import CalledProcessError

try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestSandboxInitCommand(CliTestCase):

    def test_docker_insufficient_ram(self):
        stdout_mock = MagicMock()
        docker_info_mock = MagicMock(return_value=b'\nTotal Memory: 2 GiB\nCPUs: 4')
        docker_machine_help_mock = MagicMock(side_effect=CalledProcessError(-1, 'test only'))

        logging_setup.configure_logging(MagicMock(), output=stdout_mock)
        with patch('conductr_cli.terminal.docker_info', docker_info_mock), \
                patch('conductr_cli.terminal.docker_machine_help', docker_machine_help_mock):
            sandbox_init.init(MagicMock())

        docker_info_mock.assert_called_with()
        self.assertEqual(
            as_warn("Warning: Docker has insufficient RAM of 2.0MiB - please increase to a minimum of 3.8MiB\n"),
            self.output(stdout_mock))

    def test_docker_insufficient_cpu(self):
        stdout_mock = MagicMock()
        docker_info_mock = MagicMock(return_value=b'\nTotal Memory: 3.8 GiB\nCPUs: 3')
        docker_machine_help_mock = MagicMock(side_effect=CalledProcessError(-1, 'test only'))

        logging_setup.configure_logging(MagicMock(), output=stdout_mock)
        with patch('conductr_cli.terminal.docker_info', docker_info_mock), \
                patch('conductr_cli.terminal.docker_machine_help', docker_machine_help_mock):
            sandbox_init.init(MagicMock())

        docker_info_mock.assert_called_with()
        self.assertEqual(
            as_warn("Warning: Docker has an insufficient no. of CPUs 3 - please increase to a minimum of 4 CPUs\n"),
            self.output(stdout_mock))

    def test_docker_sufficient_ram_and_cpu(self):
        stdout_mock = MagicMock()
        docker_info_mock = MagicMock(return_value=b'\nTotal Memory: 3.8 GiB\nCPUs: 4')
        docker_machine_help_mock = MagicMock(side_effect=CalledProcessError(-1, 'test only'))

        logging_setup.configure_logging(MagicMock(), output=stdout_mock)
        with patch('conductr_cli.terminal.docker_info', docker_info_mock), \
                patch('conductr_cli.terminal.docker_machine_help', docker_machine_help_mock):
            sandbox_init.init(MagicMock())

        docker_info_mock.assert_called_with()
        self.assertEqual("Docker already has sufficient RAM and CPUs\n", self.output(stdout_mock))

    def test_docker_machine_vm_not_installed(self):
        docker_info_mock = MagicMock(side_effect=CalledProcessError(-1, 'test only'))
        docker_machine_vm_name_mock = MagicMock(return_value='vm_name')
        docker_machine_help_mock = MagicMock()
        # Once VM is created, it will be in the running state
        docker_machine_status_mock = MagicMock(side_effect=[CalledProcessError(-1, 'Test Only'), 'Running'])
        # Default RAM size when VM is created is 1024MB
        vbox_manage_get_ram_size_mock = MagicMock(return_value=1024)
        # Default no of CPU when VM is created is 1
        vbox_manage_get_cpu_count_mock = MagicMock(return_value=1)
        docker_machine_create_vm_mock = MagicMock()
        docker_machine_stop_vm_mock = MagicMock()
        vbox_manage_increase_ram_mock = MagicMock()
        vbox_manage_increase_cpu_mock = MagicMock()
        docker_machine_start_vm_mock = MagicMock()

        with patch('conductr_cli.terminal.docker_info', docker_info_mock), \
                patch('conductr_cli.docker_machine.vm_name', docker_machine_vm_name_mock), \
                patch('conductr_cli.terminal.docker_machine_help', docker_machine_help_mock), \
                patch('conductr_cli.terminal.docker_machine_status', docker_machine_status_mock), \
                patch('conductr_cli.terminal.vbox_manage_get_ram_size', vbox_manage_get_ram_size_mock), \
                patch('conductr_cli.terminal.vbox_manage_get_cpu_count', vbox_manage_get_cpu_count_mock), \
                patch('conductr_cli.terminal.docker_machine_create_vm', docker_machine_create_vm_mock), \
                patch('conductr_cli.terminal.docker_machine_stop_vm', docker_machine_stop_vm_mock), \
                patch('conductr_cli.terminal.vbox_manage_increase_ram', vbox_manage_increase_ram_mock), \
                patch('conductr_cli.terminal.vbox_manage_increase_cpu', vbox_manage_increase_cpu_mock), \
                patch('conductr_cli.terminal.docker_machine_start_vm', docker_machine_start_vm_mock):
            sandbox_init.init(MagicMock())

        docker_machine_vm_name_mock.assert_called_with()
        docker_machine_help_mock.assert_called_with()
        docker_machine_status_mock.assert_called_with('vm_name')
        docker_machine_create_vm_mock.assert_called_with('vm_name')
        vbox_manage_get_ram_size_mock.assert_called_with('vm_name')
        vbox_manage_get_cpu_count_mock.assert_called_with('vm_name')
        docker_machine_stop_vm_mock.assert_called_with('vm_name')
        vbox_manage_increase_ram_mock.assert_called_with('vm_name', '4096')
        vbox_manage_increase_cpu_mock.assert_called_with('vm_name', '4')
        docker_machine_start_vm_mock.assert_called_with('vm_name')

    def test_docker_machine_stopped(self):
        docker_info_mock = MagicMock(side_effect=CalledProcessError(-1, 'test only'))
        docker_machine_vm_name_mock = MagicMock(return_value='vm_name')
        docker_machine_help_mock = MagicMock()
        docker_machine_status_mock = MagicMock(return_value='Stopped')
        vbox_manage_get_ram_size_mock = MagicMock(return_value=4096)
        vbox_manage_get_cpu_count_mock = MagicMock(return_value=4)
        docker_machine_start_vm_mock = MagicMock()

        with patch('conductr_cli.terminal.docker_info', docker_info_mock), \
                patch('conductr_cli.docker_machine.vm_name', docker_machine_vm_name_mock), \
                patch('conductr_cli.terminal.docker_machine_help', docker_machine_help_mock), \
                patch('conductr_cli.terminal.vbox_manage_get_ram_size', vbox_manage_get_ram_size_mock), \
                patch('conductr_cli.terminal.vbox_manage_get_cpu_count', vbox_manage_get_cpu_count_mock), \
                patch('conductr_cli.terminal.docker_machine_status', docker_machine_status_mock), \
                patch('conductr_cli.terminal.docker_machine_start_vm', docker_machine_start_vm_mock):
            sandbox_init.init(MagicMock())

        docker_machine_vm_name_mock.assert_called_with()
        docker_machine_help_mock.assert_called_with()
        docker_machine_status_mock.assert_called_with('vm_name')
        vbox_manage_get_ram_size_mock.assert_called_with('vm_name')
        vbox_manage_get_cpu_count_mock.assert_called_with('vm_name')
        docker_machine_start_vm_mock.assert_called_with('vm_name')

    def test_docker_machine_insufficient_ram(self):
        docker_info_mock = MagicMock(side_effect=CalledProcessError(-1, 'test only'))
        docker_machine_vm_name_mock = MagicMock(return_value='vm_name')
        docker_machine_help_mock = MagicMock()
        docker_machine_status_mock = MagicMock(return_value='Running')
        vbox_manage_get_ram_size_mock = MagicMock(return_value=1024)
        vbox_manage_get_cpu_count_mock = MagicMock(return_value=4)
        docker_machine_stop_vm_mock = MagicMock()
        vbox_manage_increase_ram_mock = MagicMock()
        docker_machine_start_vm_mock = MagicMock()

        with patch('conductr_cli.terminal.docker_info', docker_info_mock), \
                patch('conductr_cli.docker_machine.vm_name', docker_machine_vm_name_mock), \
                patch('conductr_cli.terminal.docker_machine_help', docker_machine_help_mock), \
                patch('conductr_cli.terminal.vbox_manage_get_ram_size', vbox_manage_get_ram_size_mock), \
                patch('conductr_cli.terminal.vbox_manage_get_cpu_count', vbox_manage_get_cpu_count_mock), \
                patch('conductr_cli.terminal.docker_machine_status', docker_machine_status_mock), \
                patch('conductr_cli.terminal.docker_machine_stop_vm', docker_machine_stop_vm_mock), \
                patch('conductr_cli.terminal.vbox_manage_increase_ram', vbox_manage_increase_ram_mock), \
                patch('conductr_cli.terminal.docker_machine_start_vm', docker_machine_start_vm_mock):
            sandbox_init.init(MagicMock())

        docker_machine_vm_name_mock.assert_called_with()
        docker_machine_help_mock.assert_called_with()
        docker_machine_status_mock.assert_called_with('vm_name')
        vbox_manage_get_ram_size_mock.assert_called_with('vm_name')
        vbox_manage_get_cpu_count_mock.assert_called_with('vm_name')
        docker_machine_stop_vm_mock.assert_called_with('vm_name')
        vbox_manage_increase_ram_mock.assert_called_with('vm_name', '4096')
        docker_machine_start_vm_mock.assert_called_with('vm_name')

    def test_docker_machine_insufficient_cpu(self):
        docker_info_mock = MagicMock(side_effect=CalledProcessError(-1, 'test only'))
        docker_machine_vm_name_mock = MagicMock(return_value='vm_name')
        docker_machine_help_mock = MagicMock()
        docker_machine_status_mock = MagicMock(return_value='Running')
        vbox_manage_get_ram_size_mock = MagicMock(return_value=4096)
        vbox_manage_get_cpu_count_mock = MagicMock(return_value=1)
        docker_machine_stop_vm_mock = MagicMock()
        vbox_manage_increase_cpu_mock = MagicMock()
        docker_machine_start_vm_mock = MagicMock()

        with patch('conductr_cli.terminal.docker_info', docker_info_mock), \
                patch('conductr_cli.docker_machine.vm_name', docker_machine_vm_name_mock), \
                patch('conductr_cli.terminal.docker_machine_help', docker_machine_help_mock), \
                patch('conductr_cli.terminal.vbox_manage_get_ram_size', vbox_manage_get_ram_size_mock), \
                patch('conductr_cli.terminal.vbox_manage_get_cpu_count', vbox_manage_get_cpu_count_mock), \
                patch('conductr_cli.terminal.docker_machine_status', docker_machine_status_mock), \
                patch('conductr_cli.terminal.docker_machine_stop_vm', docker_machine_stop_vm_mock), \
                patch('conductr_cli.terminal.vbox_manage_increase_cpu', vbox_manage_increase_cpu_mock), \
                patch('conductr_cli.terminal.docker_machine_start_vm', docker_machine_start_vm_mock):
            sandbox_init.init(MagicMock())

        docker_machine_vm_name_mock.assert_called_with()
        docker_machine_help_mock.assert_called_with()
        docker_machine_status_mock.assert_called_with('vm_name')
        vbox_manage_get_ram_size_mock.assert_called_with('vm_name')
        vbox_manage_get_cpu_count_mock.assert_called_with('vm_name')
        docker_machine_stop_vm_mock.assert_called_with('vm_name')
        vbox_manage_increase_cpu_mock.assert_called_with('vm_name', '4')
        docker_machine_start_vm_mock.assert_called_with('vm_name')

    def test_docker_machine_installed_and_running_with_sufficient_ram_and_cpu(self):
        docker_info_mock = MagicMock(side_effect=CalledProcessError(-1, 'test only'))
        docker_machine_vm_name_mock = MagicMock(return_value='vm_name')
        docker_machine_help_mock = MagicMock()
        docker_machine_status_mock = MagicMock(return_value='Running')
        vbox_manage_get_ram_size_mock = MagicMock(return_value=4096)
        vbox_manage_get_cpu_count_mock = MagicMock(return_value=4)

        with patch('conductr_cli.terminal.docker_info', docker_info_mock), \
                patch('conductr_cli.docker_machine.vm_name', docker_machine_vm_name_mock), \
                patch('conductr_cli.terminal.docker_machine_help', docker_machine_help_mock), \
                patch('conductr_cli.terminal.vbox_manage_get_ram_size', vbox_manage_get_ram_size_mock), \
                patch('conductr_cli.terminal.vbox_manage_get_cpu_count', vbox_manage_get_cpu_count_mock), \
                patch('conductr_cli.terminal.docker_machine_status', docker_machine_status_mock):
            sandbox_init.init(MagicMock())

        docker_machine_vm_name_mock.assert_called_with()
        docker_machine_help_mock.assert_called_with()
        docker_machine_status_mock.assert_called_with('vm_name')
        vbox_manage_get_ram_size_mock.assert_called_with('vm_name')
        vbox_manage_get_cpu_count_mock.assert_called_with('vm_name')

    def test_docker_machine_not_installed(self):
        stdout_mock = MagicMock()
        docker_info_mock = MagicMock(side_effect=CalledProcessError(-1, 'test only'))
        docker_machine_help_mock = MagicMock(side_effect=CalledProcessError(-1, 'test only'))

        logging_setup.configure_logging(MagicMock(), output=stdout_mock)
        with patch('conductr_cli.terminal.docker_info', docker_info_mock), \
                patch('conductr_cli.terminal.docker_machine_help', docker_machine_help_mock):
            sandbox_init.init(MagicMock())

        docker_machine_help_mock.assert_called_with()
        self.assertEqual("", self.output(stdout_mock))
