from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import terminal


try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestTerminal(CliTestCase):

    def test_docker_images(self):
        image = 'my-image-id'

        with patch('subprocess.check_output', return_value='{}\n'.format(image)):
            result = terminal.docker_images(image)

        self.assertEqual(result, image)

    def test_docker_pull(self):
        image = 'image:version'
        stdout = MagicMock()

        with patch('subprocess.call', patch('sys.stdout', stdout)):
            terminal.docker_pull(image)

        self.assertEqual('', self.output(stdout))

    def test_docker_ps(self):
        ps_filter = 'name=cond-'
        image1 = 'image-id1'
        image2 = 'image-id2'

        with patch('subprocess.check_output', return_value='{}\n{}\n'.format(image1, image2)):
            result = terminal.docker_ps(ps_filter)

        self.assertEqual(result, [image1, image2])

    def test_docker_inspect(self):
        container_id = 'cond-0'
        inspect_format = '{{.NetworkSettings.IPAddress}}'
        ip = '172.17.0.20'

        with patch('subprocess.check_output', return_value='{}\n'.format(ip)):
            result = terminal.docker_inspect(container_id, inspect_format)

        self.assertEqual(result, ip)

    def test_docker_run(self):
        optional_args = ['-p', '9001:9001', '-e', 'AKKA_LOGLEVEL=info']
        image = 'image:version'
        positional_args = ['--discover-host-ip']
        stdout = MagicMock()

        with patch('subprocess.call', patch('sys.stdout', stdout)):
            terminal.docker_run(optional_args, image, positional_args)

        self.assertEqual('', self.output(stdout))

    def test_docker_rm(self):
        containers = ['cond-0', 'cond-1']
        stdout = MagicMock()

        with patch('subprocess.call', patch('sys.stdout', stdout)):
            terminal.docker_rm(containers)

        self.assertEqual('', self.output(stdout))

    def test_docker_machine_env(self):
        vm_name = 'default'

        output = strip_margin("""|export DOCKER_TLS_VERIFY="1"
                                 |export DOCKER_HOST="tcp://192.168.99.100:2376"
                                 |export DOCKER_CERT_PATH="/Users/mj/.docker/machine/machines/default"
                                 |export DOCKER_MACHINE_NAME="default"
                                 |# Run this command to configure your shell:
                                 |# eval "$(docker-machine env default)
                                 |""")

        with patch('subprocess.check_output', return_value=output):
            result = terminal.docker_machine_env(vm_name)

        expected_result = ['export DOCKER_TLS_VERIFY="1"',
                           'export DOCKER_HOST="tcp://192.168.99.100:2376"',
                           'export DOCKER_CERT_PATH="/Users/mj/.docker/machine/machines/default"',
                           'export DOCKER_MACHINE_NAME="default"',
                           '# Run this command to configure your shell:',
                           '# eval "$(docker-machine env default)']

        self.assertEqual(result, expected_result)

    def test_docker_machine_ip(self):
        vm_name = 'default'
        ip = '192.168.99.100'

        with patch('subprocess.check_output', return_value='{}\n'.format(ip)):
            result = terminal.docker_machine_ip(vm_name)

        self.assertEqual(result, ip)

    def test_boot2docker_shellinit(self):
        output = strip_margin("""|Writing /Users/mj/.boot2docker/certs/boot2docker-vm/ca.pem
                                 |Writing /Users/mj/.boot2docker/certs/boot2docker-vm/cert.pem
                                 |Writing /Users/mj/.boot2docker/certs/boot2docker-vm/key.pem
                                 |    export DOCKER_HOST=tcp://192.168.59.103:2376
                                 |    export DOCKER_CERT_PATH=/Users/mj/.boot2docker/certs/boot2docker-vm
                                 |    export DOCKER_TLS_VERIFY=1
                                 |""")

        with patch('subprocess.check_output', return_value=output):
            result = terminal.boot2docker_shellinit()

        expected_result = ['Writing /Users/mj/.boot2docker/certs/boot2docker-vm/ca.pem',
                           'Writing /Users/mj/.boot2docker/certs/boot2docker-vm/cert.pem',
                           'Writing /Users/mj/.boot2docker/certs/boot2docker-vm/key.pem',
                           'export DOCKER_HOST=tcp://192.168.59.103:2376',
                           'export DOCKER_CERT_PATH=/Users/mj/.boot2docker/certs/boot2docker-vm',
                           'export DOCKER_TLS_VERIFY=1']

        self.assertEqual(result, expected_result)

    def test_boot2docker_ip(self):
        ip = '192.168.99.100'

        with patch('subprocess.check_output', return_value='{}\n'.format(ip)):
            result = terminal.boot2docker_ip()

        self.assertEqual(result, ip)

    def test_hostname(self):
        hostname = 'my-hostname'

        with patch('subprocess.check_output', return_value='{}\n'.format(hostname)):
            result = terminal.hostname()

        self.assertEqual(result, hostname)
