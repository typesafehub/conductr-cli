import subprocess
from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import terminal


try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestTerminal(CliTestCase):

    def test_docker_info(self):
        output = "test"
        check_output_mock = MagicMock(return_value='{}\n'.format(output))

        with patch('subprocess.check_output', check_output_mock):
            result = terminal.docker_info()

        self.assertEqual(result, output)
        check_output_mock.assert_called_with(['docker', 'info'], stderr=subprocess.DEVNULL)

    def test_docker_images(self):
        image = 'my-image-id'

        check_output_mock = MagicMock(return_value='{}\n'.format(image))

        with patch('subprocess.check_output', check_output_mock):
            result = terminal.docker_images(image)

        self.assertEqual(result, image)
        check_output_mock.assert_called_with(['docker', 'images', '--quiet', image], stderr=subprocess.DEVNULL)

    def test_docker_pull(self):
        image = 'image:version'
        stdout = MagicMock()
        subprocess_call_mock = MagicMock()

        with patch('subprocess.call', subprocess_call_mock), \
                patch('sys.stdout', stdout):
            terminal.docker_pull(image)

        self.assertEqual('', self.output(stdout))
        subprocess_call_mock.assert_called_with(['docker', 'pull', image])

    def test_docker_ps(self):
        ps_filter = 'name=cond-'
        image1 = 'image-id1'
        image2 = 'image-id2'

        check_output_mock = MagicMock(return_value='{}\n{}\n'.format(image1, image2))

        with patch('subprocess.check_output', check_output_mock):
            result = terminal.docker_ps(ps_filter)

        self.assertEqual(result, [image1, image2])
        check_output_mock.assert_called_with(['docker', 'ps', '--all', '--quiet', '--filter', ps_filter],
                                             universal_newlines=True, stderr=subprocess.DEVNULL)

    def test_docker_inspect(self):
        container_id = 'cond-0'
        inspect_format = '{{.NetworkSettings.IPAddress}}'
        ip = '172.17.0.20'

        check_output_mock = MagicMock(return_value='{}\n'.format(ip))

        with patch('subprocess.check_output', check_output_mock):
            result = terminal.docker_inspect(container_id, inspect_format)

        self.assertEqual(result, ip)
        check_output_mock.assert_called_with(['docker', 'inspect', '--format', '{{.NetworkSettings.IPAddress}}',
                                              container_id], universal_newlines=True)

    def test_docker_run(self):
        optional_args = ['-p', '9001:9001', '-e', 'AKKA_LOGLEVEL=info']
        image = 'image:version'
        positional_args = ['--discover-host-ip']
        stdout = MagicMock()
        subprocess_call_mock = MagicMock()

        with patch('subprocess.call', subprocess_call_mock), \
                patch('sys.stdout', stdout):
            terminal.docker_run(optional_args, image, positional_args)

        self.assertEqual('', self.output(stdout))
        subprocess_call_mock.assert_called_with(['docker', 'run'] + optional_args + [image] + positional_args)

    def test_docker_rm(self):
        containers = ['cond-0', 'cond-1']
        stdout = MagicMock()
        subprocess_call_mock = MagicMock()

        with patch('subprocess.call', subprocess_call_mock), \
                patch('sys.stdout', stdout):
            terminal.docker_rm(containers)

        self.assertEqual('', self.output(stdout))
        subprocess_call_mock.assert_called_with(['docker', 'rm', '-f'] + containers)

    def test_docker_machine_env(self):
        vm_name = 'default'

        output = strip_margin("""|export DOCKER_TLS_VERIFY="1"
                                 |export DOCKER_HOST="tcp://192.168.99.100:2376"
                                 |export DOCKER_CERT_PATH="/Users/mj/.docker/machine/machines/default"
                                 |export DOCKER_MACHINE_NAME="default"
                                 |# Run this command to configure your shell:
                                 |# eval "$(docker-machine env default)
                                 |""")
        check_output_mock = MagicMock(return_value=output)

        with patch('subprocess.check_output', check_output_mock):
            result = terminal.docker_machine_env(vm_name)

        expected_result = ['export DOCKER_TLS_VERIFY="1"',
                           'export DOCKER_HOST="tcp://192.168.99.100:2376"',
                           'export DOCKER_CERT_PATH="/Users/mj/.docker/machine/machines/default"',
                           'export DOCKER_MACHINE_NAME="default"',
                           '# Run this command to configure your shell:',
                           '# eval "$(docker-machine env default)']

        self.assertEqual(result, expected_result)
        check_output_mock.assert_called_with(['docker-machine', 'env', vm_name], universal_newlines=True)

    def test_docker_machine_ip(self):
        vm_name = 'default'
        ip = '192.168.99.100'
        check_output_mock = MagicMock(return_value='{}\n'.format(ip))

        with patch('subprocess.check_output', check_output_mock):
            result = terminal.docker_machine_ip(vm_name)

        self.assertEqual(result, ip)
        check_output_mock.assert_called_with(['docker-machine', 'ip', vm_name], universal_newlines=True)

    def test_docker_machine_status(self):
        vm_name = 'default'
        status = 'Running'

        check_output_mock = MagicMock(return_value='{}\n'.format(status))

        with patch('subprocess.check_output', check_output_mock):
            result = terminal.docker_machine_ip(vm_name)

        self.assertEqual(result, status)
        check_output_mock.assert_called_with(['docker-machine', 'ip', vm_name], universal_newlines=True)

    def test_docker_machine_create_vm(self):
        vm_name = 'default'
        mock_output = 'test output'
        check_output_mock = MagicMock(return_value=mock_output)

        with patch('subprocess.check_output', check_output_mock):
            result = terminal.docker_machine_create_vm(vm_name)

        self.assertEqual(result, mock_output)
        check_output_mock.assert_called_with(['docker-machine', 'create', vm_name, '-d', 'virtualbox'], universal_newlines=True)

    def test_docker_machine_start_vm(self):
        vm_name = 'default'
        mock_output = 'test output'
        check_output_mock = MagicMock(return_value=mock_output)

        with patch('subprocess.check_output', check_output_mock):
            result = terminal.docker_machine_start_vm(vm_name)

        self.assertEqual(result, mock_output)
        check_output_mock.assert_called_with(['docker-machine', 'start', vm_name], universal_newlines=True)

    def test_docker_machine_stop_vm(self):
        vm_name = 'default'
        mock_output = 'test output'
        check_output_mock = MagicMock(return_value=mock_output)

        with patch('subprocess.check_output', check_output_mock):
            result = terminal.docker_machine_stop_vm(vm_name)

        self.assertEqual(result, mock_output)
        check_output_mock.assert_called_with(['docker-machine', 'stop', vm_name], universal_newlines=True)

    def test_docker_machine_help(self):
        mock_output = 'test output'
        check_output_mock = MagicMock(return_value=mock_output)

        with patch('subprocess.check_output', check_output_mock):
            result = terminal.docker_machine_help()

        self.assertEqual(result, mock_output)
        check_output_mock.assert_called_with(['docker-machine', 'help'], universal_newlines=True)

    def test_boot2docker_shellinit(self):
        output = strip_margin("""|Writing /Users/mj/.boot2docker/certs/boot2docker-vm/ca.pem
                                 |Writing /Users/mj/.boot2docker/certs/boot2docker-vm/cert.pem
                                 |Writing /Users/mj/.boot2docker/certs/boot2docker-vm/key.pem
                                 |    export DOCKER_HOST=tcp://192.168.59.103:2376
                                 |    export DOCKER_CERT_PATH=/Users/mj/.boot2docker/certs/boot2docker-vm
                                 |    export DOCKER_TLS_VERIFY=1
                                 |""")
        check_output_mock = MagicMock(return_value=output)

        with patch('subprocess.check_output', check_output_mock):
            result = terminal.boot2docker_shellinit()

        expected_result = ['Writing /Users/mj/.boot2docker/certs/boot2docker-vm/ca.pem',
                           'Writing /Users/mj/.boot2docker/certs/boot2docker-vm/cert.pem',
                           'Writing /Users/mj/.boot2docker/certs/boot2docker-vm/key.pem',
                           'export DOCKER_HOST=tcp://192.168.59.103:2376',
                           'export DOCKER_CERT_PATH=/Users/mj/.boot2docker/certs/boot2docker-vm',
                           'export DOCKER_TLS_VERIFY=1']

        self.assertEqual(result, expected_result)
        check_output_mock.assert_called_with(['boot2docker', 'shellinit'], universal_newlines=True)

    def test_boot2docker_ip(self):
        ip = '192.168.99.100'
        check_output_mock = MagicMock(return_value='{}\n'.format(ip))

        with patch('subprocess.check_output', check_output_mock):
            result = terminal.boot2docker_ip()

        self.assertEqual(result, ip)
        check_output_mock.assert_called_with(['boot2docker', 'ip'], universal_newlines=True)

    def test_vbox_manage_increase_ram(self):
        vm_name = 'default'
        ram_size = '2048'
        mock_output = 'test output'
        check_output_mock = MagicMock(return_value='{}\n'.format(mock_output))

        with patch('subprocess.check_output', check_output_mock):
            result = terminal.vbox_manage_increase_ram(vm_name, ram_size)

        self.assertEqual(result, mock_output)
        check_output_mock.assert_called_with(['VBoxManage', 'modifyvm', vm_name, '--memory', ram_size], universal_newlines=True)

    def test_vbox_manage_get_ram_size(self):
        vm_name = 'default'
        mock_output = 'Memory size: 2048MB'
        check_output_mock = MagicMock(return_value='{}\n'.format(mock_output))

        with patch('subprocess.check_output', check_output_mock):
            result = terminal.vbox_manage_get_ram_size(vm_name)

        self.assertEqual(result, 2048)
        check_output_mock.assert_called_with(['VBoxManage', 'showvminfo', vm_name], universal_newlines=True)

    def test_vbox_manage_increase_cpu(self):
        vm_name = 'default'
        cpu_count = '4'
        mock_output = 'test output'
        check_output_mock = MagicMock(return_value='{}\n'.format(mock_output))

        with patch('subprocess.check_output', check_output_mock):
            result = terminal.vbox_manage_increase_cpu(vm_name, cpu_count)

        self.assertEqual(result, mock_output)
        check_output_mock.assert_called_with(['VBoxManage', 'modifyvm', vm_name, '--cpus', cpu_count], universal_newlines=True)

    def test_vbox_manage_get_cpu_count(self):
        vm_name = 'default'
        mock_output = 'Number of CPUs: 2'
        check_output_mock = MagicMock(return_value='{}\n'.format(mock_output))

        with patch('subprocess.check_output', check_output_mock):
            result = terminal.vbox_manage_get_cpu_count(vm_name)

        self.assertEqual(result, 2)
        check_output_mock.assert_called_with(['VBoxManage', 'showvminfo', vm_name], universal_newlines=True)

    def test_hostname(self):
        hostname = 'my-hostname'
        check_output_mock = MagicMock(return_value='{}\n'.format(hostname))

        with patch('subprocess.check_output', check_output_mock):
            result = terminal.hostname()

        self.assertEqual(result, hostname)
        check_output_mock.assert_called_with(['hostname'], universal_newlines=True)
