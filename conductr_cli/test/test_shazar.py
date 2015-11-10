from unittest import TestCase
import shutil
import tempfile
from os import remove
from conductr_cli.shazar import create_digest, build_parser, run
from conductr_cli.test.cli_test_case import CliTestCase

try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestShazar(TestCase):

    def test_create_digest(self):
        temp = tempfile.NamedTemporaryFile(mode='w+b', delete=False)
        temp.write(b'test file data')
        temp_name = temp.name
        temp.close()
        self.assertEqual(
            create_digest(temp_name),
            '1be7aaf1938cc19af7d2fdeb48a11c381dff8a98d4c4b47b3b0a5044a5255c04'
        )
        remove(temp_name)

    def test_parser_success(self):
        parser = build_parser()
        args = parser.parse_args('--output-dir output-dir source'.split())

        self.assertEqual(args.output_dir, 'output-dir')
        self.assertEqual(args.source, 'source')


class TestIntegration(CliTestCase):

    def __init__(self, method_name):
        super().__init__(method_name)
        self.tmpfile = tempfile.NamedTemporaryFile(mode='w+b', delete=False)
        self.tmpdir = tempfile.mkdtemp()

    def setUp(self):  # noqa
        self.tmpfile.write(b'test file data')

    def test(self):
        stdout = MagicMock()
        with patch('sys.stdout', stdout):
            run('--output-dir {} {}'.format(self.tmpdir, self.tmpfile.name).split())

        self.assertRegex(
            self.output(stdout),
            'Created digested ZIP archive at {}/tmp[a-z0-9_]{{6,8}}-[a-f0-9]{{64}}\.zip'.format(self.tmpdir)
        )

    def tearDown(self):  # noqa
        shutil.rmtree(self.tmpdir)
        remove(self.tmpfile.name)
