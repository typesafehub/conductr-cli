from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import conduct_version, logging_setup

try:
    from unittest.mock import MagicMock  # 3.3 and beyond
except ImportError:
    from mock import MagicMock


class TestConductVersionCommand(CliTestCase):

    def test_success(self):
        args = MagicMock()
        stdout = MagicMock()

        logging_setup.configure_logging(args, stdout)
        conduct_version.version(args)

        from conductr_cli import __version__
        self.assertEqual(
            strip_margin("""|{}
                            |Supported API version(s): {}
                            |""".format(__version__, ', '.join(conduct_version.supported_api_versions()))),
            self.output(stdout))
