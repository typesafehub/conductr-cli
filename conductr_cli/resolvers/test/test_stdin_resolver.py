from conductr_cli.resolver import stdin_resolver
from conductr_cli.resolvers.schemes import SCHEME_STDIN
from unittest import TestCase
from unittest.mock import patch, MagicMock
import tempfile


class TestResolverStdIn(TestCase):
    def test_resolve_bundle_tty_in(self):
        with patch('sys.stdin.isatty', lambda: True):
            self.assertEqual(
                stdin_resolver.resolve_bundle('/some/cache/dir', None, None),
                (False, None, None, None)
            )

    def test_resolve_bundle_not_used_for_given_file(self):
        with patch('sys.stdin.isatty', lambda: False):
            self.assertEqual(
                stdin_resolver.resolve_bundle('/some/cache/dir', 'somefile.zip', None),
                (False, None, None, None)
            )

    def test_resolve_bundle_file_in(self):
        read_mock = MagicMock(side_effect=[b'hello', b''])

        file = tempfile.NamedTemporaryFile()

        with patch('sys.stdin.isatty', lambda: False), \
                patch('sys.stdin.buffer.read', read_mock), \
                patch('tempfile.NamedTemporaryFile', MagicMock(return_value=file)):
            self.assertEqual(
                stdin_resolver.resolve_bundle('/some/cache/dir', '-', None),
                (True, None, file.name, None)
            )

            file.seek(0)

            self.assertEqual(file.read(), b'hello')

    def test_load_bundle_from_cache(self):
        mock_cache_dir = MagicMock()
        mock_uri = MagicMock()

        self.assertEqual(stdin_resolver.load_bundle_from_cache(mock_cache_dir, mock_uri),
                         (False, None, None, None))

    def test_resolve_bundle_configuration(self):
        mock_cache_dir = MagicMock()
        mock_uri = MagicMock()
        mock_auth = MagicMock()

        self.assertEqual(stdin_resolver.resolve_bundle_configuration(mock_cache_dir, mock_uri, mock_auth),
                         (False, None, None, None))

    def test_load_bundle_configuration_from_cache(self):
        mock_cache_dir = MagicMock()
        mock_uri = MagicMock()

        self.assertEqual(stdin_resolver.load_bundle_configuration_from_cache(mock_cache_dir, mock_uri),
                         (False, None, None, None))

    def test_resolve_bundle_version(self):
        mock_uri = MagicMock()

        self.assertEqual(stdin_resolver.resolve_bundle_version(mock_uri),
                         (None, None))

    def test_continuous_delivery_uri(self):
        mock_resolved_version = MagicMock()

        self.assertIsNone(stdin_resolver.continuous_delivery_uri(mock_resolved_version))

    def test_is_bundle_name(self):
        self.assertTrue(stdin_resolver.is_bundle_name('visualizer'))
        self.assertFalse(stdin_resolver.is_bundle_name('/tmp/foo.zip'))


class TestSupportedSchemes(TestCase):
    def test_supported_schemes(self):
        self.assertEqual([SCHEME_STDIN], stdin_resolver.supported_schemes())
