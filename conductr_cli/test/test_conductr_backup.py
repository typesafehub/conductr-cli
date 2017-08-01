import os
from unittest import mock
from unittest.mock import patch, MagicMock, ANY

from requests import HTTPError
from requests_toolbelt import MultipartEncoder

from conductr_cli.bundle_core_info import BundleCoreInfo
from conductr_cli.conductr_backup import bundles, bundle_files, validate_artifact, backup_members, \
    backup_agents, backup_bundle_json, backup_bundle_conf, backup_bundle_file, backup, process_added_bundles, \
    process_removed_bundles, backup_bundle, remove_bundle
from conductr_cli.exceptions import ConductBackupError
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT
from conductr_cli.test.cli_test_case import CliTestCase, file_contents


class TestBundleJson(CliTestCase):
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
        'bundle': '45e0c477d3e5ea92aa8d85c0d8f3e25c',
        'output_path': '/my/fav/path',
        'conductr_auth': conductr_auth,
        'server_verification_file': server_verification_file
    }

    bundle_url = 'http://127.0.0.1:9005/bundles'

    def test_backup_should_fetch_bundles_success(self):
        mock_bundle_json = self.respond_with_file_contents('data/bundles/bundle_json.json')

        input_args = MagicMock(**self.args)
        with patch('conductr_cli.conduct_request.get', mock_bundle_json):
            result = bundles(input_args)
            mock_bundle_json.assert_called_once_with(False, '127.0.0.1', self.bundle_url, auth=self.conductr_auth,
                                                     verify=self.server_verification_file,
                                                     timeout=DEFAULT_HTTP_TIMEOUT)
            expected = file_contents('data/bundles/bundle_json.json')
            self.assertEqual(expected, result)

    def test_backup_bundles_when_bundles_failure(self):
        mock_bundle = self.respond_with(status_code=404)

        input_args = MagicMock(**self.args)
        with patch('conductr_cli.conduct_request.get', mock_bundle):
            self.assertRaises(HTTPError, bundles, input_args)
            mock_bundle.assert_called_once_with(False, '127.0.0.1', self.bundle_url, auth=self.conductr_auth,
                                                verify=self.server_verification_file,
                                                timeout=DEFAULT_HTTP_TIMEOUT)

        mock_bundle = self.respond_with(status_code=500)

        input_args = MagicMock(**self.args)
        with patch('conductr_cli.conduct_request.get', mock_bundle):
            self.assertRaises(HTTPError, bundles, input_args)
            mock_bundle.assert_called_once_with(False, '127.0.0.1', self.bundle_url, auth=self.conductr_auth,
                                                verify=self.server_verification_file,
                                                timeout=DEFAULT_HTTP_TIMEOUT)

        mock_bundle = self.respond_with(status_code=301)

        input_args = MagicMock(**self.args)
        with patch('conductr_cli.conduct_request.get', mock_bundle):
            self.assertRaises(HTTPError, bundles, input_args)
            mock_bundle.assert_called_once_with(False, '127.0.0.1', self.bundle_url, auth=self.conductr_auth,
                                                verify=self.server_verification_file,
                                                timeout=DEFAULT_HTTP_TIMEOUT)


class TestBundle(CliTestCase):
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
        'bundle': '45e0c477d3e5ea92aa8d85c0d8f3e25c',
        'output_path': '/my/fav/path',
        'conductr_auth': conductr_auth,
        'server_verification_file': server_verification_file
    }

    bundle_url = 'http://127.0.0.1:9005/bundles/45e0c477d3e5ea92aa8d85c0d8f3e25c'
    bundle_zip = 'data/bundles/reactive-maps-backend-region-6273d7a5b059d0e978c6d69ee1a5d7b4f0185008d7e57614a4a20c253a18fe28.zip'

    def test_bundle_download_success(self):
        conf_path = os.path.join(os.path.dirname(__file__), 'data/bundles/conf.zip')
        bundle_path = os.path.join(os.path.dirname(__file__), self.bundle_zip)
        conf_file = open(conf_path, 'rb')
        bundle_file = open(bundle_path, 'rb')
        fields = {
            'conf': ('conf.zip', conf_file, 'application/octet-stream'),
            'bundle': ('bundle.zip', bundle_file, 'application/octet-stream'),
        }

        multipart_data = MultipartEncoder(fields=fields)

        mock_bundle = self.respond_with_multi_part_contents(multipart_data.to_string(), multipart_data.content_type)
        input_args = MagicMock(**self.args)
        with patch('conductr_cli.conduct_request.get', mock_bundle):
            result = bundle_files(input_args, '45e0c477d3e5ea92aa8d85c0d8f3e25c')
            mock_bundle.assert_called_once_with(False, '127.0.0.1', self.bundle_url, auth=self.conductr_auth,
                                                verify=self.server_verification_file,
                                                timeout=DEFAULT_HTTP_TIMEOUT, headers={'Accept': 'multipart/form-data'})
            self.assertEqual(2, len(result))

        conf_file.close()
        bundle_file.close()

    def test_bundle_download_failure(self):
        mock_bundle = self.respond_with(404)
        input_args = MagicMock(**self.args)

        with patch('conductr_cli.conduct_request.get', mock_bundle):
            self.assertRaises(ConductBackupError,
                              lambda: bundle_files(input_args, '45e0c477d3e5ea92aa8d85c0d8f3e25c')
                              )
            mock_bundle.assert_called_once_with(False, '127.0.0.1', self.bundle_url, auth=self.conductr_auth,
                                                verify=self.server_verification_file,
                                                timeout=DEFAULT_HTTP_TIMEOUT, headers={'Accept': 'multipart/form-data'})

    def test_bundle_validation_success(self):
        bundle_path = os.path.join(os.path.dirname(__file__), self.bundle_zip)

        result = validate_artifact(bundle_path,
                                   '6273d7a5b059d0e978c6d69ee1a5d7b4f0185008d7e57614a4a20c253a18fe28')
        self.assertTrue(result)

    def test_bundle_validation_failure(self):
        bundle_path = os.path.join(os.path.dirname(__file__), self.bundle_zip)

        result = validate_artifact(bundle_path, 'wrong')
        self.assertFalse(result)


class TestBackup(CliTestCase):
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
        'bundle': 'some_id',
        'output_path': '/my/fav/path',
        'conductr_auth': conductr_auth,
        'server_verification_file': server_verification_file
    }

    bundle_json = file_contents('data/bundles/bundle_json.json')

    backup_path = 'some/path'
    bundle_zip = 'data/bundles/reactive-maps-backend-region-6273d7a5b059d0e978c6d69ee1a5d7b4f0185008d7e57614a4a20c253a18fe28.zip'

    @patch('conductr_cli.control_protocol.get_members')
    def test_backup_members(self, members_mock):
        mock_args = MagicMock(**self.args)
        members_mock.return_value = '{}'
        backup_path = 'some/path'

        open_mock = mock.mock_open()
        members_json_path = os.path.join(backup_path, 'members.json')

        with patch('builtins.open', open_mock):
            backup_members(mock_args, backup_path)

        members_mock.assert_called_once_with(mock_args)
        open_mock.assert_called_once_with(members_json_path, 'w', encoding='utf-8')
        open_mock.return_value.__enter__.return_value.writelines.assert_called_once_with('"{}"')

    @patch('conductr_cli.control_protocol.get_agents')
    def test_backup_agents(self, agents_mock):
        mock_args = MagicMock(**self.args)
        backup_path = 'some/path'

        agents_mock.return_value = 'dummy'
        open_mock = mock.mock_open()
        agents_json_path = os.path.join(backup_path, 'agents.json')

        with patch('builtins.open', open_mock):
            backup_agents(mock_args, backup_path)

        agents_mock.assert_called_once_with(mock_args)
        open_mock.assert_called_once_with(agents_json_path, 'w', encoding='utf-8')
        open_mock.return_value.__enter__.return_value.writelines.assert_called_once_with('"dummy"')

    def test_backup_bundle_json(self):
        backup_path = 'some/path'
        bundle_data = 'my awesome data'
        open_mock = mock.mock_open()
        bundles_json_path = os.path.join(backup_path, 'bundles.json')

        with patch('builtins.open', open_mock):
            backup_bundle_json(backup_path, bundle_data)

        open_mock.assert_called_once_with(bundles_json_path, 'w', encoding='utf-8')
        open_mock.return_value.__enter__.return_value.writelines.assert_called_once_with(bundle_data)

    @patch('conductr_cli.conductr_backup.validate_artifact')
    def test_backup_bundle_conf(self, validate_mock):
        validate_mock.return_value = True
        mock_bundle_conf = MagicMock()

        backup_path = 'bkp_path'
        mock_bundle_info = BundleCoreInfo('b_id', 'b_name', '12345', '789')

        open_mock = mock.mock_open()
        with patch('builtins.open', open_mock):
            validated = backup_bundle_conf(backup_path, mock_bundle_conf, mock_bundle_info)

        bundle_conf_path = '{}.zip'.format(os.path.join(backup_path, 'b_name-789'))
        self.assertTrue(validated)

        validate_mock.assert_called_once_with(bundle_conf_path, '789')

    @patch('tempfile.mkdtemp')
    @patch('conductr_cli.conductr_backup.remove_backup_directory')
    @patch('conductr_cli.conductr_backup.bundles')
    def test_backup_conductr_should_raise_error_when_invalid_bundle_id_is_specified(self, bundles_mock,
                                                                                    remove_directory_mock,
                                                                                    tempfile_mock):
        mock_args = MagicMock(**self.args)
        bundles_mock.return_value = self.bundle_json

        temp_file = MagicMock()
        tempfile_mock.return_value = temp_file
        open_mock = mock.mock_open()

        with patch('builtins.open', open_mock):
            backup(mock_args)

        remove_directory_mock.assert_called_once_with(temp_file)

    @patch('conductr_cli.conductr_backup.validate_artifact')
    def test_backup_bundle_files(self, validate_mock):
        validate_mock.return_value = True
        mock_bundle_file = MagicMock()
        mock_bundle_info = BundleCoreInfo('b_id', 'b_name', '12345', '789')

        backup_path = 'bkp_path'
        open_mock = mock.mock_open()
        with patch('builtins.open', open_mock):
            validated = backup_bundle_file(backup_path, mock_bundle_file, mock_bundle_info)
            bundle_file_path = '{}.zip'.format(os.path.join(backup_path, mock_bundle_info.bundle_name_with_digest))
            self.assertTrue(validated)

        validate_mock.assert_called_once_with(bundle_file_path, '12345')

    @patch('conductr_cli.conductr_backup.backup_bundle')
    def test_process_added_bundles(self, backup_bundle_mock):
        mock_args = MagicMock(**self.args)
        backup_path = '/my/path'
        first = BundleCoreInfo('1', 'b_name', '12345', '789')
        second = BundleCoreInfo('2', 'b_name2', '12345', '789')
        third = BundleCoreInfo('3', 'b_name3', '12345', '789')
        fourth = BundleCoreInfo('4', 'b_name4', '12345', '789')
        initial_bundle_core_info = (first, second, third)
        final_bundle_core_info = (first, second, fourth)

        process_added_bundles(mock_args, backup_path, initial_bundle_core_info, final_bundle_core_info)

        backup_bundle_mock.assert_called_once_with(mock_args, backup_path, fourth)

    @patch('conductr_cli.conductr_backup.remove_bundle')
    def test_process_removed_bundles(self, remove_bundle_mock):
        backup_path = '/my/path'
        first = BundleCoreInfo('1', 'b_name', '12345', '789')
        second = BundleCoreInfo('2', 'b_name2', '12345', '789')
        third = BundleCoreInfo('3', 'b_name3', '12345', '789')
        fourth = BundleCoreInfo('4', 'b_name4', '12345', '789')
        initial_bundle_core_info = (first, second, third)
        final_bundle_core_info = (first, second, fourth)

        process_removed_bundles(backup_path, initial_bundle_core_info, final_bundle_core_info)

        remove_bundle_mock.assert_called_once_with(backup_path, third)

    @patch('conductr_cli.conductr_backup.bundle_files')
    @patch('conductr_cli.conductr_backup.backup_bundle_file')
    @patch('conductr_cli.conductr_backup.backup_bundle_conf')
    def test_backup_bundle_should_raise_error_when_bundle_validation_fails(self, backup_bundle_conf_mock,
                                                                           backup_bundle_mock,
                                                                           bundle_files_mock):
        mock_args = MagicMock(**self.args)
        backup_path = '/bkp/path'
        bundle_info = BundleCoreInfo('b_id', 'b_name', '12345', '789')
        bundle_files_mock.return_value = [1, 2]
        backup_bundle_mock.return_value = False

        self.assertRaises(ConductBackupError, lambda: backup_bundle(mock_args, backup_path, bundle_info))

        bundle_files_mock.assert_called_once_with(mock_args, bundle_info.bundle_id)
        backup_bundle_mock.assert_called_once_with(backup_path, 1, bundle_info)
        backup_bundle_conf_mock.assert_called_once_with(backup_path, 2, bundle_info)

    @patch('conductr_cli.conductr_backup.bundle_files')
    @patch('conductr_cli.conductr_backup.backup_bundle_file')
    @patch('conductr_cli.conductr_backup.backup_bundle_conf')
    def test_backup_bundle_should_raise_error_when_conf_validation_fails(self, backup_bundle_conf_mock,
                                                                         backup_bundle_file_mock,
                                                                         bundle_files_mock):
        mock_args = MagicMock(**self.args)
        backup_path = '/bkp/path'
        bundle_info = BundleCoreInfo('b_id', 'b_name', '12345', '789')
        bundle_files_mock.return_value = [1, 2]

        backup_bundle_file_mock.return_value = True
        backup_bundle_conf_mock.return_value = False

        self.assertRaises(ConductBackupError, lambda: backup_bundle(mock_args, backup_path, bundle_info))

        bundle_files_mock.assert_called_once_with(mock_args, bundle_info.bundle_id)
        backup_bundle_file_mock.assert_called_once_with(backup_path, 1, bundle_info)
        backup_bundle_conf_mock.assert_called_once_with(backup_path, 2, bundle_info)

    @patch('conductr_cli.conductr_backup.bundle_files')
    @patch('conductr_cli.conductr_backup.backup_bundle_file')
    @patch('conductr_cli.conductr_backup.backup_bundle_conf')
    @patch('conductr_cli.conductr_backup.remove_backup_directory')
    def test_backup_bundle_should_not_raise_error_when_validation_succeeds(self, remove_directory_mock,
                                                                           backup_bundle_conf_mock,
                                                                           backup_bundle_file_mock,
                                                                           bundle_files_mock):
        mock_args = MagicMock(**self.args)
        backup_path = '/bkp/path'
        bundle_info = BundleCoreInfo('b_id', 'b_name', '12345', '789')
        bundle_files_mock.return_value = [1, 2]

        backup_bundle_file_mock.return_value = True
        backup_bundle_conf_mock.return_value = True

        backup_bundle(mock_args, backup_path, bundle_info)

        bundle_files_mock.assert_called_once_with(mock_args, bundle_info.bundle_id)
        backup_bundle_file_mock.assert_called_once_with(backup_path, 1, bundle_info)
        backup_bundle_conf_mock.assert_called_once_with(backup_path, 2, bundle_info)

    @patch('conductr_cli.conductr_backup.bundle_files')
    @patch('conductr_cli.conductr_backup.backup_bundle_file')
    @patch('conductr_cli.conductr_backup.backup_bundle_conf')
    @patch('conductr_cli.conductr_backup.remove_backup_directory')
    def test_backup_bundle_should_succeed_when_there_is_no_conf(self, remove_directory_mock,
                                                                backup_bundle_conf_mock,
                                                                backup_bundle_file_mock,
                                                                bundle_files_mock):
        mock_args = MagicMock(**self.args)
        backup_path = '/bkp/path'
        bundle_info = BundleCoreInfo('b_id', 'b_name', '12345', '789')
        bundle_files_mock.return_value = [1]

        backup_bundle_file_mock.return_value = True

        backup_bundle(mock_args, backup_path, bundle_info)

        bundle_files_mock.assert_called_once_with(mock_args, bundle_info.bundle_id)
        backup_bundle_file_mock.assert_called_once_with(backup_path, 1, bundle_info)

    @patch('os.remove')
    def test_remove_bundle_success(self, os_remove_mock):
        backup_path = '/bkp/path'
        bundle_info = BundleCoreInfo('b_id', 'b_name', '12345', '789')

        remove_bundle(backup_path, bundle_info)

        bundle_file_path = '{}.zip'.format(os.path.join(backup_path, bundle_info.bundle_name_with_digest))
        os_remove_mock.assert_any_call(bundle_file_path)
        bundle_conf_path = '{}.zip'.format(os.path.join(backup_path, bundle_info.configuration_digest))
        os_remove_mock.assert_any_call(bundle_conf_path)

    @patch('os.remove')
    def test_remove_bundle_failure(self, os_remove_mock):
        backup_path = '/bkp/path'
        bundle_info = BundleCoreInfo('b_id', 'b_name', '12345', '789')
        os_remove_mock.side_effect = OSError()
        self.assertRaises(ConductBackupError, lambda: remove_bundle(backup_path, bundle_info))

    @patch('tempfile.mkdtemp')
    @patch('conductr_cli.conductr_backup.compress_backup')
    @patch('conductr_cli.conductr_backup.remove_backup_directory')
    @patch('conductr_cli.conductr_backup.backup_members')
    @patch('conductr_cli.conductr_backup.backup_agents')
    @patch('conductr_cli.conductr_backup.bundles')
    @patch('conductr_cli.conductr_backup.backup_bundle')
    @patch('conductr_cli.conductr_backup.backup_bundle_json')
    def test_should_backup_bundle(self, backup_bundle_json_mock,
                                  backup_bundle_mock,
                                  bundles_mock, agents_mock, members_mock,
                                  remove_backup_directory, compress_backup_mock,
                                  tempfile_mock):
        bundle_id = '6273d7a5b059d0e978c6d69ee1a5d7b4-d54620c7bc91897bbb2f25faaac25f46'
        args_valid_bundle = {
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
            'bundle': bundle_id,
            'output_path': '/my/fav/path',
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        }

        mock_args = MagicMock(**args_valid_bundle)

        bundles_mock.return_value = self.bundle_json

        temp_file = MagicMock()
        tempfile_mock.return_value = temp_file

        open_mock = mock.mock_open()
        with patch('builtins.open', open_mock):
            backup(mock_args)

        bundle_info = BundleCoreInfo(bundle_id=bundle_id,
                                     bundle_name='reactive-maps-backend-region',
                                     bundle_digest='6273d7a5b059d0e978c6d69ee1a5d7b4f0185008d7e57614a4a20c253a18fe28',
                                     configuration_digest='d54620c7bc91897bbb2f25faaac25f46b11e029ed327f91c7a10931ec45bd792')

        backup_bundle_json_mock.assert_called_once_with(temp_file, ANY)
        backup_bundle_mock.assert_called_once_with(mock_args, temp_file, bundle_info)
        members_mock.assert_called_once_with(mock_args, temp_file)
        agents_mock.assert_called_once_with(mock_args, temp_file)
        remove_backup_directory.assert_called_once_with(temp_file)
        compress_backup_mock.assert_called_once_with('/my/fav/path', temp_file)

    @patch('tempfile.mkdtemp')
    @patch('conductr_cli.conductr_backup.compress_backup')
    @patch('conductr_cli.conductr_backup.remove_backup_directory')
    @patch('conductr_cli.conductr_backup.backup_members')
    @patch('conductr_cli.conductr_backup.backup_agents')
    @patch('conductr_cli.conductr_backup.bundles')
    @patch('conductr_cli.conductr_backup.backup_bundle')
    @patch('conductr_cli.conductr_backup.backup_bundle_json')
    @patch('conductr_cli.conductr_backup.process_removed_bundles')
    @patch('conductr_cli.conductr_backup.process_added_bundles')
    def test_should_backup_added_bundles(self, process_added_bundles_mock,
                                         process_removed_bundles_mock, backup_bundle_json_mock,
                                         backup_bundle_mock, bundles_mock,
                                         agents_mock, members_mock,
                                         remove_backup_directory_mock, compress_backup_mock,
                                         tempfile_mock):
        args_no_bundle = {
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
            'bundle': None,
            'output_path': '/my/fav/path',
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        }

        mock_args = MagicMock(**args_no_bundle)

        modified_bundles = file_contents('data/bundles/bundle_json_modified.json')

        bundles_mock.side_effect = [self.bundle_json, modified_bundles]
        temp_file = MagicMock()
        tempfile_mock.return_value = temp_file

        open_mock = mock.mock_open()
        with patch('builtins.open', open_mock):
            backup(mock_args)

        reactive_maps_backend_region = BundleCoreInfo(
            bundle_id='6273d7a5b059d0e978c6d69ee1a5d7b4-d54620c7bc91897bbb2f25faaac25f46',
            bundle_name='reactive-maps-backend-region',
            bundle_digest='6273d7a5b059d0e978c6d69ee1a5d7b4f0185008d7e57614a4a20c253a18fe28',
            configuration_digest='d54620c7bc91897bbb2f25faaac25f46b11e029ed327f91c7a10931ec45bd792')
        continuous_delivery = BundleCoreInfo(
            bundle_id='870ee7d6a4f5853229275cca14b604b8-d54620c7bc91897bbb2f25faaac25f46',
            bundle_name='continuous-delivery',
            bundle_digest='870ee7d6a4f5853229275cca14b604b8aca62a5e74819c0a092858cc75b6c186',
            configuration_digest='d54620c7bc91897bbb2f25faaac25f46b11e029ed327f91c7a10931ec45bd792')
        eslite = BundleCoreInfo(
            bundle_id='57e432d0c647be2bbc83fa8e59ee469b-d54620c7bc91897bbb2f25faaac25f46',
            bundle_name='eslite',
            bundle_digest='57e432d0c647be2bbc83fa8e59ee469bb59d1f72df31f3d82cab0ad396130fe7',
            configuration_digest='d54620c7bc91897bbb2f25faaac25f46b11e029ed327f91c7a10931ec45bd792')
        reactive_maps_backend_summary = BundleCoreInfo(
            bundle_id='abf60451c6af18adcc851d67b369b7f5-d54620c7bc91897bbb2f25faaac25f46',
            bundle_name='reactive-maps-backend-summary',
            bundle_digest='abf60451c6af18adcc851d67b369b7f54810d12f3a0ef80a89bdc2d9dff49a10',
            configuration_digest='d54620c7bc91897bbb2f25faaac25f46b11e029ed327f91c7a10931ec45bd792')
        reactive_maps_frontend = BundleCoreInfo(
            bundle_id='69aa58f00909e36a3cb4229414698b64-d54620c7bc91897bbb2f25faaac25f46',
            bundle_name='reactive-maps-frontend',
            bundle_digest='69aa58f00909e36a3cb4229414698b6436295de8368898b5620b24f52c40c5c3',
            configuration_digest='d54620c7bc91897bbb2f25faaac25f46b11e029ed327f91c7a10931ec45bd792')
        visualiser = BundleCoreInfo(
            bundle_id='cabaae7cf37b1cf99b3861515cd5e77a-d54620c7bc91897bbb2f25faaac25f46',
            bundle_name='visualizer',
            bundle_digest='cabaae7cf37b1cf99b3861515cd5e77a16fa9638e225fa234929cc1d46dde937',
            configuration_digest='d54620c7bc91897bbb2f25faaac25f46b11e029ed327f91c7a10931ec45bd792')
        added = BundleCoreInfo(
            bundle_id='abcd-efgh',
            bundle_name='added_bundle',
            bundle_digest='abcd',
            configuration_digest='efgh')

        initial = [reactive_maps_backend_region, continuous_delivery, eslite, reactive_maps_backend_summary,
                   reactive_maps_frontend,
                   visualiser]
        final = [added, continuous_delivery, eslite, reactive_maps_backend_summary, reactive_maps_frontend, visualiser]

        backup_bundle_json_mock.assert_called_once_with(temp_file, modified_bundles)
        process_removed_bundles_mock.assert_called_once_with(temp_file, initial, final)
        process_added_bundles_mock.assert_called_once_with(mock_args, temp_file, initial, final)
        members_mock.assert_called_once_with(mock_args, temp_file)
        agents_mock.assert_called_once_with(mock_args, temp_file)
        remove_backup_directory_mock.assert_called_once_with(temp_file)
        compress_backup_mock.assert_called_once_with('/my/fav/path', temp_file)
