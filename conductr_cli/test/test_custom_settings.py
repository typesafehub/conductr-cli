from unittest import TestCase
from unittest.mock import patch, MagicMock
from conductr_cli.test.cli_test_case import strip_margin
from conductr_cli import custom_settings
from pyhocon import ConfigFactory


class TestCustomSettingsLoadCredentials(TestCase):
    custom_settings = ConfigFactory.parse_string(
        strip_margin("""|conductr {
                        |  auth {
                        |    "10.0.0.1:7777" {
                        |      enabled = true
                        |      username = seven
                        |      password = seven-password
                        |    }
                        |    "10.0.0.1:7776" {
                        |      enabled = true
                        |      username = six
                        |    }
                        |    "10.0.0.1:7775" {
                        |      enabled = true
                        |      password = five-password
                        |    }
                        |    "10.0.0.1:7774" {
                        |      enabled = true
                        |    }
                        |    "10.0.0.1:7773" {
                        |      enabled = false
                        |      username = three
                        |      password = three-password
                        |    }
                        |    "10.0.0.1:7772" {
                        |      username = three
                        |      password = three-password
                        |    }
                        |    "10.0.0.1" {
                        |      enabled = true
                        |      username = one
                        |      password = one-password
                        |    }
                        |  }
                        |}
                        |""")
    )

    def test_return_credentials(self):
        load_from_file_mock = MagicMock(return_value=self.custom_settings)
        input_args = MagicMock(**{
            'host': '10.0.0.1',
            'port': 7777,
            'dcos_mode': False
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_conductr_credentials(input_args)

        load_from_file_mock.assert_called_with(input_args)

        self.assertEqual(('seven', 'seven-password'), result)

    def test_return_fallback_credentials_from_host(self):
        load_from_file_mock = MagicMock(return_value=self.custom_settings)
        input_args = MagicMock(**{
            'host': '10.0.0.1',
            'port': 9005,
            'dcos_mode': False
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_conductr_credentials(input_args)

        load_from_file_mock.assert_called_with(input_args)

        self.assertEqual(('one', 'one-password'), result)

    def test_return_none_if_username_is_none(self):
        load_from_file_mock = MagicMock(return_value=self.custom_settings)
        input_args = MagicMock(**{
            'host': '10.0.0.1',
            'port': 7775,
            'dcos_mode': False
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_conductr_credentials(input_args)

        load_from_file_mock.assert_called_with(input_args)

        self.assertIsNone(result)

    def test_return_none_if_password_is_none(self):
        load_from_file_mock = MagicMock(return_value=self.custom_settings)
        input_args = MagicMock(**{
            'host': '10.0.0.1',
            'port': 7776,
            'dcos_mode': False
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_conductr_credentials(input_args)

        load_from_file_mock.assert_called_with(input_args)

        self.assertIsNone(result)

    def test_return_none_if_username_and_password_is_none(self):
        load_from_file_mock = MagicMock(return_value=self.custom_settings)
        input_args = MagicMock(**{
            'host': '10.0.0.1',
            'port': 7774,
            'dcos_mode': False
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_conductr_credentials(input_args)

        load_from_file_mock.assert_called_with(input_args)

        self.assertIsNone(result)

    def test_return_none_if_auth_disabled(self):
        load_from_file_mock = MagicMock(return_value=self.custom_settings)
        input_args = MagicMock(**{
            'host': '10.0.0.1',
            'port': 7773,
            'dcos_mode': False
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_conductr_credentials(input_args)

        load_from_file_mock.assert_called_with(input_args)

        self.assertIsNone(result)

    def test_return_none_if_auth_enabled_settings_not_defined(self):
        load_from_file_mock = MagicMock(return_value=self.custom_settings)
        input_args = MagicMock(**{
            'host': '10.0.0.1',
            'port': 7772,
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
        load_from_file_mock = MagicMock(return_value=self.custom_settings)
        input_args = MagicMock(**{
            'dcos_mode': True
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_conductr_credentials(input_args)

        load_from_file_mock.assert_not_called()

        self.assertIsNone(result)


class TestCustomSettingsLoadServerSSLVerificationFile(TestCase):
    custom_settings = ConfigFactory.parse_string(
        strip_margin("""|conductr {
                        |  auth {
                        |    "10.0.0.1:7777" {
                        |      server_ssl_verification_file = /path/file.pem
                        |    }
                        |    "10.0.0.1:7776" {
                        |      server_ssl_verification_file = ""
                        |    }
                        |    "10.0.0.1:7775" {
                        |      enabled = true
                        |      password = five-password
                        |    }
                        |    "10.0.0.1" {
                        |      server_ssl_verification_file = /path/def.pem
                        |    }
                        |  }
                        |}
                        |""")
    )

    def test_return_file(self):
        load_from_file_mock = MagicMock(return_value=self.custom_settings)
        input_args = MagicMock(**{
            'host': '10.0.0.1',
            'port': 7777,
            'dcos_mode': False
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_server_ssl_verification_file(input_args)

        load_from_file_mock.assert_called_with(input_args)

        self.assertEqual('/path/file.pem', result)

    def test_return_fallback_file_from_host(self):
        load_from_file_mock = MagicMock(return_value=self.custom_settings)
        input_args = MagicMock(**{
            'host': '10.0.0.1',
            'port': 9005,
            'dcos_mode': False
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_server_ssl_verification_file(input_args)

        load_from_file_mock.assert_called_with(input_args)

        self.assertEqual('/path/def.pem', result)

    def test_return_none_if_server_verification_file_is_none(self):
        load_from_file_mock = MagicMock(return_value=self.custom_settings)
        input_args = MagicMock(**{
            'host': '10.0.0.1',
            'port': 7775,
            'dcos_mode': False
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_server_ssl_verification_file(input_args)

        load_from_file_mock.assert_called_with(input_args)

        self.assertIsNone(result)

    def test_return_none_if_server_verification_file_is_empty(self):
        load_from_file_mock = MagicMock(return_value=self.custom_settings)
        input_args = MagicMock(**{
            'host': '10.0.0.1',
            'port': 7776,
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
        load_from_file_mock = MagicMock(return_value=self.custom_settings)
        input_args = MagicMock(**{
            'dcos_mode': True
        })

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_server_ssl_verification_file(input_args)

        load_from_file_mock.assert_not_called()

        self.assertIsNone(result)


class TestLoadBintrayWebhookSecret(TestCase):
    def test_return_secret(self):
        test_custom_settings = ConfigFactory.parse_string(
            strip_margin("""|conductr {
                            |  continuous-delivery {
                            |    bintray-webhook-secret = secret
                            |  }
                            |}
                            |""")
        )
        load_from_file_mock = MagicMock(return_value=test_custom_settings)
        input_args = MagicMock(**{})

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_bintray_webhook_secret(input_args)

        load_from_file_mock.assert_called_with(input_args)

        self.assertEqual('secret', result)

    def test_return_none_if_custom_settings_not_defined(self):
        load_from_file_mock = MagicMock(return_value=None)
        input_args = MagicMock(**{})

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_bintray_webhook_secret(input_args)

        load_from_file_mock.assert_called_with(input_args)

        self.assertIsNone(result)

    def test_return_none_if_webhook_not_configured(self):
        test_custom_settings = ConfigFactory.parse_string(
            strip_margin("""|abc {
                            |  def = 123
                            |}""")
        )
        load_from_file_mock = MagicMock(return_value=test_custom_settings)
        input_args = MagicMock(**{})

        with patch('conductr_cli.custom_settings.load_from_file', load_from_file_mock):
            result = custom_settings.load_bintray_webhook_secret(input_args)

        load_from_file_mock.assert_called_with(input_args)

        self.assertIsNone(result)
