from conductr_cli.test.cli_test_case import CliTestCase, as_warn
from conductr_cli import sandbox_init, logging_setup
from subprocess import CalledProcessError

try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestSandboxInitCommand(CliTestCase):

    def test_vm_not_installed(self):
        docker_machine_vm_name_mock = MagicMock(return_value='conductr')
        docker_machine_help_mock = MagicMock()
        docker_machine_env_mock = MagicMock(side_effect=CalledProcessError(-1, 'Test Only'))
        docker_machine_create_vm_mock = MagicMock()
        docker_machine_stop_vm_mock = MagicMock()
        vbox_manage_increase_ram_mock = MagicMock()
        docker_machine_start_vm_mock = MagicMock()

        with patch('conductr_cli.docker_machine.vm_name', docker_machine_vm_name_mock), \
                patch('conductr_cli.terminal.docker_machine_help', docker_machine_help_mock), \
                patch('conductr_cli.terminal.docker_machine_env', docker_machine_env_mock), \
                patch('conductr_cli.terminal.docker_machine_create_vm', docker_machine_create_vm_mock), \
                patch('conductr_cli.terminal.docker_machine_stop_vm', docker_machine_stop_vm_mock), \
                patch('conductr_cli.terminal.vbox_manage_increase_ram', vbox_manage_increase_ram_mock), \
                patch('conductr_cli.terminal.docker_machine_start_vm', docker_machine_start_vm_mock):
            sandbox_init.init(MagicMock())

        docker_machine_vm_name_mock.assert_called_with()
        docker_machine_help_mock.assert_called_with()
        docker_machine_env_mock.assert_called_with('conductr')
        docker_machine_create_vm_mock.assert_called_with('conductr')
        docker_machine_stop_vm_mock.assert_called_with('conductr')
        vbox_manage_increase_ram_mock.assert_called_with('conductr', '2048')
        docker_machine_start_vm_mock.assert_called_with('conductr')

    def test_vm_installed(self):
        docker_machine_vm_name_mock = MagicMock(return_value='conductr')
        docker_machine_help_mock = MagicMock()
        docker_machine_env_mock = MagicMock(side_effect='vm installed')

        with patch('conductr_cli.docker_machine.vm_name', docker_machine_vm_name_mock), \
                patch('conductr_cli.terminal.docker_machine_help', docker_machine_help_mock), \
                patch('conductr_cli.terminal.docker_machine_env', docker_machine_env_mock):
            sandbox_init.init(MagicMock())

        docker_machine_vm_name_mock.assert_called_with()
        docker_machine_help_mock.assert_called_with()
        docker_machine_env_mock.assert_called_with('conductr')

    def test_docker_machine_not_installed(self):
        stdout_mock = MagicMock()
        docker_machine_help_mock = MagicMock(side_effect=CalledProcessError(-1, 'test only'))

        logging_setup.configure_logging(MagicMock(), output=stdout_mock)
        with patch('conductr_cli.terminal.docker_machine_help', docker_machine_help_mock):
            sandbox_init.init(MagicMock())

        docker_machine_help_mock.assert_called_with()
        self.assertEqual(as_warn('Warning: Unable to initialize sandbox - docker-machine not installed\n'),
                         self.output(stdout_mock))
