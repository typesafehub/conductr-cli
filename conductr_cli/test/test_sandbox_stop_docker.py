from conductr_cli.test.cli_test_case import CliTestCase, strip_margin, as_error
from conductr_cli import sandbox_stop_docker, logging_setup
from unittest.mock import patch, MagicMock
from subprocess import CalledProcessError


class TestStop(CliTestCase):

    default_args = {
        'local_connection': True,
        'verbose': False,
        'quiet': False,
        'image_dir': '/Users/mj/.conductr/images'
    }

    def test_stop_containers(self):
        stdout = MagicMock()
        containers = ['cond-0', 'cond-1']

        with patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=containers), \
                patch('conductr_cli.terminal.docker_rm') as mock_docker_rm:
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            sandbox_stop_docker.stop(MagicMock(**self.default_args))

        self.assertEqual(strip_margin("""||------------------------------------------------|
                                         || Stopping ConductR                              |
                                         ||------------------------------------------------|
                                         |ConductR has been successfully stopped
                                         |"""), self.output(stdout))
        mock_docker_rm.assert_called_once_with(containers)

    def test_cannot_stop_containers(self):
        stdout = MagicMock()
        stderr = MagicMock()
        mock_docker_rm = MagicMock(side_effect=CalledProcessError(-1, 'test only'))
        containers = ['cond-0', 'cond-1']

        with patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=containers), \
                patch('conductr_cli.terminal.docker_rm', mock_docker_rm):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout, stderr)
            sandbox_stop_docker.stop(MagicMock(**self.default_args))

        self.assertEqual(strip_margin("""||------------------------------------------------|
                                         || Stopping ConductR                              |
                                         ||------------------------------------------------|
                                         |"""), self.output(stdout))
        self.assertEqual(
            as_error(strip_margin("""|Error: ConductR containers could not be stopped
                                     |Error: Please stop the Docker containers manually
                                     |""")), self.output(stderr))
        mock_docker_rm.assert_called_once_with(containers)

    def test_stop_no_containers(self):
        stdout = MagicMock()
        containers = []

        with patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=containers), \
                patch('conductr_cli.terminal.docker_rm') as mock_docker_rm:
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            sandbox_stop_docker.stop(MagicMock(**self.default_args))

        self.assertEqual('', self.output(stdout))
        mock_docker_rm.assert_not_called()
