import subprocess
from conductr_cli.test.cli_test_case import CliTestCase
from conductr_cli import terminal
from unittest.mock import patch, MagicMock


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
