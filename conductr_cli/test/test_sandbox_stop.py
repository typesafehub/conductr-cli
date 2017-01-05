from conductr_cli.test.cli_test_case import CliTestCase
from conductr_cli import sandbox_stop
from unittest.mock import patch, MagicMock


class TestSandboxStopCommand(CliTestCase):

    default_args = {
        'local_connection': True,
        'verbose': False,
        'quiet': False
    }

    def test_success(self):
        mock_sandbox_stop_docker = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('conductr_cli.sandbox_stop_docker.stop', mock_sandbox_stop_docker):
            self.assertTrue(sandbox_stop.stop(input_args))

        mock_sandbox_stop_docker.assert_called_once_with(input_args)
