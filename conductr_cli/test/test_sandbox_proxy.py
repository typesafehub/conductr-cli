from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import logging_setup, sandbox_proxy
from unittest.mock import call, patch, MagicMock
from subprocess import CalledProcessError
import ipaddress


class TestStartProxy(CliTestCase):

    def test_start(self):
        stdout = MagicMock()

        mock_is_docker_present = MagicMock(return_value=True)
        mock_setup_haproxy_dirs = MagicMock()
        mock_stop_proxy = MagicMock()
        mock_start_docker_instance = MagicMock()
        mock_start_conductr_haproxy = MagicMock()

        args = MagicMock(**{})

        with patch('conductr_cli.docker.is_docker_present', mock_is_docker_present), \
                patch('conductr_cli.sandbox_proxy.setup_haproxy_dirs', mock_setup_haproxy_dirs), \
                patch('conductr_cli.sandbox_proxy.stop_proxy', mock_stop_proxy), \
                patch('conductr_cli.sandbox_proxy.start_docker_instance', mock_start_docker_instance), \
                patch('conductr_cli.sandbox_proxy.start_conductr_haproxy', mock_start_conductr_haproxy):
            logging_setup.configure_logging(args, stdout)
            sandbox_proxy.start_proxy(ipaddress.ip_address('192.168.1.1'), 9000, [3003], [9999, 9200])

        mock_is_docker_present.assert_called_once_with()
        mock_setup_haproxy_dirs.assert_called_once_with()
        mock_stop_proxy.assert_called_once_with()
        mock_start_docker_instance.assert_called_once_with(ipaddress.ip_address('192.168.1.1'), 9000, [3003], [9999, 9200])
        mock_start_conductr_haproxy.assert_called_once_with()

        self.assertEqual('', self.output(stdout))

    def test_docker_not_present(self):
        stdout = MagicMock()

        mock_is_docker_present = MagicMock(return_value=False)
        mock_setup_haproxy_dirs = MagicMock()
        mock_stop_proxy = MagicMock()
        mock_start_docker_instance = MagicMock()
        mock_start_conductr_haproxy = MagicMock()

        args = MagicMock(**{})

        with patch('conductr_cli.docker.is_docker_present', mock_is_docker_present), \
                patch('conductr_cli.sandbox_proxy.setup_haproxy_dirs', mock_setup_haproxy_dirs), \
                patch('conductr_cli.sandbox_proxy.stop_proxy', mock_stop_proxy), \
                patch('conductr_cli.sandbox_proxy.start_docker_instance', mock_start_docker_instance), \
                patch('conductr_cli.sandbox_proxy.start_conductr_haproxy', mock_start_conductr_haproxy):
            logging_setup.configure_logging(args, stdout)
            sandbox_proxy.start_proxy(ipaddress.ip_address('192.168.1.1'), 9000, [3003], [9999, 9200])

        mock_is_docker_present.assert_called_once_with()
        mock_setup_haproxy_dirs.assert_not_called()
        mock_stop_proxy.assert_not_called()
        mock_start_docker_instance.assert_not_called()
        mock_start_conductr_haproxy.assert_not_called()

        self.assertEqual('', self.output(stdout))


class TestStopProxy(CliTestCase):
    def test_stop(self):
        stdout = MagicMock()

        mock_is_docker_present = MagicMock(return_value=True)
        mock_get_running_haproxy = MagicMock(return_value='sandbox-haproxy')
        mock_docker_rm = MagicMock()

        args = MagicMock(**{})

        with patch('conductr_cli.docker.is_docker_present', mock_is_docker_present), \
                patch('conductr_cli.sandbox_proxy.get_running_haproxy', mock_get_running_haproxy), \
                patch('conductr_cli.terminal.docker_rm', mock_docker_rm):
            logging_setup.configure_logging(args, stdout)
            self.assertTrue(sandbox_proxy.stop_proxy())

        mock_get_running_haproxy.assert_called_once_with()
        mock_docker_rm.assert_called_once_with(['sandbox-haproxy'])

        expected_output = strip_margin("""||------------------------------------------------|
                                          || Stopping HAProxy                               |
                                          ||------------------------------------------------|
                                          |HAProxy has been successfully stopped
                                          |""")
        self.assertEqual(expected_output, self.output(stdout))

    def test_already_stopped(self):
        stdout = MagicMock()

        mock_is_docker_present = MagicMock(return_value=True)
        mock_get_running_haproxy = MagicMock(return_value=None)
        mock_docker_rm = MagicMock()

        args = MagicMock(**{})

        with patch('conductr_cli.docker.is_docker_present', mock_is_docker_present), \
                patch('conductr_cli.sandbox_proxy.get_running_haproxy', mock_get_running_haproxy), \
                patch('conductr_cli.terminal.docker_rm', mock_docker_rm):
            logging_setup.configure_logging(args, stdout)
            self.assertTrue(sandbox_proxy.stop_proxy())

        mock_get_running_haproxy.assert_called_once_with()
        mock_docker_rm.assert_not_called()

        self.assertEqual('', self.output(stdout))

    def test_called_process_error(self):
        stdout = MagicMock()

        mock_is_docker_present = MagicMock(return_value=True)
        mock_get_running_haproxy = MagicMock(side_effect=CalledProcessError(1, 'test'))
        mock_docker_rm = MagicMock()

        args = MagicMock(**{})

        with patch('conductr_cli.docker.is_docker_present', mock_is_docker_present), \
                patch('conductr_cli.sandbox_proxy.get_running_haproxy', mock_get_running_haproxy), \
                patch('conductr_cli.terminal.docker_rm', mock_docker_rm):
            logging_setup.configure_logging(args, stdout)
            self.assertFalse(sandbox_proxy.stop_proxy())

        mock_get_running_haproxy.assert_called_once_with()
        mock_docker_rm.assert_not_called()

        self.assertEqual('', self.output(stdout))

    def test_attribute_error(self):
        stdout = MagicMock()

        mock_is_docker_present = MagicMock(return_value=True)
        mock_get_running_haproxy = MagicMock(side_effect=AttributeError('test'))
        mock_docker_rm = MagicMock()

        args = MagicMock(**{})

        with patch('conductr_cli.docker.is_docker_present', mock_is_docker_present), \
                patch('conductr_cli.sandbox_proxy.get_running_haproxy', mock_get_running_haproxy), \
                patch('conductr_cli.terminal.docker_rm', mock_docker_rm):
            logging_setup.configure_logging(args, stdout)
            self.assertFalse(sandbox_proxy.stop_proxy())

        mock_get_running_haproxy.assert_called_once_with()
        mock_docker_rm.assert_not_called()

        self.assertEqual('', self.output(stdout))

    def test_docker_not_present(self):
        stdout = MagicMock()

        mock_is_docker_present = MagicMock(return_value=False)
        mock_get_running_haproxy = MagicMock()
        mock_docker_rm = MagicMock()

        args = MagicMock(**{})

        with patch('conductr_cli.docker.is_docker_present', mock_is_docker_present), \
                patch('conductr_cli.sandbox_proxy.get_running_haproxy', mock_get_running_haproxy), \
                patch('conductr_cli.terminal.docker_rm', mock_docker_rm):
            logging_setup.configure_logging(args, stdout)
            self.assertTrue(sandbox_proxy.stop_proxy())

        mock_get_running_haproxy.assert_not_called()
        mock_docker_rm.assert_not_called()

        self.assertEqual('', self.output(stdout))


class TestSetupHAProxyDirs(CliTestCase):
    def test_create_config(self):
        mock_makedirs = MagicMock()

        mock_exists = MagicMock(return_value=False)
        mock_open = MagicMock()

        with patch('os.makedirs', mock_makedirs), \
                patch('os.path.exists', mock_exists), \
                patch('builtins.open', mock_open):
            sandbox_proxy.setup_haproxy_dirs()

        mock_makedirs.assert_called_once_with(sandbox_proxy.HAPROXY_CFG_DIR, mode=0o700, exist_ok=True)
        mock_exists.assert_called_once_with(sandbox_proxy.HAPROXY_CFG_PATH)
        mock_open.assert_called_once_with(sandbox_proxy.HAPROXY_CFG_PATH, 'w')
        mock_open.return_value.__enter__.return_value.write.assert_called_once_with(sandbox_proxy.DEFAULT_HAPROXY_CFG_ENTRIES)

    def test_not_create_config(self):
        mock_makedirs = MagicMock()

        mock_exists = MagicMock(return_value=True)
        mock_open = MagicMock()

        with patch('os.makedirs', mock_makedirs), \
                patch('os.path.exists', mock_exists), \
                patch('builtins.open', mock_open):
            sandbox_proxy.setup_haproxy_dirs()

        mock_makedirs.assert_called_once_with(sandbox_proxy.HAPROXY_CFG_DIR, mode=0o700, exist_ok=True)
        mock_exists.assert_called_once_with(sandbox_proxy.HAPROXY_CFG_PATH)
        mock_open.assert_not_called()


class TestGetRunningHAProxy(CliTestCase):
    def test_create_dir(self):
        mock_docker_ps_result = 'test'
        mock_docker_ps = MagicMock(return_value=mock_docker_ps_result)

        with patch('conductr_cli.terminal.docker_ps', mock_docker_ps):
            self.assertEqual(mock_docker_ps_result, sandbox_proxy.get_running_haproxy())

        mock_docker_ps.assert_called_once_with(ps_filter='name=sandbox-haproxy')


class TestStartDockerInstance(CliTestCase):
    def test_start(self):
        stdout = MagicMock()

        mock_docker_images = MagicMock(return_value='sandbox-haproxy-container-id')
        mock_docker_pull = MagicMock()
        mock_docker_run = MagicMock()

        args = MagicMock(**{})

        with patch('conductr_cli.terminal.docker_images', mock_docker_images), \
                patch('conductr_cli.terminal.docker_pull', mock_docker_pull), \
                patch('conductr_cli.terminal.docker_run', mock_docker_run):
            logging_setup.configure_logging(args, stdout)
            sandbox_proxy.start_docker_instance(ipaddress.ip_address('192.168.1.1'), 9000, [3003], [19001])

        mock_docker_images.assert_called_once_with('haproxy:1.5')
        mock_docker_pull.assert_not_called()
        mock_docker_run.assert_called_once_with(
            ['-d',
             '--name', 'sandbox-haproxy',
             '-p', '192.168.1.1:80:80',
             '-p', '192.168.1.1:443:443',
             '-p', '192.168.1.1:3003:3003',
             '-p', '192.168.1.1:8999:8999',
             '-p', '192.168.1.1:9000:9000',
             '-p', '192.168.1.1:19001:19001',
             '-v', '{}:/usr/local/etc/haproxy:ro'.format(sandbox_proxy.HAPROXY_CFG_DIR)],
            'haproxy:1.5',
            positional_args=[]
        )

        expected_output = strip_margin("""||------------------------------------------------|
                                          || Starting HAProxy                               |
                                          ||------------------------------------------------|
                                          |Exposing the following ports [80, 443, 3003, 8999, 9000, 19001]
                                          |""")
        self.assertEqual(expected_output, self.output(stdout))

    def test_start_duplicate_ports(self):
        stdout = MagicMock()

        mock_docker_images = MagicMock(return_value='sandbox-haproxy-container-id')
        mock_docker_pull = MagicMock()
        mock_docker_run = MagicMock()

        args = MagicMock(**{})

        with patch('conductr_cli.terminal.docker_images', mock_docker_images), \
                patch('conductr_cli.terminal.docker_pull', mock_docker_pull), \
                patch('conductr_cli.terminal.docker_run', mock_docker_run):
            logging_setup.configure_logging(args, stdout)
            sandbox_proxy.start_docker_instance(ipaddress.ip_address('192.168.1.1'), 9000, [3003, 3000], [19001, 3000])

        mock_docker_images.assert_called_once_with('haproxy:1.5')
        mock_docker_pull.assert_not_called()
        mock_docker_run.assert_called_once_with(
            ['-d',
             '--name', 'sandbox-haproxy',
             '-p', '192.168.1.1:80:80',
             '-p', '192.168.1.1:443:443',
             '-p', '192.168.1.1:3000:3000',
             '-p', '192.168.1.1:3003:3003',
             '-p', '192.168.1.1:8999:8999',
             '-p', '192.168.1.1:9000:9000',
             '-p', '192.168.1.1:19001:19001',
             '-v', '{}:/usr/local/etc/haproxy:ro'.format(sandbox_proxy.HAPROXY_CFG_DIR)],
            'haproxy:1.5',
            positional_args=[]
        )

        expected_output = strip_margin("""||------------------------------------------------|
                                          || Starting HAProxy                               |
                                          ||------------------------------------------------|
                                          |Exposing the following ports [80, 443, 3000, 3003, 8999, 9000, 19001]
                                          |""")
        self.assertEqual(expected_output, self.output(stdout))

    def test_start_with_pull(self):
        stdout = MagicMock()

        mock_docker_images = MagicMock(return_value=None)
        mock_docker_pull = MagicMock()
        mock_docker_run = MagicMock()

        args = MagicMock(**{})

        with patch('conductr_cli.terminal.docker_images', mock_docker_images), \
                patch('conductr_cli.terminal.docker_pull', mock_docker_pull), \
                patch('conductr_cli.terminal.docker_run', mock_docker_run):
            logging_setup.configure_logging(args, stdout)
            sandbox_proxy.start_docker_instance(ipaddress.ip_address('192.168.1.1'), 9000, [3003], [19001])

        mock_docker_images.assert_called_once_with('haproxy:1.5')
        mock_docker_pull.assert_called_once_with('haproxy:1.5')
        mock_docker_run.assert_called_once_with(
            ['-d',
             '--name', 'sandbox-haproxy',
             '-p', '192.168.1.1:80:80',
             '-p', '192.168.1.1:443:443',
             '-p', '192.168.1.1:3003:3003',
             '-p', '192.168.1.1:8999:8999',
             '-p', '192.168.1.1:9000:9000',
             '-p', '192.168.1.1:19001:19001',
             '-v', '{}:/usr/local/etc/haproxy:ro'.format(sandbox_proxy.HAPROXY_CFG_DIR)],
            'haproxy:1.5',
            positional_args=[]
        )

        expected_output = strip_margin("""||------------------------------------------------|
                                          || Starting HAProxy                               |
                                          ||------------------------------------------------|
                                          |Pulling docker image haproxy:1.5
                                          |Exposing the following ports [80, 443, 3003, 8999, 9000, 19001]
                                          |""")
        self.assertEqual(expected_output, self.output(stdout))


class TestStartConductrHAProxy(CliTestCase):
    def test_success(self):
        stdout = MagicMock()
        mock_run = MagicMock()
        args = MagicMock(**{})

        with patch('conductr_cli.conduct_main.run', mock_run):
            logging_setup.configure_logging(args, stdout)
            sandbox_proxy.start_conductr_haproxy()

        self.assertEqual([
            call(['load', 'conductr-haproxy', 'conductr-haproxy-dev-mode', '--disable-instructions'], configure_logging=False),
            call(['run', 'conductr-haproxy', '--disable-instructions'], configure_logging=False)
        ], mock_run.call_args_list)
