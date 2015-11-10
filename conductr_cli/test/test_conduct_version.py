from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import conduct_version

try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestConductVersionCommand(CliTestCase):

    def test_success(self):
        stdout = MagicMock()

        with patch('sys.stdout', stdout):
            conduct_version.version()

        from conductr_cli import __version__
        self.assertEqual(
            strip_margin("""|{}
                            |Supported API version(s): {}
                            |""".format(__version__, ', '.join(conduct_version.supported_api_versions()))),
            self.output(stdout))
