import json
import os
from unittest import mock
from unittest.mock import patch, MagicMock, call

from conductr_cli import logging_setup
from conductr_cli.bundle_core_info import BundleCoreInfo
from conductr_cli.conductr_restore import unpack_backup, process_bundle, compatible_bundle, scale_bundle, restore
from conductr_cli.test.cli_test_case import file_contents, CliTestCase, as_error, strip_margin


class TestConductrRestore(CliTestCase):
    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')

    args = {
        'dcos_mode': False,
        'command': 'conduct',
        'scheme': 'http',
        'host': '127.0.0.1',
        'port': 9005,
        'base_path': '/',
        'api_version': '1',
        'disable_instructions': False,
        'verbose': False,
        'no_wait': False,
        'quiet': False,
        'cli_parameters': '',
        'backup': 'bkp.zip',
        'output_path': '/my/fav/path',
        'conductr_auth': conductr_auth,
        'server_verification_file': server_verification_file
    }

    @patch('tempfile.mkdtemp')
    @patch('shutil.unpack_archive')
    def test_unpack_backup(self, archive_mock, tmp_mock):
        backup = MagicMock()
        tmp_mock.return_value = "something"
        result = unpack_backup(backup)

        archive_mock.assert_called_once_with(backup, tmp_mock.return_value, format='zip')
        self.assertEqual(tmp_mock.return_value, result)

    @patch('conductr_cli.control_protocol.load_bundle')
    @patch('conductr_cli.conduct_load.create_multipart')
    @patch('conductr_cli.bundle_utils.conf')
    def test_process_bundle(self, mock_conf, mock_multipart, mock_load_bundle):
        mock_args = MagicMock()
        mock_conf.return_value = 'hello'
        mock_multipart.return_value = MagicMock()
        bundle_info = BundleCoreInfo('1', 'b_name', '1234', '5678')
        open_mock = mock.mock_open()

        with patch('builtins.open', open_mock):
            process_bundle(mock_args, 'yolo', bundle_info)

        calls = [call(os.path.join('yolo', 'b_name-1234.zip'), 'rb'),
                 call(os.path.join('yolo', 'b_name-5678.zip'), 'rb')]
        open_mock.assert_has_calls(calls)

        conf_calls = [call(os.path.join('yolo', 'b_name-1234.zip')),
                      call(os.path.join('yolo', 'b_name-5678.zip'))]
        mock_conf.assert_has_calls(conf_calls)
        mock_load_bundle.assert_called_once_with(mock_args, mock_multipart.return_value)

    @patch('conductr_cli.control_protocol.load_bundle')
    @patch('conductr_cli.conduct_load.create_multipart')
    @patch('conductr_cli.bundle_utils.conf')
    def test_process_bundle_with_no_configuration(self, mock_conf, mock_multipart, mock_load_bundle):
        mock_args = MagicMock()
        mock_conf.return_value = 'hello'
        mock_multipart.return_value = MagicMock()
        bundle_info = BundleCoreInfo('1', 'b_name', '1234', '')
        open_mock = mock.mock_open()

        with patch('builtins.open', open_mock):
            process_bundle(mock_args, 'yolo', bundle_info)

        open_mock.assert_called_once_with(os.path.join('yolo', 'b_name-1234.zip'), 'rb')
        mock_conf.assert_called_once_with(os.path.join('yolo', 'b_name-1234.zip'))

        mock_load_bundle.assert_called_once_with(mock_args, mock_multipart.return_value)

    def test_should_find_compatible_bundles(self):
        b1 = BundleCoreInfo('1', 'b1', 'abcd', 'efgh', 2, compatibility_version=1)
        b2 = BundleCoreInfo('2', 'b2', 'qwer', 'ty', 2, compatibility_version=1)
        b3 = BundleCoreInfo('3', 'b3', 'ghjk', 'polk', 3, compatibility_version=3)
        b4 = BundleCoreInfo('4', 'b3', 'yolo', 'why', 3, compatibility_version=4)

        matched = compatible_bundle([b1, b2, b3, b4], 'b3', 3)
        self.assertEqual('3', matched)

        no_match = compatible_bundle([b1, b2, b3, b4], 'b3', 2)
        self.assertEqual(None, no_match)

        not_matched = compatible_bundle([b1, b2, b3, b4], 'b5', 3)
        self.assertEqual(None, not_matched)

    @patch('copy.deepcopy')
    @patch('conductr_cli.bundle_scale.wait_for_scale')
    @patch('conductr_cli.control_protocol.run_bundle')
    def test_should_call_run_with_modified_args(self, mock_run_bundle,
                                                scale_mock, mock_copy):
        mock_args = MagicMock(**self.args)
        mock_run_bundle.return_value = json.loads('{"bundleId":"abcd"}')
        mock_copy.return_value = MagicMock()
        scale_bundle(mock_args, 'abcd', 3, 'efgh')

        mock_run_bundle.assert_called_once_with(mock_copy.return_value)
        scale_mock.assert_called_once_with('abcd', 3, wait_for_is_active=True, args=mock_copy.return_value)

    @patch('conductr_cli.control_protocol.get_bundles')
    @patch('conductr_cli.conductr_restore.unpack_backup')
    def test_restore_should_log_load_errors(self, mock_unpack, mock_bundle):
        mock_args = MagicMock(**self.args)
        stdout = MagicMock()
        stderr = MagicMock()

        mock_unpack.return_value = 'my/path'
        mock_bundle.return_value = json.loads(file_contents('data/bundles/bundle_json_modified.json'))

        logging_setup.configure_logging(mock_args, stdout, stderr)

        open_mock = mock.mock_open(read_data=file_contents('data/bundles/bundle_json.json'))

        with patch('builtins.open', open_mock):
            restore(mock_args)

        mock_unpack.assert_called_once_with('bkp.zip')
        mock_bundle.assert_called_once_with(mock_args)

        self.assertEqual(
            strip_margin("""|Restoring bundle : continuous-delivery.
                            |Restoring bundle : eslite.
                            |Restoring bundle : visualizer.
                            |Restoring bundle : reactive-maps-backend-region.
                            |Restoring bundle : reactive-maps-backend-summary.
                            |Restoring bundle : reactive-maps-frontend.
                            |"""),
            self.output(stdout))

        self.assertEqual(
            as_error(strip_margin("""|Error: continuous-delivery could not be loaded.
                                     |Error: eslite could not be loaded.
                                     |Error: visualizer could not be loaded.
                                     |Error: reactive-maps-backend-region could not be loaded.
                                     |Error: reactive-maps-backend-summary could not be loaded.
                                     |Error: reactive-maps-frontend could not be loaded.
                                     |""")),
            self.output(stderr))

    @patch('conductr_cli.conductr_restore.scale_bundle')
    @patch('conductr_cli.conductr_restore.compatible_bundle')
    @patch('conductr_cli.conductr_restore.process_bundle')
    @patch('conductr_cli.control_protocol.get_bundles')
    @patch('conductr_cli.conductr_restore.unpack_backup')
    def test_restore_should_scale_loaded_bundles(self, mock_unpack,
                                                 mock_bundle, mock_process_bundle,
                                                 mock_compatible, mock_scale_bundle):
        mock_args = MagicMock(**self.args)

        mock_unpack.return_value = 'my/path'
        mock_process_bundle.return_value = '1234'
        mock_compatible.return_value = 'yolo'

        bundles = file_contents('data/bundles/bundle_json.json')
        mock_bundle.return_value = json.loads(file_contents('data/bundles/bundle_json_modified.json'))
        bundles_info = sorted(BundleCoreInfo.from_bundles(json.loads(bundles)),
                              key=lambda b: b.start_time)

        open_mock = mock.mock_open(read_data=bundles)

        with patch('builtins.open', open_mock):
            restore(mock_args)

        mock_unpack.assert_called_once_with('bkp.zip')
        mock_bundle.assert_called_once_with(mock_args)

        calls = [call(mock_args, 'my/path', bundles_info[0]),
                 call(mock_args, 'my/path', bundles_info[1]),
                 call(mock_args, 'my/path', bundles_info[2]),
                 call(mock_args, 'my/path', bundles_info[3]),
                 call(mock_args, 'my/path', bundles_info[4]),
                 call(mock_args, 'my/path', bundles_info[5])]

        mock_process_bundle.assert_has_calls(calls)

        dest_bundles_info = BundleCoreInfo.from_bundles(mock_bundle.return_value)
        compat_calls = [call(dest_bundles_info, 'continuous-delivery', '3'),
                        call(dest_bundles_info, 'eslite', '1'),
                        call(dest_bundles_info, 'visualizer', '2'),
                        call(dest_bundles_info, 'reactive-maps-backend-region', '1'),
                        call(dest_bundles_info, 'reactive-maps-backend-summary', '1'),
                        call(dest_bundles_info, 'reactive-maps-frontend', '1')]

        mock_compatible.assert_has_calls(compat_calls)

        scale_calls = [call(mock_args, '1234', 1, 'yolo'),
                       call(mock_args, '1234', 1, 'yolo'),
                       call(mock_args, '1234', 1, 'yolo'),
                       call(mock_args, '1234', 1, 'yolo'),
                       call(mock_args, '1234', 0, 'yolo'),
                       call(mock_args, '1234', 1, 'yolo')]

        mock_scale_bundle.assert_has_calls(scale_calls)
