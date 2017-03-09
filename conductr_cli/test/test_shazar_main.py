from unittest import TestCase
import shutil
import sys
import tempfile
import os
from os import remove
from conductr_cli import logging_setup
from conductr_cli.shazar_main import build_parser, run, write_with_digest
from conductr_cli.test.cli_test_case import as_error, CliTestCase
from unittest.mock import patch, MagicMock


class TestShazar(TestCase):
    def test_write_with_digest(self):
        temp = tempfile.NamedTemporaryFile(mode='w+b')
        temp.write(b'test file data')
        temp.seek(0)

        output = MagicMock()

        write_with_digest(temp, output)

        self.assertEqual(
            CliTestCase.output_bytes(output),
            'test file data\nsha-256/1be7aaf1938cc19af7d2fdeb48a11c381dff8a98d4c4b47b3b0a5044a5255c04'.encode("UTF-8")
        )

    def test_parser_success(self):
        parser = build_parser()
        args = parser.parse_args('--output-dir output-dir source -o output-file --tar'.split())

        self.assertEqual(args.output_dir, 'output-dir')
        self.assertEqual(args.source, 'source')
        self.assertTrue(args.tar)
        self.assertEqual(args.output, 'output-file')


class TestIntegration(CliTestCase):

    def __init__(self, method_name):
        super().__init__(method_name)
        self.tmpfile = tempfile.NamedTemporaryFile(mode='w+b', delete=False)
        self.tmpdir = tempfile.mkdtemp()

    def setUp(self):  # noqa
        self.tmpfile.write(b'test file data')
        self.tmpfile.close()

    def test(self):
        stdout = MagicMock()

        with patch('sys.stdout.write', stdout):
            run('--output-dir {} {}'.format(self.tmpdir, self.tmpfile.name).split())

        self.assertEqual(stdout.call_count, 1)

        # The file separator on Windows `\` need to be escaped before used as part of regex comparison,
        # otherwise it will form an incomplete escape character.
        bundle_dir = '{}{}'.format(self.tmpdir, os.sep).replace('\\', '\\\\')

        self.assertRegex(
            stdout.call_args[0][0],
            ('^{}tmp[a-z0-9_]{{6,8}}-[a-f0-9]{{64}}\.zip' + os.linesep + '$').format(bundle_dir)
        )

    def test_inputs_tty_help(self):
        parser_print_help_mock = MagicMock()

        with \
                patch('sys.stdout.isatty', lambda: True),\
                patch('sys.stdin.isatty', lambda: True), \
                patch('argparse.ArgumentParser.print_help', parser_print_help_mock):
            run('')

        parser_print_help_mock.assert_called_once_with()

    def test_warn_output_tty(self):
        stdout = MagicMock()
        stderr = MagicMock()
        logging_setup.configure_logging(MagicMock(), stdout, stderr)

        configure_logging_mock = MagicMock()

        with \
                patch('sys.stdout.isatty', lambda: True), \
                patch('sys.stdin.isatty', lambda: False), \
                patch('conductr_cli.logging_setup.configure_logging', configure_logging_mock), \
                patch('sys.exit', lambda _: ()):
            run('')

        self.assertEqual(
            self.output(stderr),
            as_error('Error: shazar: Refusing to write to terminal. Provide -o or redirect elsewhere\n')
        )

    def test_warn_tar_output_tty(self):
        stdout = MagicMock()
        stderr = MagicMock()
        logging_setup.configure_logging(MagicMock(), stdout, stderr)

        configure_logging_mock = MagicMock()

        with \
                patch('sys.stdout.isatty', lambda: True), \
                patch('sys.stdin.isatty', lambda: True), \
                patch('conductr_cli.logging_setup.configure_logging', configure_logging_mock), \
                patch('sys.exit', lambda _: ()):
            run(['--tar', 'test.tar'])

        self.assertEqual(
            self.output(stderr),
            as_error('Error: shazar: Refusing to write to terminal. Provide -o or redirect elsewhere\n')
        )

    def test_tar_no_source(self):
        tarfile = MagicMock()
        zipfile = MagicMock()
        stdout = MagicMock()

        file = tempfile.NamedTemporaryFile()

        with \
                patch('sys.stdout.buffer.write', stdout), \
                patch('sys.stdout.isatty', lambda: False), \
                patch('sys.stdin.isatty', lambda: False), \
                patch('zipfile.ZipFile', zipfile), \
                patch('tarfile.open', tarfile), \
                patch('tempfile.NamedTemporaryFile', MagicMock(return_value=file)):
            run('')

        tarfile.assert_called_once_with(fileobj=sys.stdin.buffer, mode='r|')
        zipfile.assert_called_once_with(file, 'w')
        stdout.assert_called_once_with(b'\nsha-256/'
                                       b'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')

    def test_tar_source(self):
        tarfile = MagicMock()
        zipfile = MagicMock()
        stdout = MagicMock()

        file = tempfile.NamedTemporaryFile()

        with \
                patch('sys.stdout.buffer.write', stdout), \
                patch('sys.stdout.isatty', lambda: False),\
                patch('sys.stdin.isatty', lambda: False), \
                patch('zipfile.ZipFile', zipfile),\
                patch('tarfile.open', tarfile), \
                patch('tempfile.NamedTemporaryFile', MagicMock(return_value=file)):
            run(['--tar', 'testing.tar'])

        tarfile.assert_called_once_with('testing.tar', mode='r')
        zipfile.assert_called_once_with(file, 'w')
        stdout.assert_called_once_with(b'\nsha-256/'
                                       b'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')

    def test_regular_source(self):
        tarfile = MagicMock()
        zipfile = MagicMock()
        move = MagicMock()
        stdout = MagicMock()

        file = tempfile.NamedTemporaryFile()

        with \
                patch('sys.stdout.buffer.write', stdout), \
                patch('sys.stdout.isatty', lambda: False), patch('sys.stdin.isatty', lambda: False), \
                patch('zipfile.ZipFile', zipfile), patch('tarfile.open', tarfile), \
                patch('shutil.move', move), \
                patch('tempfile.NamedTemporaryFile', MagicMock(return_value=file)):
            run(['testing'])

        move.assert_called_once_with(
            file.name,
            './testing-e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.zip'
        )

        tarfile.assert_not_called()
        zipfile.assert_called_once_with(file, 'w')
        stdout.assert_called_once_with(
            b'./testing-e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.zip\n'
        )

    def test_output(self):
        mock_tarfile = MagicMock()
        mock_zipfile = MagicMock()
        mock_move = MagicMock()
        mock_open = MagicMock()
        stdout = MagicMock()

        file = tempfile.NamedTemporaryFile()

        with \
                patch('sys.stdout.buffer.write', stdout), \
                patch('sys.stdout.isatty', lambda: False), patch('sys.stdin.isatty', lambda: False), \
                patch('zipfile.ZipFile', mock_zipfile), patch('tarfile.open', mock_tarfile), \
                patch('builtins.open', mock_open), \
                patch('shutil.move', mock_move), \
                patch('tempfile.NamedTemporaryFile', MagicMock(return_value=file)):
            run(['-o', 'test.zip'])

            mock_tarfile.assert_called_once_with(fileobj=sys.stdin.buffer, mode='r|')
            stdout.assert_not_called()
            mock_move.assert_not_called()
            mock_open.assert_called_once_with('test.zip', 'wb')
            mock_zipfile.assert_called_once_with(file, 'w')

    def test_output_dash(self):
        # tests that providing "-o -" goes through stdout

        tarfile = MagicMock()
        zipfile = MagicMock()
        move = MagicMock()
        stdout = MagicMock()

        file = tempfile.NamedTemporaryFile()

        with \
                patch('sys.stdout.buffer.write', stdout), \
                patch('sys.stdout.isatty', lambda: False), patch('sys.stdin.isatty', lambda: False), \
                patch('zipfile.ZipFile', zipfile), patch('tarfile.open', tarfile), \
                patch('shutil.move', move), \
                patch('tempfile.NamedTemporaryFile', MagicMock(return_value=file)):

            run(['-o', '-'])

            tarfile.assert_called_once_with(fileobj=sys.stdin.buffer, mode='r|')
            move.assert_not_called()
            zipfile.assert_called_once_with(file, 'w')
            stdout.assert_called_once_with(b'\nsha-256/'
                                           b'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')

    def tearDown(self):  # noqa
        shutil.rmtree(self.tmpdir)
        remove(self.tmpfile.name)
