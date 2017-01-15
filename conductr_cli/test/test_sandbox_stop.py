from conductr_cli.test.cli_test_case import CliTestCase
from conductr_cli import sandbox_stop
from unittest.mock import patch, MagicMock
from subprocess import CalledProcessError


class TestSandboxStopCommand(CliTestCase):

    default_args = {
        'local_connection': True,
        'verbose': False,
        'quiet': False
    }

    def test_success(self):
        mock_sandbox_stop_proxy = MagicMock(return_value=True)
        mock_sandbox_stop_docker = MagicMock(return_value=True)
        mock_sandbox_stop_jvm = MagicMock(return_value=True)

        input_args = MagicMock(**self.default_args)
        with patch('conductr_cli.sandbox_stop_docker.stop', mock_sandbox_stop_docker), \
                patch('conductr_cli.sandbox_stop_jvm.stop', mock_sandbox_stop_jvm), \
                patch('conductr_cli.sandbox_proxy.stop_proxy', mock_sandbox_stop_proxy):
            self.assertTrue(sandbox_stop.stop(input_args))

        mock_sandbox_stop_proxy.assert_called_once_with()
        mock_sandbox_stop_docker.assert_called_once_with(input_args)
        mock_sandbox_stop_jvm.assert_called_once_with(input_args)

    def test_stop_proxy_called_process_error(self):
        mock_sandbox_stop_proxy = MagicMock(side_effect=CalledProcessError(1, 'test'))
        mock_sandbox_stop_docker = MagicMock(return_value=True)
        mock_sandbox_stop_jvm = MagicMock(return_value=True)

        input_args = MagicMock(**self.default_args)
        with patch('conductr_cli.sandbox_stop_docker.stop', mock_sandbox_stop_docker), \
                patch('conductr_cli.sandbox_stop_jvm.stop', mock_sandbox_stop_jvm), \
                patch('conductr_cli.sandbox_proxy.stop_proxy', mock_sandbox_stop_proxy):
            self.assertFalse(sandbox_stop.stop(input_args))

        mock_sandbox_stop_proxy.assert_called_once_with()
        mock_sandbox_stop_docker.assert_called_once_with(input_args)
        mock_sandbox_stop_jvm.assert_called_once_with(input_args)

    def test_stop_proxy_attribute_error(self):
        mock_sandbox_stop_proxy = MagicMock(side_effect=AttributeError('test'))
        mock_sandbox_stop_docker = MagicMock(return_value=True)
        mock_sandbox_stop_jvm = MagicMock(return_value=True)

        input_args = MagicMock(**self.default_args)
        with patch('conductr_cli.sandbox_stop_docker.stop', mock_sandbox_stop_docker), \
                patch('conductr_cli.sandbox_stop_jvm.stop', mock_sandbox_stop_jvm), \
                patch('conductr_cli.sandbox_proxy.stop_proxy', mock_sandbox_stop_proxy):
            self.assertFalse(sandbox_stop.stop(input_args))

        mock_sandbox_stop_proxy.assert_called_once_with()
        mock_sandbox_stop_docker.assert_called_once_with(input_args)
        mock_sandbox_stop_jvm.assert_called_once_with(input_args)
