from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import conduct_dcos, logging_setup

import os

try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestConductDcosCommand(CliTestCase):

    def test_success(self):
        args = MagicMock()
        stdout = MagicMock()
        symlink = MagicMock()

        logging_setup.configure_logging(args, stdout)

        with patch('shutil.which', lambda x: '/somefile'), \
                patch('os.path.exists', lambda x: True), \
                patch('os.remove', lambda x: True), \
                patch('os.symlink', symlink):
            result = conduct_dcos.setup(args)
        self.assertTrue(result)

        symlink.assert_called_with('/somefile',
                                   '{}/.dcos/subcommands/conductr/env/bin/dcos-conduct'.format(os.path.expanduser('~')))

        self.assertEqual(
            strip_margin("""|The DC/OS CLI is now configured.
                            |Prefix \'conduct\' with \'dcos\' when you want to contact ConductR on DC/OS e.g. \'dcos conduct info\'
                            |"""),
            self.output(stdout))
