from conductr_cli import license_auth
from conductr_cli.constants import DEFAULT_AUTH_TOKEN_FILE
from unittest import TestCase
from unittest.mock import patch, MagicMock
import io
import tempfile


class TestGetCachedAuthToken(TestCase):
    def test_cached_token_exists(self):
        mock_exists = MagicMock(return_value=True)
        cached_token = 'test cached token'
        mock_open = MagicMock(return_value=io.StringIO(cached_token))

        with patch('os.path.exists', mock_exists), \
                patch('builtins.open', mock_open):
            license_auth.get_cached_auth_token()

        mock_exists.assert_called_once_with(DEFAULT_AUTH_TOKEN_FILE)
        mock_open.assert_called_once_with(DEFAULT_AUTH_TOKEN_FILE, 'r', encoding="utf-8")

    def test_cached_token_missing(self):
        mock_exists = MagicMock(return_value=False)
        mock_open = MagicMock()

        with patch('os.path.exists', mock_exists), \
                patch('builtins.open', mock_open):
            license_auth.get_cached_auth_token()

        mock_exists.assert_called_once_with(DEFAULT_AUTH_TOKEN_FILE)
        mock_open.assert_not_called()


class TestPromptForAuthToken(TestCase):
    def test_prompt_for_auth_token(self):
        auth_token = 'test auth token'

        mock_print = MagicMock()
        mock_input = MagicMock(return_value=auth_token)

        with patch('builtins.print', mock_print), \
                patch('builtins.input', mock_input), \
                patch('sys.stdin.isatty', lambda: True):
            self.assertEqual(auth_token, license_auth.prompt_for_auth_token())

        mock_input.assert_called_once_with(license_auth.AUTH_TOKEN_PROMPT)

    def test_no_tty_dont_prompt_for_auth_token(self):
        auth_token = 'test auth token'

        mock_print = MagicMock()
        mock_input = MagicMock(return_value=auth_token)

        with patch('builtins.print', mock_print), \
                patch('builtins.input', mock_input), \
                patch('sys.stdin.isatty', lambda: False):
            self.assertEqual(auth_token, license_auth.prompt_for_auth_token())

        mock_input.assert_called_once_with()


class TestRemoveCachedAuthToken(TestCase):
    def test_cached_token_exists(self):
        mock_exists = MagicMock(return_value=True)
        mock_remove = MagicMock()

        with patch('os.path.exists', mock_exists), \
                patch('os.remove', mock_remove):
            license_auth.remove_cached_auth_token()

        mock_exists.assert_called_once_with(DEFAULT_AUTH_TOKEN_FILE)
        mock_remove.assert_called_once_with(DEFAULT_AUTH_TOKEN_FILE)

    def test_cached_token_missing(self):
        mock_exists = MagicMock(return_value=False)
        mock_remove = MagicMock()

        with patch('os.path.exists', mock_exists), \
                patch('os.remove', mock_remove):
            license_auth.remove_cached_auth_token()

        mock_exists.assert_called_once_with(DEFAULT_AUTH_TOKEN_FILE)
        mock_remove.assert_not_called()


class TestSaveAuthToken(TestCase):
    def test_save_auth_token(self):
        with tempfile.NamedTemporaryFile() as f:
            auth_token = 'test auth token'

            open_temp_file = open(f.name, 'w')
            mock_open = MagicMock(return_value=open_temp_file)

            with patch('builtins.open', mock_open):
                license_auth.save_auth_token(auth_token)

            mock_open.assert_called_once_with(DEFAULT_AUTH_TOKEN_FILE, 'w', encoding="utf-8")

            with open(f.name, 'r') as d:
                self.assertEqual([auth_token], d.readlines())
