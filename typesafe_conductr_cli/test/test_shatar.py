from unittest import TestCase
from unittest.mock import patch, MagicMock
import tempfile
from os import remove
from typesafe_conductr_cli.shatar import digest_file, build_parser

class TestShatar(TestCase):

    def test_digest_file(self):
        temp = tempfile.NamedTemporaryFile(mode='w+b', delete=False)
        temp.write(b"test file data")
        temp_name = temp.name
        temp.close()

        self.assertEqual(
            digest_file(temp_name),
            "1be7aaf1938cc19af7d2fdeb48a11c381dff8a98d4c4b47b3b0a5044a5255c04"
        )

        remove(temp_name)

    def test_parser_success(self):
        parser = build_parser()
        args = parser.parse_args("--output-dir output-dir source".split())

        self.assertEqual(args.output_dir, "output-dir")
        self.assertEqual(args.source, "source")
