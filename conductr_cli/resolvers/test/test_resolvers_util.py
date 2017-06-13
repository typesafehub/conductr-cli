from unittest import TestCase
from conductr_cli import bundle_shorthand
from conductr_cli.resolvers import resolvers_util
from conductr_cli.resolvers.schemes import SCHEME_BUNDLE, SCHEME_FILE, SCHEME_HTTP, SCHEME_HTTPS, SCHEME_S3, \
    SCHEME_STDIN
from unittest.mock import patch, MagicMock
import os
import shutil
import tempfile


class TestIsLocalFile(TestCase):
    def test_is_local_file_with_file(self):
        with tempfile.NamedTemporaryFile() as temp:
            self.assertTrue(resolvers_util.is_local_file(temp.name, require_bundle_conf=True))
            self.assertTrue(resolvers_util.is_local_file(temp.name, require_bundle_conf=False))

    def test_is_local_file_with_empty_dir(self):
        temp = tempfile.mkdtemp()

        try:
            self.assertFalse(resolvers_util.is_local_file(temp, require_bundle_conf=True))
            self.assertTrue(resolvers_util.is_local_file(temp, require_bundle_conf=False))
        finally:
            shutil.rmtree(temp)

    def test_is_local_file_with_bundle_dir(self):
        temp = tempfile.mkdtemp()
        open(os.path.join(temp, 'bundle.conf'), 'w').close()

        try:
            self.assertTrue(resolvers_util.is_local_file(temp, require_bundle_conf=True))
            self.assertTrue(resolvers_util.is_local_file(temp, require_bundle_conf=False))
        finally:
            shutil.rmtree(temp)

    def test_is_local_file_with_bundle_conf_dir(self):
        temp = tempfile.mkdtemp()
        open(os.path.join(temp, 'runtime-config.sh'), 'w').close()

        try:
            self.assertFalse(resolvers_util.is_local_file(temp, require_bundle_conf=True))
            self.assertTrue(resolvers_util.is_local_file(temp, require_bundle_conf=False))
        finally:
            shutil.rmtree(temp)


class TestDetectSchemes(TestCase):
    def test_bundle(self):
        mock_isatty = MagicMock(return_value=True)
        mock_exists = MagicMock(return_value=False)

        with patch('os.path.exists', mock_exists), \
                patch('sys.stdin.isatty', mock_isatty), \
                patch.object(bundle_shorthand, 'parse_bundle',
                             wraps=bundle_shorthand.parse_bundle) as parse_bundle:  # spy on the parse_bundle input args
            self.assertEqual([SCHEME_BUNDLE], resolvers_util.detect_schemes('visualizer'))
            parse_bundle.assert_called_once_with('visualizer')
            mock_exists.assert_called_once_with('visualizer')

    def test_bundle_and_file(self):
        mock_isatty = MagicMock(return_value=True)
        mock_exists = MagicMock(return_value=True)

        with patch('os.path.exists', mock_exists), \
                patch('sys.stdin.isatty', mock_isatty), \
                patch.object(bundle_shorthand, 'parse_bundle',
                             wraps=bundle_shorthand.parse_bundle) as parse_bundle:  # spy on the parse_bundle input args
            self.assertEqual([SCHEME_BUNDLE, SCHEME_FILE], resolvers_util.detect_schemes('org/foo/bar'))
            parse_bundle.assert_called_once_with('org/foo/bar')
            mock_exists.assert_called_once_with('org/foo/bar')

    def test_file(self):
        mock_isatty = MagicMock(return_value=True)
        mock_exists = MagicMock(return_value=False)

        with patch('os.path.exists', mock_exists), \
                patch('sys.stdin.isatty', mock_isatty), \
                patch.object(bundle_shorthand, 'parse_bundle',
                             wraps=bundle_shorthand.parse_bundle) as parse_bundle:  # spy on the parse_bundle input args
            self.assertEqual([SCHEME_FILE], resolvers_util.detect_schemes('file:///tmp/foo/bundle.zip'))
            parse_bundle.assert_called_once_with('file:///tmp/foo/bundle.zip')
            mock_exists.assert_not_called()

    def test_http(self):
        mock_isatty = MagicMock(return_value=True)
        mock_exists = MagicMock(return_value=False)

        with patch('os.path.exists', mock_exists), \
                patch('sys.stdin.isatty', mock_isatty), \
                patch.object(bundle_shorthand, 'parse_bundle',
                             wraps=bundle_shorthand.parse_bundle) as parse_bundle:  # spy on the parse_bundle input args
            self.assertEqual([SCHEME_HTTP], resolvers_util.detect_schemes('http://foo/bundle.zip'))
            parse_bundle.assert_called_once_with('http://foo/bundle.zip')
            mock_exists.assert_called_once_with('http://foo/bundle.zip')

    def test_https(self):
        mock_isatty = MagicMock(return_value=True)
        mock_exists = MagicMock(return_value=False)

        with patch('os.path.exists', mock_exists), \
                patch('sys.stdin.isatty', mock_isatty), \
                patch.object(bundle_shorthand, 'parse_bundle',
                             wraps=bundle_shorthand.parse_bundle) as parse_bundle:  # spy on the parse_bundle input args
            self.assertEqual([SCHEME_HTTPS], resolvers_util.detect_schemes('https://foo/bundle.zip'))
            parse_bundle.assert_called_once_with('https://foo/bundle.zip')
            mock_exists.assert_called_once_with('https://foo/bundle.zip')

    def test_s3(self):
        mock_isatty = MagicMock(return_value=True)
        mock_exists = MagicMock(return_value=False)

        with patch('os.path.exists', mock_exists), \
                patch('sys.stdin.isatty', mock_isatty), \
                patch.object(bundle_shorthand, 'parse_bundle',
                             wraps=bundle_shorthand.parse_bundle) as parse_bundle:  # spy on the parse_bundle input args
            self.assertEqual([SCHEME_S3], resolvers_util.detect_schemes('s3://bucket/key/bundle.zip'))
            parse_bundle.assert_called_once_with('s3://bucket/key/bundle.zip')
            mock_exists.assert_called_once_with('s3://bucket/key/bundle.zip')

    def test_no_tty_but_not_stdin(self):
        mock_isatty = MagicMock(return_value=False)
        mock_exists = MagicMock(return_value=False)

        with patch('os.path.exists', mock_exists), \
                patch('sys.stdin.isatty', mock_isatty), \
                patch.object(bundle_shorthand, 'parse_bundle',
                             wraps=bundle_shorthand.parse_bundle) as parse_bundle:  # spy on the parse_bundle input args
            self.assertEqual([SCHEME_S3], resolvers_util.detect_schemes('s3://bucket/key/bundle.zip'))
            parse_bundle.assert_called_once_with('s3://bucket/key/bundle.zip')
            mock_exists.assert_called_once_with('s3://bucket/key/bundle.zip')

    def test_stdin(self):
        mock_isatty = MagicMock(return_value=False)

        with patch('sys.stdin.isatty', mock_isatty):
            self.assertEqual([SCHEME_STDIN], resolvers_util.detect_schemes('-'))
