from conductr_cli.test.cli_test_case import CliTestCase, strip_margin, as_error
from conductr_cli import conduct_load_license, logging_setup
from conductr_cli.constants import DEFAULT_LICENSE_FILE
from conductr_cli.exceptions import LicenseDownloadError
from unittest.mock import patch, MagicMock, call
from requests.exceptions import ConnectionError, HTTPError
from dcos.errors import DCOSHTTPException


class TestConductLoadLicense(CliTestCase):
    host = '10.0.0.1'

    args = {
        'offline_mode': False,
        'host': host,
        'force_flag_enabled': False,
    }

    license = {
        'user': 'cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend',
        'maxConductrAgents': 3,
        'conductrVersions': ['2.1.*'],
        'expires': '2018-03-01T00:00:00Z',
        'grants': ['akka-sbr', 'cinnamon', 'conductr'],
    }

    license_formatted = 'test-only'

    http_failure_response = {
        'status_code': 500,
        'reason': 'test',
        'text': 'test'
    }

    def test_success(self):
        mock_download_license = MagicMock()
        mock_exists = MagicMock(return_value=True)
        mock_post_license = MagicMock(return_value=True)
        mock_get_license = MagicMock(return_value=(True, self.license))
        mock_format_license = MagicMock(return_value=self.license_formatted)

        input_args = MagicMock(**self.args)

        stdout = MagicMock()

        with patch('conductr_cli.license.download_license', mock_download_license), \
                patch('os.path.exists', mock_exists), \
                patch('conductr_cli.license.post_license', mock_post_license), \
                patch('conductr_cli.license.get_license', mock_get_license), \
                patch('conductr_cli.license.format_license', mock_format_license):
            logging_setup.configure_logging(input_args, stdout)
            self.assertTrue(conduct_load_license.load_license(input_args))

        mock_download_license.assert_called_once_with(input_args,
                                                      save_to=DEFAULT_LICENSE_FILE,
                                                      use_cached_auth_token=True)
        mock_exists.assert_called_once_with(DEFAULT_LICENSE_FILE)
        mock_post_license.assert_called_once_with(input_args, DEFAULT_LICENSE_FILE)
        mock_get_license.assert_has_calls([call(input_args), call(input_args)])
        mock_format_license.assert_called_once_with(self.license)

        expected_output = strip_margin("""|Loading license into ConductR at {}
                                          |
                                          |{}
                                          |
                                          |License successfully loaded
                                          |""".format(self.host, self.license_formatted))
        self.assertEqual(expected_output, self.output(stdout))

    def test_success_with_force_flag_enabled(self):
        mock_download_license = MagicMock()
        mock_exists = MagicMock(return_value=True)
        mock_post_license = MagicMock(return_value=True)
        mock_get_license = MagicMock(return_value=(True, self.license))
        mock_format_license = MagicMock(return_value=self.license_formatted)

        args = self.args.copy()
        args.update({'force_flag_enabled': True})
        input_args = MagicMock(**args)

        stdout = MagicMock()

        with patch('conductr_cli.license.download_license', mock_download_license), \
                patch('os.path.exists', mock_exists), \
                patch('conductr_cli.license.post_license', mock_post_license), \
                patch('conductr_cli.license.get_license', mock_get_license), \
                patch('conductr_cli.license.format_license', mock_format_license):
            logging_setup.configure_logging(input_args, stdout)
            self.assertTrue(conduct_load_license.load_license(input_args))

        mock_download_license.assert_called_once_with(input_args,
                                                      save_to=DEFAULT_LICENSE_FILE,
                                                      use_cached_auth_token=False)
        mock_exists.assert_called_once_with(DEFAULT_LICENSE_FILE)
        mock_post_license.assert_called_once_with(input_args, DEFAULT_LICENSE_FILE)
        mock_get_license.assert_has_calls([call(input_args), call(input_args)])
        mock_format_license.assert_called_once_with(self.license)

        expected_output = strip_margin("""|Loading license into ConductR at {}
                                          |
                                          |{}
                                          |
                                          |License successfully loaded
                                          |""".format(self.host, self.license_formatted))
        self.assertEqual(expected_output, self.output(stdout))

    def test_success_by_ip(self):
        mock_download_license = MagicMock()
        mock_exists = MagicMock(return_value=True)
        mock_post_license = MagicMock(return_value=True)
        mock_get_license = MagicMock(return_value=(True, self.license))
        mock_format_license = MagicMock(return_value=self.license_formatted)

        args = {
            'offline_mode': False,
            'ip': self.host,
            'force_flag_enabled': False
        }

        input_args = MagicMock(**args)

        stdout = MagicMock()

        with patch('conductr_cli.license.download_license', mock_download_license), \
                patch('os.path.exists', mock_exists), \
                patch('conductr_cli.license.post_license', mock_post_license), \
                patch('conductr_cli.license.get_license', mock_get_license), \
                patch('conductr_cli.license.format_license', mock_format_license):
            logging_setup.configure_logging(input_args, stdout)
            self.assertTrue(conduct_load_license.load_license(input_args))

        mock_download_license.assert_called_once_with(input_args,
                                                      save_to=DEFAULT_LICENSE_FILE,
                                                      use_cached_auth_token=True)
        mock_exists.assert_called_once_with(DEFAULT_LICENSE_FILE)
        mock_post_license.assert_called_once_with(input_args, DEFAULT_LICENSE_FILE)
        mock_get_license.assert_has_calls([call(input_args), call(input_args)])
        mock_format_license.assert_called_once_with(self.license)

        expected_output = strip_margin("""|Loading license into ConductR at {}
                                          |
                                          |{}
                                          |
                                          |License successfully loaded
                                          |""".format(self.host, self.license_formatted))
        self.assertEqual(expected_output, self.output(stdout))

    def test_offline_mode(self):
        mock_download_license = MagicMock()
        mock_exists = MagicMock(return_value=True)
        mock_post_license = MagicMock(return_value=True)
        mock_get_license = MagicMock(return_value=(True, self.license))
        mock_format_license = MagicMock(return_value=self.license_formatted)

        args = self.args.copy()
        args.pop('offline_mode', True)
        input_args = MagicMock(**args)

        stdout = MagicMock()

        with patch('conductr_cli.license.download_license', mock_download_license), \
                patch('os.path.exists', mock_exists), \
                patch('conductr_cli.license.post_license', mock_post_license), \
                patch('conductr_cli.license.get_license', mock_get_license), \
                patch('conductr_cli.license.format_license', mock_format_license):
            logging_setup.configure_logging(input_args, stdout)
            self.assertTrue(conduct_load_license.load_license(input_args))

        mock_download_license.assert_not_called()
        mock_exists.assert_called_once_with(DEFAULT_LICENSE_FILE)
        mock_post_license.assert_called_once_with(input_args, DEFAULT_LICENSE_FILE)
        mock_get_license.assert_has_calls([call(input_args), call(input_args)])
        mock_format_license.assert_called_once_with(self.license)

        expected_output = strip_margin("""|Skipping downloading license from Lightbend.com
                                          |Loading license into ConductR at {}
                                          |
                                          |{}
                                          |
                                          |License successfully loaded
                                          |""".format(self.host, self.license_formatted))
        self.assertEqual(expected_output, self.output(stdout))

    def test_download_license_error(self):
        mock_download_license = MagicMock(side_effect=LicenseDownloadError(['test']))
        mock_exists = MagicMock(return_value=True)
        mock_post_license = MagicMock(return_value=True)
        mock_get_license = MagicMock(return_value=(True, self.license))
        mock_format_license = MagicMock(return_value=self.license_formatted)

        input_args = MagicMock(**self.args)

        stdout = MagicMock()
        stderr = MagicMock()

        with patch('conductr_cli.license.download_license', mock_download_license), \
                patch('os.path.exists', mock_exists), \
                patch('conductr_cli.license.post_license', mock_post_license), \
                patch('conductr_cli.license.get_license', mock_get_license), \
                patch('conductr_cli.license.format_license', mock_format_license):
            logging_setup.configure_logging(input_args, stdout, stderr)
            self.assertFalse(conduct_load_license.load_license(input_args))

        mock_download_license.assert_called_once_with(input_args,
                                                      save_to=DEFAULT_LICENSE_FILE,
                                                      use_cached_auth_token=True)
        mock_exists.assert_not_called()
        mock_post_license.assert_not_called()
        mock_get_license.assert_called_once_with(input_args)
        mock_format_license.assert_not_called()

        self.assertEqual('', self.output(stdout))
        expected_output = strip_margin("""|Error: test
                                          |Error: Use `conduct load-license -f` to re-download your license.
                                          |""")
        self.assertEqual(as_error(expected_output), self.output(stderr))

    def test_offline_mode_license_file_missing(self):
        mock_download_license = MagicMock()
        mock_exists = MagicMock(return_value=False)
        mock_post_license = MagicMock(return_value=True)
        mock_get_license = MagicMock(return_value=(True, self.license))
        mock_format_license = MagicMock(return_value=self.license_formatted)

        args = self.args.copy()
        args.pop('offline_mode', True)
        input_args = MagicMock(**args)

        stdout = MagicMock()
        stderr = MagicMock()

        with patch('conductr_cli.license.download_license', mock_download_license), \
                patch('os.path.exists', mock_exists), \
                patch('conductr_cli.license.post_license', mock_post_license), \
                patch('conductr_cli.license.get_license', mock_get_license), \
                patch('conductr_cli.license.format_license', mock_format_license):
            logging_setup.configure_logging(input_args, stdout, stderr)
            self.assertFalse(conduct_load_license.load_license(input_args))

        mock_download_license.assert_not_called()
        mock_exists.assert_called_once_with(DEFAULT_LICENSE_FILE)
        mock_post_license.assert_not_called()
        mock_get_license.assert_called_once_with(input_args)
        mock_format_license.assert_not_called()

        expected_output = strip_margin("""|Skipping downloading license from Lightbend.com
                                          |""".format(self.host, self.license_formatted))
        self.assertEqual(expected_output, self.output(stdout))

        expected_error = as_error(strip_margin("""|Error: Error loading license into ConductR
                                                  |Error: Please ensure the license file exists at {}
                                                  |Error: Use `conduct load-license -f` to re-download your license.
                                                  |""".format(DEFAULT_LICENSE_FILE)))
        self.assertEqual(expected_error, self.output(stderr))

    def test_license_not_found_in_conductr(self):
        mock_download_license = MagicMock()
        mock_exists = MagicMock(return_value=True)
        mock_post_license = MagicMock(return_value=True)
        mock_get_license = MagicMock(return_value=(True, None))
        mock_format_license = MagicMock()

        input_args = MagicMock(**self.args)

        stdout = MagicMock()
        stderr = MagicMock()

        with patch('conductr_cli.license.download_license', mock_download_license), \
                patch('os.path.exists', mock_exists), \
                patch('conductr_cli.license.post_license', mock_post_license), \
                patch('conductr_cli.license.get_license', mock_get_license), \
                patch('conductr_cli.license.format_license', mock_format_license):
            logging_setup.configure_logging(input_args, stdout, stderr)
            self.assertFalse(conduct_load_license.load_license(input_args))

        mock_download_license.assert_called_once_with(input_args,
                                                      save_to=DEFAULT_LICENSE_FILE,
                                                      use_cached_auth_token=True)
        mock_exists.assert_called_once_with(DEFAULT_LICENSE_FILE)
        mock_post_license.assert_called_once_with(input_args, DEFAULT_LICENSE_FILE)
        mock_get_license.assert_has_calls([call(input_args), call(input_args)])
        mock_format_license.assert_not_called()

        expected_output = strip_margin("""|Loading license into ConductR at {}
                                          |""".format(self.host, self.license_formatted))
        self.assertEqual(expected_output, self.output(stdout))

        expected_error = as_error(strip_margin("""|Error: Error loading license into ConductR
                                                  |Error: Unable to find recently loaded license
                                                  |Error: Use `conduct load-license -f` to re-download your license.
                                                  |""".format(self.host, self.license_formatted)))
        self.assertEqual(expected_error, self.output(stderr))

    def test_http_error(self):
        mock_download_license = MagicMock()
        mock_exists = MagicMock(return_value=True)
        mock_post_license = MagicMock(side_effect=HTTPError('test', response=MagicMock(**self.http_failure_response)))
        mock_get_license = MagicMock()
        mock_format_license = MagicMock()

        input_args = MagicMock(**self.args)

        stdout = MagicMock()
        stderr = MagicMock()

        with patch('conductr_cli.license.download_license', mock_download_license), \
                patch('os.path.exists', mock_exists), \
                patch('conductr_cli.license.post_license', mock_post_license), \
                patch('conductr_cli.license.get_license', mock_get_license), \
                patch('conductr_cli.license.format_license', mock_format_license):
            logging_setup.configure_logging(input_args, stdout, stderr)
            self.assertFalse(conduct_load_license.load_license(input_args))

        mock_download_license.assert_called_once_with(input_args,
                                                      save_to=DEFAULT_LICENSE_FILE,
                                                      use_cached_auth_token=True)
        mock_exists.assert_called_once_with(DEFAULT_LICENSE_FILE)
        mock_post_license.assert_called_once_with(input_args, DEFAULT_LICENSE_FILE)
        mock_get_license.assert_called_once_with(input_args)
        mock_format_license.assert_not_called()

    def test_dcos_http_error(self):
        mock_download_license = MagicMock()
        mock_exists = MagicMock(return_value=True)
        mock_post_license = MagicMock(side_effect=DCOSHTTPException(MagicMock(**self.http_failure_response)))
        mock_get_license = MagicMock()
        mock_format_license = MagicMock()

        input_args = MagicMock(**self.args)

        stdout = MagicMock()
        stderr = MagicMock()

        with patch('conductr_cli.license.download_license', mock_download_license), \
                patch('os.path.exists', mock_exists), \
                patch('conductr_cli.license.post_license', mock_post_license), \
                patch('conductr_cli.license.get_license', mock_get_license), \
                patch('conductr_cli.license.format_license', mock_format_license):
            logging_setup.configure_logging(input_args, stdout, stderr)
            self.assertFalse(conduct_load_license.load_license(input_args))

        mock_download_license.assert_called_once_with(input_args,
                                                      save_to=DEFAULT_LICENSE_FILE,
                                                      use_cached_auth_token=True)
        mock_exists.assert_called_once_with(DEFAULT_LICENSE_FILE)
        mock_post_license.assert_called_once_with(input_args, DEFAULT_LICENSE_FILE)
        mock_get_license.assert_called_once_with(input_args)
        mock_format_license.assert_not_called()

    def test_connection_error(self):
        mock_download_license = MagicMock()
        mock_exists = MagicMock(return_value=True)
        mock_post_license = MagicMock(side_effect=ConnectionError('test'))
        mock_get_license = MagicMock()
        mock_format_license = MagicMock()

        input_args = MagicMock(**self.args)

        stdout = MagicMock()
        stderr = MagicMock()

        with patch('conductr_cli.license.download_license', mock_download_license), \
                patch('os.path.exists', mock_exists), \
                patch('conductr_cli.license.post_license', mock_post_license), \
                patch('conductr_cli.license.get_license', mock_get_license), \
                patch('conductr_cli.license.format_license', mock_format_license):
            logging_setup.configure_logging(input_args, stdout, stderr)
            self.assertFalse(conduct_load_license.load_license(input_args))

        mock_download_license.assert_called_once_with(input_args,
                                                      save_to=DEFAULT_LICENSE_FILE,
                                                      use_cached_auth_token=True)
        mock_exists.assert_called_once_with(DEFAULT_LICENSE_FILE)
        mock_post_license.assert_called_once_with(input_args, DEFAULT_LICENSE_FILE)
        mock_get_license.assert_called_once_with(input_args)
        mock_format_license.assert_not_called()

    def test_license_download_error(self):
        mock_download_license = MagicMock(side_effect=LicenseDownloadError('test'))
        mock_exists = MagicMock(return_value=True)
        mock_post_license = MagicMock()
        mock_get_license = MagicMock(return_value=(True, None))
        mock_format_license = MagicMock()

        input_args = MagicMock(**self.args)

        stdout = MagicMock()
        stderr = MagicMock()

        with patch('conductr_cli.license.download_license', mock_download_license), \
                patch('os.path.exists', mock_exists), \
                patch('conductr_cli.license.post_license', mock_post_license), \
                patch('conductr_cli.license.get_license', mock_get_license), \
                patch('conductr_cli.license.format_license', mock_format_license):
            logging_setup.configure_logging(input_args, stdout, stderr)
            self.assertFalse(conduct_load_license.load_license(input_args))

        mock_download_license.assert_called_once_with(input_args,
                                                      save_to=DEFAULT_LICENSE_FILE,
                                                      use_cached_auth_token=True)
        mock_exists.assert_not_called()
        mock_post_license.assert_not_called()
        mock_get_license.assert_called_once_with(input_args)
        mock_format_license.assert_not_called()
