from conductr_cli.test.cli_test_case import CliTestCase
from conductr_cli import logging_setup
from conductr_cli.exceptions import S3InvalidArtefactError, S3MalformedUrlError
from conductr_cli.resolvers import s3_resolver
from conductr_cli.resolvers.schemes import SCHEME_S3
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound
from unittest.mock import call, patch, MagicMock
import io


class TestResolve(CliTestCase):
    cache_dir = '/tmp'
    bucket_name = 'myorg'
    s3_key = 'bundle/weather/weather-v3-digest.zip'
    valid_s3_url = 's3://{}/{}'.format(bucket_name, s3_key)

    def test_resolve_bundle(self):
        download_result = MagicMock()
        mock_download_from_s3 = MagicMock(return_value=download_result)

        with patch('conductr_cli.resolvers.s3_resolver.download_from_s3', mock_download_from_s3):
            result = s3_resolver.resolve_bundle(self.cache_dir, self.valid_s3_url)
            self.assertEqual(download_result, result)

        mock_download_from_s3.assert_called_once_with(self.cache_dir, self.bucket_name, self.s3_key)

    def test_resolve_bundle_configuration(self):
        download_result = MagicMock()
        mock_download_from_s3 = MagicMock(return_value=download_result)

        with patch('conductr_cli.resolvers.s3_resolver.download_from_s3', mock_download_from_s3):
            result = s3_resolver.resolve_bundle_configuration(self.cache_dir, self.valid_s3_url)
            self.assertEqual(download_result, result)

        mock_download_from_s3.assert_called_once_with(self.cache_dir, self.bucket_name, self.s3_key)

    def test_resolve_bundle_non_s3_url(self):
        mock_download_from_s3 = MagicMock()

        with patch('conductr_cli.resolvers.s3_resolver.download_from_s3', mock_download_from_s3):
            result = s3_resolver.resolve_bundle(self.cache_dir, 'http://example.org')
            self.assertEqual((False, None, None, None), result)

        mock_download_from_s3.assert_not_called()

    def test_resolve_bundle_configuration_non_s3_url(self):
        mock_download_from_s3 = MagicMock()

        with patch('conductr_cli.resolvers.s3_resolver.download_from_s3', mock_download_from_s3):
            result = s3_resolver.resolve_bundle_configuration(self.cache_dir, 'http://example.org')
            self.assertEqual((False, None, None, None), result)

        mock_download_from_s3.assert_not_called()

    def test_resolve_bundle_no_credentials_error(self):
        error = NoCredentialsError()
        mock_download_from_s3 = MagicMock(side_effect=error)

        with patch('conductr_cli.resolvers.s3_resolver.download_from_s3', mock_download_from_s3):
            result = s3_resolver.resolve_bundle(self.cache_dir, self.valid_s3_url)
            self.assertEqual((False, None, None, error), result)

        mock_download_from_s3.assert_called_once_with(self.cache_dir, self.bucket_name, self.s3_key)

    def test_resolve_bundle_configuration_no_credentials_error(self):
        error = NoCredentialsError()
        mock_download_from_s3 = MagicMock(side_effect=error)

        with patch('conductr_cli.resolvers.s3_resolver.download_from_s3', mock_download_from_s3):
            result = s3_resolver.resolve_bundle_configuration(self.cache_dir, self.valid_s3_url)
            self.assertEqual((False, None, None, error), result)

    def test_resolve_bundle_malformed_url_error(self):
        mock_download_from_s3 = MagicMock()

        with patch('conductr_cli.resolvers.s3_resolver.download_from_s3', mock_download_from_s3):
            is_resolved, file_name, file_path, error = s3_resolver.resolve_bundle(self.cache_dir, 's3://bucket')
            self.assertFalse(is_resolved)
            self.assertIsNone(file_name)
            self.assertIsNone(file_path)
            self.assertIsInstance(error, S3MalformedUrlError)

        mock_download_from_s3.assert_not_called()

    def test_resolve_bundle_configuration_malformed_url_error(self):
        mock_download_from_s3 = MagicMock()

        with patch('conductr_cli.resolvers.s3_resolver.download_from_s3', mock_download_from_s3):
            is_resolved, file_name, file_path, error = s3_resolver.resolve_bundle_configuration(self.cache_dir,
                                                                                                's3://bucket')
            self.assertFalse(is_resolved)
            self.assertIsNone(file_name)
            self.assertIsNone(file_path)
            self.assertIsInstance(error, S3MalformedUrlError)

        mock_download_from_s3.assert_not_called()


class TestLoadFromCache(CliTestCase):
    cache_dir = '/tmp'
    bucket_name = 'myorg'
    s3_key = 'bundle/weather/weather-v3-digest.zip'
    valid_s3_url = 's3://{}/{}'.format(bucket_name, s3_key)

    def test_load_bundle_from_cache_found(self):
        mock_exists = MagicMock(return_value=True)
        stdout = MagicMock()

        with patch('os.path.exists', mock_exists):
            logging_setup.configure_logging(MagicMock(**{}), stdout)
            result = s3_resolver.load_bundle_from_cache(self.cache_dir, self.valid_s3_url)
            self.assertEqual((True, 'weather-v3-digest.zip', '/tmp/weather-v3-digest.zip', None), result)

        mock_exists.assert_called_once_with('/tmp/weather-v3-digest.zip')
        self.assertEqual('Retrieving from cache /tmp/weather-v3-digest.zip\n', self.output(stdout))

    def test_load_bundle_from_cache_not_found(self):
        mock_exists = MagicMock(return_value=False)
        stdout = MagicMock()

        with patch('os.path.exists', mock_exists):
            logging_setup.configure_logging(MagicMock(**{}), stdout)
            result = s3_resolver.load_bundle_from_cache(self.cache_dir, self.valid_s3_url)
            self.assertEqual((False, None, None, None), result)

        mock_exists.assert_called_once_with('/tmp/weather-v3-digest.zip')
        self.assertEqual('', self.output(stdout))

    def test_load_bundle_configuration_from_cache_found(self):
        mock_exists = MagicMock(return_value=True)
        stdout = MagicMock()

        with patch('os.path.exists', mock_exists):
            logging_setup.configure_logging(MagicMock(**{}), stdout)
            result = s3_resolver.load_bundle_configuration_from_cache(self.cache_dir, self.valid_s3_url)
            self.assertEqual((True, 'weather-v3-digest.zip', '/tmp/weather-v3-digest.zip', None), result)

        mock_exists.assert_called_once_with('/tmp/weather-v3-digest.zip')
        self.assertEqual('Retrieving from cache /tmp/weather-v3-digest.zip\n', self.output(stdout))

    def test_load_bundle_configuration_from_cache_not_found(self):
        mock_exists = MagicMock(return_value=False)
        stdout = MagicMock()

        with patch('os.path.exists', mock_exists):
            logging_setup.configure_logging(MagicMock(**{}), stdout)
            result = s3_resolver.load_bundle_configuration_from_cache(self.cache_dir, self.valid_s3_url)
            self.assertEqual((False, None, None, None), result)

        mock_exists.assert_called_once_with('/tmp/weather-v3-digest.zip')
        self.assertEqual('', self.output(stdout))

    def test_non_s3_url(self):
        mock_exists = MagicMock()
        stdout = MagicMock()

        with patch('os.path.exists', mock_exists):
            logging_setup.configure_logging(MagicMock(**{}), stdout)
            result = s3_resolver.load_bundle_configuration_from_cache(self.cache_dir, 'http://example.org')
            self.assertEqual((False, None, None, None), result)

        mock_exists.assert_not_called()
        self.assertEqual('', self.output(stdout))


class TestOtherMethods(CliTestCase):
    def test_resolve_bundle_version(self):
        mock_uri = MagicMock()
        self.assertIsNone(s3_resolver.resolve_bundle_version(mock_uri))
        mock_uri.assert_not_called()

    def test_continuous_delivery_uri(self):
        mock_resolved_version = MagicMock()
        self.assertIsNone(s3_resolver.continuous_delivery_uri(mock_resolved_version))
        mock_resolved_version.assert_not_called()


class TestS3BucketAndKeyFromUri(CliTestCase):
    def test_success(self):
        self.assertEqual(('bucket', 'path/to/key.zip'),
                         s3_resolver.s3_bucket_and_key_from_uri('s3://bucket/path/to/key.zip'))
        self.assertEqual(('bucket', 'key'),
                         s3_resolver.s3_bucket_and_key_from_uri('s3://bucket/key'))

    def test_s3_url_without_key(self):
        self.assertEqual((None, None),
                         s3_resolver.s3_bucket_and_key_from_uri('s3://bucket'))

    def test_invalid_s3_url(self):
        self.assertEqual((None, None),
                         s3_resolver.s3_bucket_and_key_from_uri('s3://'))

    def test_non_s3_url(self):
        self.assertEqual((None, None),
                         s3_resolver.s3_bucket_and_key_from_uri('visualizer'))
        self.assertEqual((None, None),
                         s3_resolver.s3_bucket_and_key_from_uri('/tmp/path'))
        self.assertEqual((None, None),
                         s3_resolver.s3_bucket_and_key_from_uri('http://example.org'))


class TestIsS3Url(CliTestCase):
    def test_urls(self):
        self.assertTrue(s3_resolver.is_s3_url('s3://bucket/path/to/key.zip'))
        self.assertTrue(s3_resolver.is_s3_url('s3://bucket/path/to/key'))
        self.assertTrue(s3_resolver.is_s3_url('s3://bucket'))

        self.assertFalse(s3_resolver.is_s3_url('/tmp/foo'))
        self.assertFalse(s3_resolver.is_s3_url('/tmp'))
        self.assertFalse(s3_resolver.is_s3_url('visualizer'))
        self.assertFalse(s3_resolver.is_s3_url('http://test.com/abc/def'))
        self.assertFalse(s3_resolver.is_s3_url('http://test.com'))


class TestDownloadFromS3(CliTestCase):
    cache_dir = '/tmp'
    bucket_name = 'acme-org'
    key_name = 'bundle/builder/builder-v1-digest.zip'

    artefact_size = 100
    artefact_data = MagicMock(name='artefact data')
    artefact = {
        'ContentLength': artefact_size,
        'Body': artefact_data
    }

    def test_success(self):
        mock_get_object = MagicMock(return_value=self.artefact)

        mock_s3_client = MagicMock()
        mock_s3_client.get_object = mock_get_object

        mock_create_s3_client = MagicMock(return_value=mock_s3_client)
        mock_validate_artefact = MagicMock()
        mock_save_artefact_data_to_file = MagicMock()
        mock_move = MagicMock()

        with patch('conductr_cli.resolvers.s3_resolver.create_s3_client', mock_create_s3_client), \
                patch('conductr_cli.resolvers.s3_resolver.validate_artefact', mock_validate_artefact), \
                patch('conductr_cli.resolvers.s3_resolver.save_artefact_data_to_file',
                      mock_save_artefact_data_to_file), \
                patch('shutil.move', mock_move):
            result = s3_resolver.download_from_s3(self.cache_dir, self.bucket_name, self.key_name)
            self.assertEqual((True, 'builder-v1-digest.zip', '/tmp/builder-v1-digest.zip', None), result)

        mock_create_s3_client.assert_called_once_with()
        mock_s3_client.get_object.assert_called_once_with(Bucket=self.bucket_name, Key=self.key_name)
        mock_validate_artefact.assert_called_once_with(self.artefact)
        mock_save_artefact_data_to_file.assert_called_once_with(self.artefact_size,
                                                                self.artefact_data,
                                                                '/tmp/builder-v1-digest.zip.tmp')
        mock_move.assert_called_once_with('/tmp/builder-v1-digest.zip.tmp', '/tmp/builder-v1-digest.zip')

    def test_client_error(self):
        error = ClientError(MagicMock(), MagicMock())
        mock_get_object = MagicMock(side_effect=error)

        mock_s3_client = MagicMock()
        mock_s3_client.get_object = mock_get_object

        mock_create_s3_client = MagicMock(return_value=mock_s3_client)
        mock_validate_artefact = MagicMock()
        mock_save_artefact_data_to_file = MagicMock()
        mock_move = MagicMock()

        with patch('conductr_cli.resolvers.s3_resolver.create_s3_client', mock_create_s3_client), \
                patch('conductr_cli.resolvers.s3_resolver.validate_artefact', mock_validate_artefact), \
                patch('conductr_cli.resolvers.s3_resolver.save_artefact_data_to_file',
                      mock_save_artefact_data_to_file), \
                patch('shutil.move', mock_move):
            result = s3_resolver.download_from_s3(self.cache_dir, self.bucket_name, self.key_name)
            self.assertEqual((False, None, None, error), result)

        mock_create_s3_client.assert_called_once_with()
        mock_s3_client.get_object.assert_called_once_with(Bucket=self.bucket_name, Key=self.key_name)
        mock_validate_artefact.assert_not_called()
        mock_save_artefact_data_to_file.assert_not_called()
        mock_move.assert_not_called()

    def test_invalid_artefact_error(self):
        mock_get_object = MagicMock(return_value=self.artefact)

        mock_s3_client = MagicMock()
        mock_s3_client.get_object = mock_get_object

        mock_create_s3_client = MagicMock(return_value=mock_s3_client)
        error = S3InvalidArtefactError('test')
        mock_validate_artefact = MagicMock(side_effect=error)
        mock_save_artefact_data_to_file = MagicMock()
        mock_move = MagicMock()

        with patch('conductr_cli.resolvers.s3_resolver.create_s3_client', mock_create_s3_client), \
                patch('conductr_cli.resolvers.s3_resolver.validate_artefact', mock_validate_artefact), \
                patch('conductr_cli.resolvers.s3_resolver.save_artefact_data_to_file',
                      mock_save_artefact_data_to_file), \
                patch('shutil.move', mock_move):
            result = s3_resolver.download_from_s3(self.cache_dir, self.bucket_name, self.key_name)
            self.assertEqual((False, None, None, error), result)

        mock_create_s3_client.assert_called_once_with()
        mock_s3_client.get_object.assert_called_once_with(Bucket=self.bucket_name, Key=self.key_name)
        mock_validate_artefact.assert_called_once_with(self.artefact)
        mock_save_artefact_data_to_file.assert_not_called()
        mock_move.assert_not_called()


class TestValidateArtefact(CliTestCase):
    def test_success(self):
        artefact = {
            'ContentType': 'application/zip',
            'ContentLength': 2,
            'Body': MagicMock()
        }
        s3_resolver.validate_artefact(artefact)

    def test_missing_content_length(self):
        artefact = {
            'ContentType': 'application/zip',
            'Body': MagicMock()
        }
        with self.assertRaises(S3InvalidArtefactError):
            s3_resolver.validate_artefact(artefact)

    def test_invalid_content_length(self):
        artefact = {
            'ContentType': 'application/zip',
            'ContentLength': -1,
            'Body': MagicMock()
        }
        with self.assertRaises(S3InvalidArtefactError):
            s3_resolver.validate_artefact(artefact)

    def test_missing_content_type(self):
        artefact = {
            'ContentLength': 2,
            'Body': MagicMock()
        }
        with self.assertRaises(S3InvalidArtefactError):
            s3_resolver.validate_artefact(artefact)

    def test_invalid_content_type(self):
        artefact = {
            'ContentType': 'text/plain',
            'ContentLength': 2,
            'Body': MagicMock()
        }
        with self.assertRaises(S3InvalidArtefactError):
            s3_resolver.validate_artefact(artefact)

    def test_missing_body(self):
        artefact = {
            'ContentType': 'application/zip',
            'ContentLength': -1,
        }
        with self.assertRaises(S3InvalidArtefactError):
            s3_resolver.validate_artefact(artefact)


class TestSaveArtefactDataToFile(CliTestCase):
    artefact_size = 2
    file_path = '/tmp/bar/foo.zip'
    args = MagicMock(**{})

    def test_success(self):
        mock_makedirs = MagicMock()
        mock_exists = MagicMock(side_effect=[False, True])
        mock_remove = MagicMock()

        mock_artefact_data = MagicMock()

        mock_artefact_data_read = MagicMock(return_value=b'0')
        mock_artefact_data.read = mock_artefact_data_read

        mock_artefact_data_close = MagicMock()
        mock_artefact_data.close = mock_artefact_data_close

        written_data = io.BytesIO()
        written_data.write = MagicMock()
        mock_open = MagicMock(return_value=written_data)

        mock_progress_bar = MagicMock(return_value='#')

        mock_time = MagicMock(side_effect=[i for i in range(0, 100)])

        stdout = MagicMock()

        with patch('os.makedirs', mock_makedirs), \
                patch('os.path.exists', mock_exists), \
                patch('os.remove', mock_remove), \
                patch('builtins.open', mock_open), \
                patch('time.time', mock_time), \
                patch('conductr_cli.screen_utils.progress_bar', mock_progress_bar):
            logging_setup.configure_logging(self.args, stdout)
            result = s3_resolver.save_artefact_data_to_file(self.artefact_size, mock_artefact_data, self.file_path)
            self.assertEqual(self.file_path, result)

        mock_makedirs.assert_called_once_with('/tmp/bar', mode=0o700)

        self.assertEqual([
            call('/tmp/bar'),
            call(self.file_path),
        ], mock_exists.call_args_list)

        mock_remove.assert_called_once_with(self.file_path)

        self.assertEqual([
            call(s3_resolver.DATA_READ_CHUNK_SIZE),
            call(s3_resolver.DATA_READ_CHUNK_SIZE),
        ], mock_artefact_data_read.call_args_list)

        self.assertEqual([
            call(0.5),
            call(1.0),
        ], mock_progress_bar.call_args_list)

        self.assertEqual([
            call(b'0'),
            call(b'0'),
        ], written_data.write.call_args_list)

        mock_artefact_data_close.assert_called_once_with()

        self.assertTrue(written_data.closed)

        self.assertEqual('#\r#\n', self.output(stdout))

    def test_error(self):
        mock_makedirs = MagicMock()
        mock_exists = MagicMock(side_effect=[False, True])
        mock_remove = MagicMock()

        mock_artefact_data = MagicMock()

        mock_artefact_data_read = MagicMock(return_value=b'0')
        mock_artefact_data.read = mock_artefact_data_read

        mock_artefact_data_close = MagicMock()
        mock_artefact_data.close = mock_artefact_data_close

        written_data = io.BytesIO()
        error = IOError('test only')
        written_data.write = MagicMock(side_effect=error)
        mock_open = MagicMock(return_value=written_data)

        mock_progress_bar = MagicMock(return_value='#')

        mock_time = MagicMock(side_effect=[i for i in range(0, 100)])

        stdout = MagicMock()

        with patch('os.makedirs', mock_makedirs), \
                patch('os.path.exists', mock_exists), \
                patch('os.remove', mock_remove), \
                patch('builtins.open', mock_open), \
                patch('time.time', mock_time), \
                patch('conductr_cli.screen_utils.progress_bar', mock_progress_bar), \
                self.assertRaises(IOError) as e:
            logging_setup.configure_logging(self.args, stdout)
            s3_resolver.save_artefact_data_to_file(self.artefact_size, mock_artefact_data, self.file_path)

        self.assertEqual(error, e.exception)
        mock_artefact_data_close.assert_called_once_with()


class TestCreateS3Client(CliTestCase):

    def test_use_conductr_profile(self):
        mock_session = MagicMock()

        mock_create_session = MagicMock(return_value=mock_session)

        mock_client = MagicMock()
        mock_session.client = MagicMock(return_value=mock_client)

        with patch('boto3.Session', mock_create_session):
            result = s3_resolver.create_s3_client()
            self.assertEqual(mock_client, result)

        mock_create_session.assert_called_once_with(profile_name='conductr')
        mock_session.client.assert_called_once_with('s3')

    def test_use_default_profile(self):
        mock_session = MagicMock()

        mock_create_session = MagicMock(side_effect=[
            ProfileNotFound(profile='conductr'),
            mock_session
        ])

        mock_client = MagicMock()
        mock_session.client = MagicMock(return_value=mock_client)

        with patch('boto3.Session', mock_create_session):
            result = s3_resolver.create_s3_client()
            self.assertEqual(mock_client, result)

        self.assertEqual([
            call(profile_name='conductr'),
            call(),
        ], mock_create_session.call_args_list)
        mock_session.client.assert_called_once_with('s3')


class TestSupportedSchemes(CliTestCase):
    def test_supported_schemes(self):
        self.assertEqual([SCHEME_S3], s3_resolver.supported_schemes())
