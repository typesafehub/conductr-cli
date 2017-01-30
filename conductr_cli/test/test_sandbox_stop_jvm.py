from conductr_cli.test.cli_test_case import CliTestCase, as_error, strip_margin
from conductr_cli import sandbox_stop_jvm, logging_setup
from conductr_cli.screen_utils import h1
from unittest.mock import patch, MagicMock, call
import signal


class TestStop(CliTestCase):

    default_args = {
        'local_connection': True,
        'verbose': False,
        'quiet': False,
        'image_dir': '/Users/mj/.conductr/images'
    }

    def test_stop_processes_with_first_attempt(self):
        ps_output_first = [
            {'id': 58002, 'type': 'core'},
            {'id': 58003, 'type': 'agent'},
            {'id': 58004, 'type': 'core'},
            {'id': 58005, 'type': 'agent'},
            {'id': 58006, 'type': 'core'},
            {'id': 58007, 'type': 'agent'}
        ]
        ps_output_second = []

        stdout = MagicMock()
        mock_os_kill = MagicMock()
        mock_time_sleep = MagicMock()
        mock_find_pids = MagicMock(side_effect=[ps_output_first, ps_output_second])

        with patch('os.kill', mock_os_kill), \
                patch('time.sleep', mock_time_sleep), \
                patch('conductr_cli.sandbox_common.find_pids', mock_find_pids):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            sandbox_stop_jvm.stop(MagicMock(**self.default_args))

        self.assertEqual(strip_margin("""||------------------------------------------------|
                                         || Stopping ConductR                              |
                                         ||------------------------------------------------|
                                         |ConductR core pid 58002 stopped
                                         |ConductR agent pid 58003 stopped
                                         |ConductR core pid 58004 stopped
                                         |ConductR agent pid 58005 stopped
                                         |ConductR core pid 58006 stopped
                                         |ConductR agent pid 58007 stopped
                                         |ConductR has been successfully stopped
                                         |"""), self.output(stdout))
        mock_os_kill.assert_has_calls([call(58002, signal.SIGTERM),
                                       call(58003, signal.SIGTERM),
                                       call(58004, signal.SIGTERM),
                                       call(58005, signal.SIGTERM),
                                       call(58006, signal.SIGTERM),
                                       call(58007, signal.SIGTERM)])

    def test_stop_processes_with_second_attempt(self):
        ps_output_first = [
            {'id': 58002, 'type': 'core'},
            {'id': 58003, 'type': 'agent'},
            {'id': 58004, 'type': 'core'},
            {'id': 58005, 'type': 'agent'},
            {'id': 58006, 'type': 'core'},
            {'id': 58007, 'type': 'agent'}
        ]
        ps_output_second = [
            {'id': 58002, 'type': 'core'},
            {'id': 58003, 'type': 'agent'}
        ]
        ps_output_third = []

        stdout = MagicMock()
        mock_os_kill = MagicMock()
        mock_time_sleep = MagicMock()
        mock_find_pids = MagicMock(side_effect=[ps_output_first, ps_output_second, ps_output_third])

        with patch('os.kill', mock_os_kill), \
                patch('time.sleep', mock_time_sleep), \
                patch('conductr_cli.sandbox_common.find_pids', mock_find_pids):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            sandbox_stop_jvm.stop(MagicMock(**self.default_args))

        self.assertEqual(strip_margin("""||------------------------------------------------|
                                         || Stopping ConductR                              |
                                         ||------------------------------------------------|
                                         |ConductR core pid 58004 stopped
                                         |ConductR agent pid 58005 stopped
                                         |ConductR core pid 58006 stopped
                                         |ConductR agent pid 58007 stopped
                                         |ConductR core pid 58002 stopped
                                         |ConductR agent pid 58003 stopped
                                         |ConductR has been successfully stopped
                                         |"""), self.output(stdout))
        mock_os_kill.assert_has_calls([call(58002, signal.SIGTERM),
                                       call(58003, signal.SIGTERM),
                                       call(58004, signal.SIGTERM),
                                       call(58005, signal.SIGTERM),
                                       call(58006, signal.SIGTERM),
                                       call(58007, signal.SIGTERM)])

    def test_hung_processes(self):
        ps_output = [
            {'id': 58002, 'type': 'core'},
            {'id': 58003, 'type': 'agent'}
        ]

        stdout = MagicMock()
        stderr = MagicMock()
        mock_os_kill = MagicMock()
        mock_time_sleep = MagicMock()
        mock_find_pids = MagicMock(return_value=ps_output)

        with patch('os.kill', mock_os_kill), \
                patch('time.sleep', mock_time_sleep), \
                patch('conductr_cli.sandbox_common.find_pids', mock_find_pids):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout, stderr)
            sandbox_stop_jvm.stop(MagicMock(**self.default_args))

        self.assertEqual(h1('Stopping ConductR') + '\n', self.output(stdout))
        self.assertEqual(strip_margin(as_error("""|Error: ConductR core pid 58002 could not be stopped
                                                  |Error: ConductR agent pid 58003 could not be stopped
                                                  |Error: Please stop the processes manually
                                                  |""")), self.output(stderr))
        mock_os_kill.assert_has_calls([call(58002, signal.SIGTERM),
                                       call(58003, signal.SIGTERM)])

    def test_no_process(self):
        ps_output = []

        stdout = MagicMock()
        mock_os_kill = MagicMock()
        mock_find_pids = MagicMock(return_value=ps_output)

        with patch('os.kill', mock_os_kill), \
                patch('conductr_cli.sandbox_common.find_pids', mock_find_pids):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            sandbox_stop_jvm.stop(MagicMock(**self.default_args))

        self.assertEqual('', self.output(stdout))
        mock_os_kill.assert_not_called()
