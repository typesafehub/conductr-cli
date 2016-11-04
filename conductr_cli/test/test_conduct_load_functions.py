from unittest import TestCase
from conductr_cli import conduct_load
from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor

import io

try:
    from unittest.mock import call, patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import call, patch, MagicMock


class TestCommonFunctions(TestCase):
    def test_conduct_load_progress_monitor(self):
        log = MagicMock()
        log.progress = MagicMock()

        monitor = MagicMock()
        monitor.len = 100
        monitor.encoder = MagicMock()

        progress_bar = MagicMock(side_effect=['progress bar', 'progress bar completed'])

        with patch('conductr_cli.screen_utils.progress_bar', progress_bar):
            progress_monitor = conduct_load.conduct_load_progress_monitor(log)
            # First call
            monitor.bytes_read = 1
            monitor.encoder.finished = False
            progress_monitor(monitor)

            # Final call
            monitor.bytes_read = 100
            monitor.encoder.finished = True
            progress_monitor(monitor)

            # Subsequent call should not trigger any logger
            progress_monitor(monitor)

        self.assertEqual(
            progress_bar.call_args_list,
            [
                call(1, 100),
                call(100, 100)
            ]
        )

        self.assertEqual(
            log.progress.call_args_list,
            [
                call('progress bar', flush=False),
                call('progress bar completed', flush=True)
            ]
        )

    def test_create_multipart(self):
        def test_callback(monitor):
            pass

        log = MagicMock()
        conduct_load_progress_monitor = MagicMock(return_value=test_callback)
        files = [('param', 'value'), ('testFile', ('text.txt', io.StringIO('text file')))]

        with patch('conductr_cli.conduct_load.conduct_load_progress_monitor', conduct_load_progress_monitor):
            result = conduct_load.create_multipart(log, files)
            self.assertIsInstance(result, MultipartEncoderMonitor)
            self.assertEqual(result.callback, test_callback)
            self.assertIsInstance(result.encoder, MultipartEncoder)
            self.assertEqual(files, result.encoder.fields)

        conduct_load_progress_monitor.assert_called_with(log)

    def test_string_io(self):
        result = conduct_load.string_io('input')
        self.assertIsInstance(result, io.StringIO)
        self.assertEqual(['input'], result.readlines())
