from conductr_cli.test.cli_test_case import CliTestCase
from conductr_cli import main_handler
from conductr_cli.constants import DEFAULT_ERROR_LOG_FILE
import sys


try:
    from unittest.mock import MagicMock, patch, call  # 3.3 and beyond
except ImportError:
    from mock import MagicMock, patch, call


class TestMainHandler(CliTestCase):
    def test_successful_completion(self):
        def callback():
            return "test"

        result = main_handler.run(callback)
        self.assertEqual(result, "test")

    def test_operation_cancelled(self):
        def cancelled():
            raise KeyboardInterrupt()

        main_handler.run(cancelled)

    def test_system_exit_requested(self):
        def request_system_exit():
            raise SystemExit()

        self.assertRaises(SystemExit, main_handler.run, request_system_exit)

    def test_handle_failure(self):
        def raise_unhandled_error():
            raise AssertionError("Test Only")

        main_log = MagicMock(name="main logger")

        formatter_mock = MagicMock()
        create_formatter_mock = MagicMock(return_value=formatter_mock)

        rotating_file_handler_mock = MagicMock()
        create_rotating_file_handler_mock = MagicMock(return_value=rotating_file_handler_mock)

        exception_log = MagicMock(name="exception logger")

        get_logger_mock = MagicMock(side_effect=[main_log, exception_log])
        sys_exit_mock = MagicMock()

        with patch('logging.getLogger', get_logger_mock), \
                patch('logging.Formatter', create_formatter_mock), \
                patch('logging.handlers.RotatingFileHandler', create_rotating_file_handler_mock), \
                patch('sys.exit', sys_exit_mock):
            main_handler.run(raise_unhandled_error)

        self.assertEqual(get_logger_mock.call_args_list, [
            call('conductr_cli.main'),
            call('conductr_cli.main.exception')
        ])

        self.assertEqual(main_log.error.call_args_list, [
            call('Encountered unexpected error.'),
            call('Reason: AssertionError Test Only'),
            call('Further information of the error can be found in the error log file: {}'.format(DEFAULT_ERROR_LOG_FILE))
        ])

        self.assertFalse(exception_log.propagate)
        create_formatter_mock.assert_called_with('%(asctime)s: %(message)s')
        create_rotating_file_handler_mock.assert_called_with(DEFAULT_ERROR_LOG_FILE, backupCount=1, maxBytes=3000000)
        rotating_file_handler_mock.setFormatter.assert_called_with(formatter_mock)
        self.assertEqual(exception_log.addHandler.call_args_list, [
            call(rotating_file_handler_mock)
        ])
        self.assertEqual(exception_log.error.call_args_list, [
            call("Failure running the following command: {}".format(sys.argv), exc_info=True)
        ])
        sys_exit_mock.assert_called_with(1)
