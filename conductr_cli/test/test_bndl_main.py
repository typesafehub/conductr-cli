from conductr_cli import bndl_main
from conductr_cli.test.cli_test_case import CliTestCase, as_error
from io import BytesIO
from unittest.mock import patch, MagicMock
import os
import shutil
import tempfile


class TestBndl(CliTestCase):
    parser = bndl_main.build_parser()

    def test_parser_with_min_params(self):
        args = self.parser.parse_args(['--name', 'hello', '--image-tag', 'latest'])

        self.assertEqual(args.func.__name__, 'bndl')
        self.assertEqual(args.name, 'hello')
        self.assertEqual(args.image_tag, 'latest')
        self.assertTrue(args.use_shazar)
        self.assertTrue(args.use_default_endpoints)

    def test_parser_with_all_params(self):
        args = self.parser.parse_args([
            'oci-image-dir',
            '--name',
            'world',
            '--image-tag',
            'earliest',
            '--image-name',
            'test',
            '-o',
            '/dev/null',
            '--no-shazar',
            '--component-description',
            'some description',
            '--version',
            '4',
            '--compatibility-version',
            '5',
            '--system',
            'myapp',
            '--system-version',
            '3',
            '--nr-of-cpus',
            '8',
            '--memory',
            '65536',
            '--disk-space',
            '16384',
            '--roles',
            'web',
            'backend',
            '--with-check',
            '--no-default-endpoints',
            '--annotation',
            'com.lightbend.test=hello world',
            '--annotation',
            'description=this is a test'
        ])

        self.assertEqual(args.source, 'oci-image-dir')
        self.assertEqual(args.func.__name__, 'bndl')
        self.assertEqual(args.name, 'world')
        self.assertEqual(args.image_tag, 'earliest')
        self.assertEqual(args.image_name, 'test')
        self.assertEqual(args.output, '/dev/null')
        self.assertFalse(args.use_shazar)
        self.assertEqual(args.component_description, 'some description')
        self.assertEqual(args.version, '4')
        self.assertEqual(args.compatibility_version, '5')
        self.assertEqual(args.system, 'myapp')
        self.assertEqual(args.system_version, '3')
        self.assertEqual(args.nr_of_cpus, 8.0)
        self.assertEqual(args.memory, 65536)
        self.assertEqual(args.disk_space, 16384)
        self.assertEqual(args.roles, ['web', 'backend'])
        self.assertEqual(args.annotations, ['com.lightbend.test=hello world', 'description=this is a test'])
        self.assertFalse(args.use_default_endpoints)

    def test_parser_no_args(self):
        args = self.parser.parse_args([])

        self.assertEqual(args.func.__name__, 'bndl')
        self.assertTrue(args.use_shazar)

    def test_run_dash_rewrite(self):
        bndl_mock = MagicMock()
        exit_mock = MagicMock()

        with \
                patch('conductr_cli.bndl_main.bndl', bndl_mock), \
                patch('sys.stdout.isatty', lambda: False), \
                patch('sys.stdin.isatty', lambda: False), \
                patch('sys.exit', exit_mock):
            bndl_main.run(['-o', '-', '-'])

        self.assertEqual(bndl_mock.call_count, 1)
        self.assertIsNone(bndl_mock.call_args[0][0].output)
        self.assertIsNone(bndl_mock.call_args[0][0].source)

    def test_warn_output_tty(self):
        stdout_mock = MagicMock()
        stderr_mock = MagicMock()
        exit_mock = MagicMock()
        configure_logging_mock = MagicMock()
        bndl_main.logging_setup.configure_logging(MagicMock(), stdout_mock, stderr_mock)

        with \
                patch('sys.stdin', MagicMock(**{'buffer': BytesIO(b''), 'isatty': MagicMock(return_value=False)})), \
                patch('sys.stdout.isatty', lambda: True), \
                patch('conductr_cli.logging_setup.configure_logging', configure_logging_mock), \
                patch('sys.exit', exit_mock):
            bndl_main.run(['--name', 'test', '--image-tag', 'latest'])

        self.assertEqual(
            self.output(stderr_mock),
            as_error('Error: bndl: Refusing to write to terminal. Provide -o or redirect elsewhere\n')
        )

        exit_mock.assert_called_once_with(2)

    def test_warn_bad_file(self):
        stdout_mock = MagicMock()
        stderr_mock = MagicMock()
        exit_mock = MagicMock()
        configure_logging_mock = MagicMock()
        bndl_main.logging_setup.configure_logging(MagicMock(), stdout_mock, stderr_mock)

        with \
                patch('sys.stdin', MagicMock(**{'buffer': BytesIO(b'')})), \
                patch('sys.stdout.isatty', lambda: False), \
                patch('conductr_cli.logging_setup.configure_logging', configure_logging_mock), \
                patch('sys.exit', exit_mock):
            bndl_main.run(['--name', 'test', '-f', 'docker', '/some/file'])

        self.assertEqual(
            self.output(stderr_mock),
            as_error('Error: bndl: Unable to read /some/file. Must be the path to a valid file or directory\n')
        )

        exit_mock.assert_called_once_with(2)

    def test_warn_bad_oci_image_format_no_tag(self):
        stdout_mock = MagicMock()
        stderr_mock = MagicMock()
        exit_mock = MagicMock()
        configure_logging_mock = MagicMock()
        bndl_main.logging_setup.configure_logging(MagicMock(), stdout_mock, stderr_mock)
        temp = tempfile.mkdtemp()

        try:
            with \
                    patch('sys.stdin', MagicMock(**{'buffer': BytesIO(b'')})), \
                    patch('sys.stdout.isatty', lambda: False), \
                    patch('conductr_cli.logging_setup.configure_logging', configure_logging_mock), \
                    patch('sys.exit', exit_mock):
                bndl_main.run(['--name', 'test', '-f', 'oci-image', '--image-tag', 'latest', temp])

            self.assertEqual(
                self.output(stderr_mock),
                as_error('Error: bndl: Not an OCI Image\n')
            )

            exit_mock.assert_called_once_with(2)
        finally:
            shutil.rmtree(temp)

    def test_warn_bad_oci_image_format_no_layout(self):
        stdout_mock = MagicMock()
        stderr_mock = MagicMock()
        exit_mock = MagicMock()
        configure_logging_mock = MagicMock()
        bndl_main.logging_setup.configure_logging(MagicMock(), stdout_mock, stderr_mock)
        temp = tempfile.mkdtemp()

        try:
            os.mkdir(os.path.join(temp, 'refs'))
            open(os.path.join(temp, 'refs/latest'), 'a').close()

            with \
                    patch('sys.stdin', MagicMock(**{'buffer': BytesIO(b'')})), \
                    patch('sys.stdout.isatty', lambda: False), \
                    patch('conductr_cli.logging_setup.configure_logging', configure_logging_mock), \
                    patch('sys.exit', exit_mock):
                bndl_main.run(['--name', 'test', '-f', 'oci-image', '--image-tag', 'latest', temp])

            self.assertEqual(
                self.output(stderr_mock),
                as_error('Error: bndl: Invalid OCI Image. Missing oci-layout\n')
            )

            exit_mock.assert_called_once_with(2)
        finally:
            shutil.rmtree(temp)
