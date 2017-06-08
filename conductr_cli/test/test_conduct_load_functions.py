from unittest import TestCase
from unittest.mock import call, patch, MagicMock
from conductr_cli import conduct_load
from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor

import datetime
import io


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
                call(0.01),
                call(1.0)
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

    def test_cleanup_old_bundles(self):
        cache_dir = '/home/user/.conductr/cache'
        recently_loaded_bundle = '{}/reactive-maps-frontend-v1-recent.zip'.format(cache_dir)
        files_in_cache = [
            '{}/reactive-maps-frontend-v1-oldest.zip'.format(cache_dir),
            '{}/reactive-maps-frontend-v1-older.zip'.format(cache_dir),
            '{}/reactive-maps-frontend-v1-old.zip'.format(cache_dir),
            recently_loaded_bundle
        ]
        glob_mock = MagicMock(return_value=files_in_cache)
        is_same_path_mock = MagicMock(side_effect=[False, False, False, True])
        isfile_mock = MagicMock(return_value=True)

        today = datetime.date.today()
        yesterday = today - datetime.timedelta(1)
        last_week = today - datetime.timedelta(7)
        last_month = today - datetime.timedelta(30)
        getmtime_mock = MagicMock(side_effect=[last_month, last_week, yesterday])

        remove_mock = MagicMock()

        with patch('glob.glob', glob_mock), \
                patch('os.path.isfile', isfile_mock), \
                patch('os.path.getmtime', getmtime_mock), \
                patch('os.remove', remove_mock), \
                patch('conductr_cli.conduct_load.is_same_path', is_same_path_mock):
            conduct_load.cleanup_old_bundles(cache_dir, 'reactive-maps-frontend-v1-recent.zip',
                                             excluded=recently_loaded_bundle)

        glob_mock.assert_called_with('{}/*.zip'.format(cache_dir))
        self.assertEqual(isfile_mock.call_args_list, [
            call('{}/reactive-maps-frontend-v1-oldest.zip'.format(cache_dir)),
            call('{}/reactive-maps-frontend-v1-older.zip'.format(cache_dir)),
            call('{}/reactive-maps-frontend-v1-old.zip'.format(cache_dir)),
            call(recently_loaded_bundle)
        ])
        self.assertEqual(is_same_path_mock.call_args_list, [
            call('{}/reactive-maps-frontend-v1-oldest.zip'.format(cache_dir), recently_loaded_bundle),
            call('{}/reactive-maps-frontend-v1-older.zip'.format(cache_dir), recently_loaded_bundle),
            call('{}/reactive-maps-frontend-v1-old.zip'.format(cache_dir), recently_loaded_bundle),
            call(recently_loaded_bundle, recently_loaded_bundle)
        ])
        self.assertEqual(getmtime_mock.call_args_list, [
            call('{}/reactive-maps-frontend-v1-oldest.zip'.format(cache_dir)),
            call('{}/reactive-maps-frontend-v1-older.zip'.format(cache_dir)),
            call('{}/reactive-maps-frontend-v1-old.zip'.format(cache_dir))
        ])
        self.assertEqual(remove_mock.call_args_list, [
            call('{}/reactive-maps-frontend-v1-oldest.zip'.format(cache_dir)),
            call('{}/reactive-maps-frontend-v1-older.zip'.format(cache_dir))
        ])

    def test_is_same_path(self):
        file_a = "path-a.zip"
        file_b = "path-b.zip"
        abs_path_mock = MagicMock(side_effect=[
            "same-path", "same-path",
            "different-path-a", "different-path-b"
        ])

        with patch('os.path.abspath', abs_path_mock):
            self.assertTrue(conduct_load.is_same_path(file_a, file_b))
            self.assertFalse(conduct_load.is_same_path(file_a, file_b))

        self.assertEqual(abs_path_mock.call_args_list, [
            call(file_a), call(file_b),
            call(file_a), call(file_b)
        ])

    def test_open_bundle_use_given_name_no_digest(self):
        extract_open_mock = MagicMock(return_value=(1, None))

        with patch('conductr_cli.bundle_utils.digest_extract_and_open', extract_open_mock):
            bundle_file_name, bundle_open_file = \
                conduct_load.open_bundle(
                    'bundle-6ae881d57578a07900c4eb37e21afa4c2095beb8e852fb6ed8d0c9f343bc7fa8.zip',
                    '/tmp/asdf',
                    '{ name = "mock-name" }'
                )

        self.assertEqual(
            bundle_file_name,
            'bundle-6ae881d57578a07900c4eb37e21afa4c2095beb8e852fb6ed8d0c9f343bc7fa8.zip'
        )

    def test_open_bundle_use_bundle_name_for_digest_format(self):
        extract_open_mock = MagicMock(return_value=(1, ('sha-256', '6ae881d57578a07900c4eb37e21afa4c'
                                                                   '2095beb8e852fb6ed8d0c9f343bc7fa8')))

        with patch('conductr_cli.bundle_utils.digest_extract_and_open', extract_open_mock):
            bundle_file_name, bundle_open_file = \
                conduct_load.open_bundle('bundle.zip', '/tmp/asdf', '{ name = "mock-name" }')

        self.assertEqual(
            bundle_file_name,
            'mock-name-6ae881d57578a07900c4eb37e21afa4c2095beb8e852fb6ed8d0c9f343bc7fa8.zip'
        )

    def test_open_bundle_error_for_digest_format_when_no_bundle_name(self):
        extract_open_mock = MagicMock(return_value=(1, ('sha-256', '6ae881d57578a07900c4eb37e21afa4c'
                                                                   '2095beb8e852fb6ed8d0c9f343bc7fa8')))

        test_failed = True

        with patch('conductr_cli.bundle_utils.digest_extract_and_open', extract_open_mock):
            try:
                conduct_load.open_bundle(None, '/tmp/asdf', '{ }')
            except conduct_load.MalformedBundleError:
                test_failed = False

        self.assertFalse(test_failed)
