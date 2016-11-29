from unittest import TestCase
from conductr_cli.test.cli_test_case import strip_margin
from conductr_cli import custom_settings
from pyhocon import ConfigFactory

try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestCustomSettingsLoadCredentials(TestCase):
    def test_return_credentials(self):
        load_from_file_mock = MagicMock(return_value=self.custom_settings('uid', 'pwd'))
        input_args = MagicMock(**{
            'dcos_mode': False
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_conductr_credentials(input_args)

        load_from_file_mock.assert_called_with(input_args)

        self.assertEqual(('uid', 'pwd'), result)

    def test_return_none_if_username_is_none(self):
        load_from_file_mock = MagicMock(return_value=self.custom_settings(None, 'pwd'))
        input_args = MagicMock(**{
            'dcos_mode': False
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_conductr_credentials(input_args)

        load_from_file_mock.assert_called_with(input_args)

        self.assertIsNone(result)

    def test_return_none_if_password_is_none(self):
        load_from_file_mock = MagicMock(return_value=self.custom_settings('uid', None))
        input_args = MagicMock(**{
            'dcos_mode': False
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_conductr_credentials(input_args)

        load_from_file_mock.assert_called_with(input_args)

        self.assertIsNone(result)

    def test_return_none_if_username_and_password_is_none(self):
        load_from_file_mock = MagicMock(return_value=self.custom_settings(None, None))
        input_args = MagicMock(**{
            'dcos_mode': False
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_conductr_credentials(input_args)

        load_from_file_mock.assert_called_with(input_args)

        self.assertIsNone(result)

    def test_return_none_if_auth_disabled(self):
        load_from_file_mock = MagicMock(return_value=self.custom_settings('uid', 'pwd', auth_enabled=False))
        input_args = MagicMock(**{
            'dcos_mode': False
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_conductr_credentials(input_args)

        load_from_file_mock.assert_called_with(input_args)

        self.assertIsNone(result)

    def test_return_none_if_auth_enabled_settings_not_defined(self):
        load_from_file_mock = MagicMock(return_value=self.custom_settings('uid', 'pwd', auth_enabled=None))
        input_args = MagicMock(**{
            'dcos_mode': False
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_conductr_credentials(input_args)

        load_from_file_mock.assert_called_with(input_args)

        self.assertIsNone(result)

    def test_return_none_if_custom_settings_not_defined(self):
        load_from_file_mock = MagicMock(return_value=None)
        input_args = MagicMock(**{
            'dcos_mode': False
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_conductr_credentials(input_args)

        load_from_file_mock.assert_called_with(input_args)

        self.assertIsNone(result)

    def test_return_none_if_dcos_mode(self):
        load_from_file_mock = MagicMock(return_value=self.custom_settings('uid', 'pwd'))
        input_args = MagicMock(**{
            'dcos_mode': True
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_conductr_credentials(input_args)

        load_from_file_mock.assert_not_called()

        self.assertIsNone(result)

    def custom_settings(self, username, password, auth_enabled=True):
        if username and password and auth_enabled is None:
            config = strip_margin("""|conductr.auth.username = {}
                                     |conductr.auth.password = {}
                                     |""".format(username, password))
        elif username and password:
            config = strip_margin("""|conductr.auth.enabled = {}
                                     |conductr.auth.username = {}
                                     |conductr.auth.password = {}
                                     |""".format(auth_enabled, username, password))
        elif username:
            config = strip_margin("""|conductr.auth.enabled = {}
                                     |conductr.auth.username = {}
                                     |""".format(auth_enabled, username))
        elif password:
            config = strip_margin("""|conductr.auth.enabled = {}
                                     |conductr.auth.password = {}
                                     |""".format(auth_enabled, password))
        else:
            config = strip_margin("""|some.other.config = some-value
                                     |""")

        return ConfigFactory.parse_string(config)


class TestCustomSettingsLoadServerSSLVerificationFile(TestCase):
    def test_return_file(self):
        load_from_file_mock = MagicMock(return_value=self.custom_settings('test.pem'))
        input_args = MagicMock(**{
            'dcos_mode': False
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_server_ssl_verification_file(input_args)

        load_from_file_mock.assert_called_with(input_args)

        self.assertEqual('test.pem', result)

    def test_return_none_if_server_verification_file_is_none(self):
        load_from_file_mock = MagicMock(return_value=self.custom_settings(None))
        input_args = MagicMock(**{
            'dcos_mode': False
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_server_ssl_verification_file(input_args)

        load_from_file_mock.assert_called_with(input_args)

        self.assertIsNone(result)

    def test_return_none_if_custom_settings_not_defined(self):
        load_from_file_mock = MagicMock(return_value=None)
        input_args = MagicMock(**{
            'dcos_mode': False
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_server_ssl_verification_file(input_args)

        load_from_file_mock.assert_called_with(input_args)

        self.assertIsNone(result)

    def test_return_none_if_dcos_mode(self):
        load_from_file_mock = MagicMock(return_value=self.custom_settings('test.pem'))
        input_args = MagicMock(**{
            'dcos_mode': True
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_server_ssl_verification_file(input_args)

        load_from_file_mock.assert_not_called()

        self.assertIsNone(result)

    def custom_settings(self, file):
        if file:
            config = strip_margin("""|conductr.server_ssl_verification_file = {}
                                     |""".format(file))
        else:
            config = strip_margin("""|some.other.config = some-value
                                     |""")

        return ConfigFactory.parse_string(config)
