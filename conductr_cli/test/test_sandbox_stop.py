from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import sandbox_stop


try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestSandboxStopCommand(CliTestCase):

    default_args = {
        'local_connection': True
    }

    def expected_output(self):
        return strip_margin("""Stopping ConductR..""")

    def test_success(self):
        stdout = MagicMock()
        containers = ['cond-0', 'cond-1']

        with patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=containers), \
                patch('conductr_cli.terminal.docker_rm') as mock_docker_rm, \
                patch('sys.stdout', stdout):
            sandbox_stop.stop(MagicMock(**self.default_args))

        self.assertEqual('Stopping ConductR..\n', self.output(stdout))
        mock_docker_rm.assert_called_once_with(containers)
