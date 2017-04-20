from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import license, logging_setup
from conductr_cli.exceptions import LicenseDownloadError
from conductr_cli.license import EXPIRY_DATE_DISPLAY_FORMAT
from unittest import TestCase
from unittest.mock import patch, MagicMock
from requests.exceptions import HTTPError
from dcos.errors import DCOSHTTPException
import arrow
import datetime
import json
import tempfile


class TestDownloadLicense(CliTestCase):
    cached_token = 'test-token'
    cached_token_b64 = 'dGVzdC10b2tlbg=='
    license_text = 'test-license-text'
    license_download_url = 'http://test.com/download'
    server_verification_file = 'test-server_verification_file'
    license_file = '~/.lightbend/license'

    args = {
        'dcos_mode': False,
        'license_download_url': license_download_url,
        'server_verification_file': server_verification_file
    }

    def test_download_with_cached_token(self):
        stdout = MagicMock()

        mock_get_cached_auth_token = MagicMock(return_value=self.cached_token)
        mock_prompt_for_auth_token = MagicMock()
        mock_get = self.respond_with(200, self.license_text)
        mock_save_auth_token = MagicMock()
        mock_save_license_data = MagicMock()

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.license_auth.get_cached_auth_token', mock_get_cached_auth_token), \
                patch('conductr_cli.license_auth.prompt_for_auth_token', mock_prompt_for_auth_token), \
                patch('requests.get', mock_get), \
                patch('conductr_cli.license_auth.save_auth_token', mock_save_auth_token),\
                patch('conductr_cli.license.save_license_data', mock_save_license_data):
            logging_setup.configure_logging(input_args, stdout)
            license.download_license(input_args, save_to=self.license_file, use_cached_auth_token=True)

        mock_get_cached_auth_token.assert_called_once_with()
        mock_prompt_for_auth_token.assert_not_called()
        mock_get.assert_called_once_with(self.license_download_url,
                                         headers={'Authorization': 'Bearer {}'.format(self.cached_token_b64)},
                                         verify=self.server_verification_file)
        mock_save_auth_token.assert_called_once_with(self.cached_token)
        mock_save_license_data.assert_called_once_with(self.license_text, self.license_file)

    def test_download_with_new_token(self):
        stdout = MagicMock()
        mock_get_cached_auth_token = MagicMock(return_value=None)

        prompted_token = 'prompted-token'
        prompted_token_b64 = 'cHJvbXB0ZWQtdG9rZW4='
        mock_prompt_for_auth_token = MagicMock(return_value=prompted_token)

        mock_get = self.respond_with(200, self.license_text)
        mock_save_auth_token = MagicMock()
        mock_save_license_data = MagicMock()

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.license_auth.get_cached_auth_token', mock_get_cached_auth_token), \
                patch('conductr_cli.license_auth.prompt_for_auth_token', mock_prompt_for_auth_token), \
                patch('requests.get', mock_get), \
                patch('conductr_cli.license_auth.save_auth_token', mock_save_auth_token), \
                patch('conductr_cli.license.save_license_data', mock_save_license_data):
            logging_setup.configure_logging(input_args, stdout)
            license.download_license(input_args, save_to=self.license_file, use_cached_auth_token=True)

        mock_get_cached_auth_token.assert_called_once_with()
        mock_prompt_for_auth_token.assert_called_once_with()
        mock_get.assert_called_once_with(self.license_download_url,
                                         headers={'Authorization': 'Bearer {}'.format(prompted_token_b64)},
                                         verify=self.server_verification_file)
        mock_save_auth_token.assert_called_once_with(prompted_token)
        mock_save_license_data.assert_called_once_with(self.license_text, self.license_file)

    def test_expired_token(self):
        stdout = MagicMock()
        mock_get_cached_auth_token = MagicMock(return_value=self.cached_token)
        mock_prompt_for_auth_token = MagicMock()
        mock_get = self.respond_with(401, 'test expired')
        mock_save_auth_token = MagicMock()
        mock_save_license_data = MagicMock()

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.license_auth.get_cached_auth_token', mock_get_cached_auth_token), \
                patch('conductr_cli.license_auth.prompt_for_auth_token', mock_prompt_for_auth_token), \
                patch('requests.get', mock_get), \
                patch('conductr_cli.license_auth.save_auth_token', mock_save_auth_token), \
                patch('conductr_cli.license.save_license_data', mock_save_license_data):
            logging_setup.configure_logging(input_args, stdout)
            self.assertRaises(LicenseDownloadError, license.download_license, input_args, self.license_file, True)

        mock_get_cached_auth_token.assert_called_once_with()
        mock_prompt_for_auth_token.assert_not_called()
        mock_get.assert_called_once_with(self.license_download_url,
                                         headers={'Authorization': 'Bearer {}'.format(self.cached_token_b64)},
                                         verify=self.server_verification_file)
        mock_save_auth_token.assert_not_called()
        mock_save_license_data.assert_not_called()

    def test_invalid_terms_token(self):
        stdout = MagicMock()
        mock_get_cached_auth_token = MagicMock(return_value=self.cached_token)
        mock_prompt_for_auth_token = MagicMock()
        mock_get = self.respond_with(401, 'terms not accepted')
        mock_save_auth_token = MagicMock()
        mock_save_license_data = MagicMock()

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.license_auth.get_cached_auth_token', mock_get_cached_auth_token), \
                patch('conductr_cli.license_auth.prompt_for_auth_token', mock_prompt_for_auth_token), \
                patch('requests.get', mock_get), \
                patch('conductr_cli.license_auth.save_auth_token', mock_save_auth_token), \
                patch('conductr_cli.license.save_license_data', mock_save_license_data):
            logging_setup.configure_logging(input_args, stdout)
            self.assertRaises(LicenseDownloadError, license.download_license, input_args, self.license_file, True)

        mock_get_cached_auth_token.assert_called_once_with()
        mock_prompt_for_auth_token.assert_not_called()
        mock_get.assert_called_once_with(self.license_download_url,
                                         headers={'Authorization': 'Bearer {}'.format(self.cached_token_b64)},
                                         verify=self.server_verification_file)
        mock_save_auth_token.assert_not_called()
        mock_save_license_data.assert_not_called()

    def test_download_ignoring_cached_token(self):
        stdout = MagicMock()
        mock_get_cached_auth_token = MagicMock(return_value=None)

        prompted_token = 'prompted-token'
        prompted_token_b64 = 'cHJvbXB0ZWQtdG9rZW4='
        mock_prompt_for_auth_token = MagicMock(return_value=prompted_token)

        mock_get = self.respond_with(200, self.license_text)
        mock_save_auth_token = MagicMock()
        mock_save_license_data = MagicMock()

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.license_auth.get_cached_auth_token', mock_get_cached_auth_token), \
                patch('conductr_cli.license_auth.prompt_for_auth_token', mock_prompt_for_auth_token), \
                patch('requests.get', mock_get), \
                patch('conductr_cli.license_auth.save_auth_token', mock_save_auth_token), \
                patch('conductr_cli.license.save_license_data', mock_save_license_data):
            logging_setup.configure_logging(input_args, stdout)
            license.download_license(input_args, save_to=self.license_file, use_cached_auth_token=False)

        mock_get_cached_auth_token.assert_not_called()
        mock_prompt_for_auth_token.assert_called_once_with()
        mock_get.assert_called_once_with(self.license_download_url,
                                         headers={'Authorization': 'Bearer {}'.format(prompted_token_b64)},
                                         verify=self.server_verification_file)
        mock_save_auth_token.assert_called_once_with(prompted_token)
        mock_save_license_data.assert_called_once_with(self.license_text, self.license_file)


class TestSaveLicenseData(CliTestCase):
    def test_save_license_data(self):
        with tempfile.NamedTemporaryFile() as f:
            license_text = 'test license text'
            license.save_license_data(license_text, f.name)

            with open(f.name, 'r') as d:
                self.assertEqual([license_text], d.readlines())


class TestPostLicense(CliTestCase):
    auth = ('username', 'password')
    server_verification_file = 'test_server_verification_file'

    args = {
        'dcos_mode': False,
        'scheme': 'https',
        'host': '10.0.0.1',
        'port': '9005',
        'base_path': '/',
        'api_version': '2',
        'conductr_auth': auth,
        'server_verification_file': server_verification_file
    }

    def test_success(self):
        license_file = MagicMock()

        mock_license_file_content = MagicMock()
        mock_open = MagicMock(return_value=mock_license_file_content)

        mock_post = self.respond_with(status_code=200)

        input_args = MagicMock(**self.args)

        with patch('builtins.open', mock_open), \
                patch('conductr_cli.conduct_request.post', mock_post):
            self.assertTrue(license.post_license(input_args, license_file))

        mock_open.assert_called_once_with(license_file, 'rb')
        mock_post.assert_called_once_with(False, '10.0.0.1', 'https://10.0.0.1:9005/v2/license',
                                          auth=self.auth,
                                          data=mock_license_file_content,
                                          verify=self.server_verification_file)

    def test_http_error(self):
        license_file = MagicMock()

        mock_license_file_content = MagicMock()
        mock_open = MagicMock(return_value=mock_license_file_content)

        mock_post = self.respond_with(status_code=500)

        input_args = MagicMock(**self.args)

        with patch('builtins.open', mock_open), \
                patch('conductr_cli.conduct_request.post', mock_post):
            self.assertRaises(HTTPError, license.post_license, input_args, license_file)

        mock_open.assert_called_once_with(license_file, 'rb')
        mock_post.assert_called_once_with(False, '10.0.0.1', 'https://10.0.0.1:9005/v2/license',
                                          auth=self.auth,
                                          data=mock_license_file_content,
                                          verify=self.server_verification_file)

    def test_endpoint_not_supported(self):
        license_file = MagicMock()

        mock_license_file_content = MagicMock()
        mock_open = MagicMock(return_value=mock_license_file_content)

        mock_post = self.respond_with(status_code=503)

        input_args = MagicMock(**self.args)

        with patch('builtins.open', mock_open), \
                patch('conductr_cli.conduct_request.post', mock_post):
            self.assertFalse(license.post_license(input_args, license_file))

        mock_open.assert_called_once_with(license_file, 'rb')
        mock_post.assert_called_once_with(False, '10.0.0.1', 'https://10.0.0.1:9005/v2/license',
                                          auth=self.auth,
                                          data=mock_license_file_content,
                                          verify=self.server_verification_file)


class TestGetLicense(CliTestCase):
    auth = ('username', 'password')
    server_verification_file = 'test_server_verification_file'

    args = {
        'dcos_mode': False,
        'scheme': 'https',
        'host': '10.0.0.1',
        'port': '9005',
        'base_path': '/',
        'api_version': '2',
        'conductr_auth': auth,
        'server_verification_file': server_verification_file
    }

    license = {
        'user': 'cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend',
        'maxConductrAgents': 3,
        'conductrVersions': ['2.1.*'],
        'expires': '2018-03-01T00:00:00Z',
        'grants': ['akka-sbr', 'cinnamon', 'conductr'],
    }

    license_json_text = json.dumps(license)

    def test_license_found(self):
        mock_get = self.respond_with(status_code=200, text=self.license_json_text)

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.conduct_request.get', mock_get):
            is_license_success, license_result = license.get_license(input_args)
            self.assertTrue(is_license_success)
            self.assertEqual(self.license, license_result)

        mock_get.assert_called_once_with(False, '10.0.0.1', 'https://10.0.0.1:9005/v2/license', auth=self.auth)

    def test_license_not_found(self):
        mock_get = self.respond_with(status_code=404)

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.conduct_request.get', mock_get):
            is_license_success, license_result = license.get_license(input_args)
            self.assertFalse(is_license_success)
            self.assertIsNone(license_result)

        mock_get.assert_called_once_with(False, '10.0.0.1', 'https://10.0.0.1:9005/v2/license', auth=self.auth)

    def test_http_error(self):
        mock_get = self.respond_with(status_code=500)

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.conduct_request.get', mock_get):
            self.assertRaises(HTTPError, license.get_license, input_args)

        mock_get.assert_called_once_with(False, '10.0.0.1', 'https://10.0.0.1:9005/v2/license', auth=self.auth)

    def test_endpoint_not_supported(self):
        mock_get = self.respond_with(status_code=503)

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.conduct_request.get', mock_get):
            is_license_success, license_result = license.get_license(input_args)
            self.assertFalse(is_license_success)
            self.assertIsNone(license_result)

        mock_get.assert_called_once_with(False, '10.0.0.1', 'https://10.0.0.1:9005/v2/license', auth=self.auth)

    def test_dcos_error_license_not_found(self):
        mock_response = MagicMock(**{
            'status_code': 404,
            'url': 'dummy',
            'reason': 'test',
        })
        mock_get = MagicMock(side_effect=DCOSHTTPException(mock_response))

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.conduct_request.get', mock_get):
            is_license_success, license_result = license.get_license(input_args)
            self.assertFalse(is_license_success)
            self.assertIsNone(license_result)

        mock_get.assert_called_once_with(False, '10.0.0.1', 'https://10.0.0.1:9005/v2/license', auth=self.auth)

    def test_dcos_error_endpoint_not_supported(self):
        mock_response = MagicMock(**{
            'status_code': 503,
            'url': 'dummy',
            'reason': 'test',
        })
        mock_get = MagicMock(side_effect=DCOSHTTPException(mock_response))

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.conduct_request.get', mock_get):
            is_license_success, license_result = license.get_license(input_args)
            self.assertFalse(is_license_success)
            self.assertIsNone(license_result)

        mock_get.assert_called_once_with(False, '10.0.0.1', 'https://10.0.0.1:9005/v2/license', auth=self.auth)

    def test_dcos_error(self):
        mock_response = MagicMock(**{
            'status_code': 500,
            'url': 'dummy',
            'reason': 'test',
        })
        mock_get = MagicMock(side_effect=DCOSHTTPException(mock_response))

        input_args = MagicMock(**self.args)

        with patch('conductr_cli.conduct_request.get', mock_get):
            self.assertRaises(DCOSHTTPException, license.get_license, input_args)

        mock_get.assert_called_once_with(False, '10.0.0.1', 'https://10.0.0.1:9005/v2/license', auth=self.auth)


class TestFormatLicense(TestCase):
    license = {
        'user': 'cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend',
        'maxConductrAgents': 3,
        'conductrVersions': ['2.1.*', '2.2.*'],
        'expires': '2018-03-01T00:00:00Z',
        'grants': ['akka-sbr', 'cinnamon', 'conductr'],
    }

    formatted_expiry = 'formatted_expiry'

    def test_all_fields_present(self):
        mock_format_expiry = MagicMock(return_value=self.formatted_expiry)

        with patch('conductr_cli.license.format_expiry', mock_format_expiry):
            result = license.format_license(self.license)

            expected_result = strip_margin("""|Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                                              |Max ConductR agents: 3
                                              |Expires In: {}
                                              |ConductR Version(s): 2.1.*, 2.2.*
                                              |Grants: akka-sbr, cinnamon, conductr""".format(self.formatted_expiry))
            self.assertEqual(expected_result, result)

        mock_format_expiry.assert_called_once_with(self.license['expires'])

    def test_not_present_expiry(self):
        mock_format_expiry = MagicMock(return_value=self.formatted_expiry)

        license_no_expiry = self.license.copy()
        del license_no_expiry['expires']

        with patch('conductr_cli.license.format_expiry', mock_format_expiry):
            result = license.format_license(license_no_expiry)

            expected_result = strip_margin("""|Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                                              |Max ConductR agents: 3
                                              |ConductR Version(s): 2.1.*, 2.2.*
                                              |Grants: akka-sbr, cinnamon, conductr""")
            self.assertEqual(expected_result, result)

        mock_format_expiry.assert_not_called()

    def test_not_present_versions(self):
        mock_format_expiry = MagicMock(return_value=self.formatted_expiry)

        license_no_versions = self.license.copy()
        del license_no_versions['conductrVersions']

        with patch('conductr_cli.license.format_expiry', mock_format_expiry):
            result = license.format_license(license_no_versions)

            expected_result = strip_margin("""|Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                                              |Max ConductR agents: 3
                                              |Expires In: {}
                                              |Grants: akka-sbr, cinnamon, conductr""".format(self.formatted_expiry))
            self.assertEqual(expected_result, result)

        mock_format_expiry.assert_called_once_with(self.license['expires'])

    def test_not_present_grants(self):
        mock_format_expiry = MagicMock(return_value=self.formatted_expiry)

        license_no_grants = self.license.copy()
        del license_no_grants['grants']

        with patch('conductr_cli.license.format_expiry', mock_format_expiry):
            result = license.format_license(license_no_grants)

            expected_result = strip_margin("""|Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                                              |Max ConductR agents: 3
                                              |Expires In: {}
                                              |ConductR Version(s): 2.1.*, 2.2.*""".format(self.formatted_expiry))
            self.assertEqual(expected_result, result)

        mock_format_expiry.assert_called_once_with(self.license['expires'])


class TestFormatExpiry(TestCase):
    date_now = datetime.datetime(2018, 12, 1, 0, 0, 0, 0)
    next_year = datetime.datetime(2019, 12, 1, 0, 0, 0, 0)
    last_year = datetime.datetime(2017, 12, 1, 0, 0, 0, 0)

    def test_valid(self):
        mock_current_date = MagicMock(return_value=self.date_now)

        with patch('conductr_cli.license.current_date', mock_current_date):
            # License expires in 1 year
            expiry_date = self.next_year
            result = license.format_expiry(expiry_date=expiry_date.strftime('%Y-%m-%dT%H:%M:%SZ'))

            expected_expiry_date_display = arrow.get(expiry_date).to('local').strftime(EXPIRY_DATE_DISPLAY_FORMAT)
            expected_result = '365 days ({})'.format(expected_expiry_date_display)
            self.assertEqual(expected_result, result)

    def test_expiring_today(self):
        mock_current_date = MagicMock(return_value=self.date_now)

        with patch('conductr_cli.license.current_date', mock_current_date):
            # License expires today
            expiry_date = self.date_now
            result = license.format_expiry(expiry_date=expiry_date.strftime('%Y-%m-%dT%H:%M:%SZ'))

            expected_expiry_date_display = arrow.get(expiry_date).to('local').strftime(EXPIRY_DATE_DISPLAY_FORMAT)
            expected_result = 'Today ({})'.format(expected_expiry_date_display)
            self.assertEqual(expected_result, result)

    def test_expired(self):
        mock_current_date = MagicMock(return_value=self.date_now)

        with patch('conductr_cli.license.current_date', mock_current_date):
            # License expired last year
            expiry_date = self.last_year
            result = license.format_expiry(expiry_date=expiry_date.strftime('%Y-%m-%dT%H:%M:%SZ'))

            expected_expiry_date_display = arrow.get(expiry_date).to('local').strftime(EXPIRY_DATE_DISPLAY_FORMAT)
            expected_result = 'Expired ({})'.format(expected_expiry_date_display)
            self.assertEqual(expected_result, result)
