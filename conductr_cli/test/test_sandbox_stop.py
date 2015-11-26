from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import sandbox_stop, logging_setup


try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestSandboxStopCommand(CliTestCase):

    default_args = {
        'local_connection': True,
        'verbose': False,
        'quiet': False
    }

    def expected_output(self):
        return strip_margin("""Stopping ConductR..""")

    def test_success(self):
        stdout = MagicMock()
        containers = ['cond-0', 'cond-1']

        with patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=containers), \
                patch('conductr_cli.terminal.docker_rm') as mock_docker_rm:
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            sandbox_stop.stop(MagicMock(**self.default_args))

        self.assertEqual('Stopping ConductR..\n', self.output(stdout))
        mock_docker_rm.assert_called_once_with(containers)
