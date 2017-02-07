from conductr_cli.test.cli_test_case import CliTestCase, as_error, strip_margin
from conductr_cli import logging_setup, sandbox_restart
from unittest.mock import patch, MagicMock, call, mock_open


class TestSandboxRestartCommand(CliTestCase):

    def test_success_without_whitespace(self):
        args = MagicMock()
        mock_sandbox_main = MagicMock()

        with patch('builtins.open', mock_open(read_data='2.0.0 --feature visualization -n 2:3')), \
                patch('conductr_cli.sandbox_main.run', mock_sandbox_main):
            self.assertTrue(sandbox_restart.restart(args))

        mock_sandbox_main.assert_has_calls([
            call(['stop'], configure_logging=False),
            call(['run', '2.0.0', '--feature', 'visualization', '-n', '2:3'], configure_logging=False)
        ])

    def test_success_with_whitespace(self):
        args = MagicMock()
        mock_sandbox_main = MagicMock()

        with patch('builtins.open', mock_open(read_data='2.0.0 --feature "this feature" -n 2:3')), \
                patch('conductr_cli.sandbox_main.run', mock_sandbox_main):
            self.assertTrue(sandbox_restart.restart(args))

        mock_sandbox_main.assert_has_calls([
            call(['stop'], configure_logging=False),
            call(['run', '2.0.0', '--feature', '"this', 'feature"', '-n', '2:3'], configure_logging=False)
        ])

    def test_file_not_found_error(self):
        args = MagicMock()
        stderr = MagicMock()
        _mock_open = MagicMock(side_effect=FileNotFoundError)

        with patch('builtins.open', _mock_open):
            logging_setup.configure_logging(args, err_output=stderr)
            self.assertFalse(sandbox_restart.restart(args))
            self.assertEqual(as_error(strip_margin("""|Error: ConductR cannot be restarted.
                                                      |Error: Please start ConductR first with: sandbox run
                                                      |""")),
                             self.output(stderr))
