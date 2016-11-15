from unittest import TestCase
from conductr_cli import host
from conductr_cli.docker import DockerVmType
from conductr_cli.exceptions import DockerMachineNotRunningError

try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestResolveDefaultHost(TestCase):
    def test_resolve(self):
        getenv_mock = MagicMock(return_value='test')
        resolve_default_ip_mock = MagicMock(return_value='resolve_result')
        with patch('os.getenv', getenv_mock), \
                patch('conductr_cli.host.resolve_default_ip', resolve_default_ip_mock):
            result = host.resolve_default_host()
            self.assertEqual(result, 'test')

        getenv_mock.assert_called_with('CONDUCTR_HOST', 'resolve_result')


class TestResolveDefaultIp(TestCase):
    def test_resolve(self):
        getenv_mock = MagicMock(return_value='test')
        vm_type_mock = MagicMock(return_value='vm_type')
        resolve_ip_by_vm_type_mock = MagicMock(return_value='resolve_result')
        with patch('os.getenv', getenv_mock), \
                patch('conductr_cli.docker.vm_type', vm_type_mock), \
                patch('conductr_cli.host.resolve_ip_by_vm_type', resolve_ip_by_vm_type_mock):
            result = host.resolve_default_ip()
            self.assertEqual(result, 'test')

        getenv_mock.assert_called_with('CONDUCTR_IP', 'resolve_result')
        vm_type_mock.assert_called_with()
        resolve_ip_by_vm_type_mock.assert_called_with('vm_type')


class TestResolveIpByVmType(TestCase):
    def test_vm_type_none(self):
        with_docker_machine_mock = MagicMock(return_value='result')
        with patch('conductr_cli.host.with_docker_machine', with_docker_machine_mock):
            result = host.resolve_ip_by_vm_type(DockerVmType.NONE)
            self.assertEqual(result, '127.0.0.1')

        with_docker_machine_mock.assert_not_called()

    def test_vm_type_docker_engine(self):
        with_docker_machine_mock = MagicMock(return_value='result')
        with patch('conductr_cli.host.with_docker_machine', with_docker_machine_mock):
            result = host.resolve_ip_by_vm_type(DockerVmType.DOCKER_ENGINE)
            self.assertEqual(result, '127.0.0.1')

        with_docker_machine_mock.assert_not_called()

    def test_vm_type_docker_machine(self):
        with_docker_machine_mock = MagicMock(return_value='result')
        with patch('conductr_cli.host.with_docker_machine', with_docker_machine_mock):
            result = host.resolve_ip_by_vm_type(DockerVmType.DOCKER_MACHINE)
            self.assertEqual(result, 'result')

        with_docker_machine_mock.assert_called_with()


class TestWithDockerMachine(TestCase):
    def test_success(self):
        vm_name_mock = MagicMock(return_value='vm_name')
        docker_machine_ip_mock = MagicMock(return_value='docker ip')
        with patch('conductr_cli.docker_machine.vm_name', vm_name_mock), \
                patch('conductr_cli.terminal.docker_machine_ip', docker_machine_ip_mock):
            result = host.with_docker_machine()
            self.assertEqual(result, 'docker ip')

        vm_name_mock.assert_called_with()
        docker_machine_ip_mock.assert_called_with('vm_name')

    def test_docker_machine_not_running(self):
        vm_name_mock = MagicMock(return_value='vm_name')
        docker_machine_ip_mock = MagicMock(return_value='')
        with patch('conductr_cli.docker_machine.vm_name', vm_name_mock), \
                patch('conductr_cli.terminal.docker_machine_ip', docker_machine_ip_mock):
            host.with_docker_machine()

        vm_name_mock.assert_called_with()
        docker_machine_ip_mock.assert_called_with('vm_name')

    def test_called_process_error(self):
        vm_name_mock = MagicMock(return_value='vm_name')
        docker_machine_ip_mock = MagicMock(side_effect=DockerMachineNotRunningError('test only'))
        with patch('conductr_cli.docker_machine.vm_name', vm_name_mock), \
                patch('conductr_cli.terminal.docker_machine_ip', docker_machine_ip_mock):
            host.with_docker_machine()

        vm_name_mock.assert_called_with()
        docker_machine_ip_mock.assert_called_with('vm_name')
