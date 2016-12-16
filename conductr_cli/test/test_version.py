from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import version, logging_setup
from unittest.mock import MagicMock


class TestConductVersionCommand(CliTestCase):

    def test_success(self):
        args = MagicMock()
        stdout = MagicMock()

        logging_setup.configure_logging(args, stdout)
        result = version.version(args)
        self.assertTrue(result)

        from conductr_cli import __version__
        self.assertEqual(
            strip_margin("""|{}
                            |Supported API version(s): {}
                            |""".format(__version__, ', '.join(version.supported_api_versions()))),
            self.output(stdout))
