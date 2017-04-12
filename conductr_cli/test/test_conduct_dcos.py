from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import conduct_dcos, logging_setup
from unittest.mock import patch, MagicMock

import os


class TestConductDcosCommand(CliTestCase):

    def test_success_which(self):
        args = MagicMock()
        stdout = MagicMock()
        makedirs = MagicMock()
        symlink = MagicMock()

        logging_setup.configure_logging(args, stdout)

        with patch('shutil.which', lambda x: '/somefile'), \
                patch('sys.executable', '/usr/bin/python3'), \
                patch('os.path.exists', lambda x: True), \
                patch('os.remove', lambda x: True), \
                patch('os.makedirs', makedirs), \
                patch('os.symlink', symlink):
            result = conduct_dcos.setup(args)
        self.assertTrue(result)

        makedirs.assert_called_once_with(
            '{}/.dcos/subcommands/conductr/env/bin'.format(os.path.expanduser('~')),
            exist_ok=True
        )

        symlink.assert_called_with('/somefile',
                                   '{}/.dcos/subcommands/conductr/env/bin/dcos-conduct'.format(os.path.expanduser('~')))

        self.assertEqual(
            strip_margin("""|The DC/OS CLI is now configured.
                            |Prefix \'conduct\' with \'dcos\' when you want to contact ConductR on DC/OS e.g. \'dcos conduct info\'
                            |"""),
            self.output(stdout))

    def test_success_executable(self):
        args = MagicMock()
        stdout = MagicMock()
        makedirs = MagicMock()
        symlink = MagicMock()

        logging_setup.configure_logging(args, stdout)

        with \
                patch('shutil.which', lambda x: '/somefile'), \
                patch('sys.executable', '/path/to/conduct'), \
                patch('os.path.exists', lambda x: True), \
                patch('os.remove', lambda x: True), \
                patch('os.makedirs', makedirs), \
                patch('os.symlink', symlink):
            result = conduct_dcos.setup(args)
        self.assertTrue(result)

        symlink.assert_called_with('/path/to/conduct',
                                   '{}/.dcos/subcommands/conductr/env/bin/dcos-conduct'.format(os.path.expanduser('~')))

    def test_create_dir(self):
        args = MagicMock()
        stdout = MagicMock()
        remove = MagicMock()
        makedirs = MagicMock()
        symlink = MagicMock()

        logging_setup.configure_logging(args, stdout)

        with \
                patch('shutil.which', lambda x: '/somefile'), \
                patch('os.path.exists', lambda x: False), \
                patch('os.path.islink', lambda x: False), \
                patch('os.remove', remove), \
                patch('os.makedirs', makedirs), \
                patch('os.symlink', symlink):
            result = conduct_dcos.setup(args)
        self.assertTrue(result)

        remove.assert_not_called()

        makedirs.assert_called_with('{}/.dcos/subcommands/conductr/env/bin'.format(os.path.expanduser('~')),
                                    exist_ok=True)
        symlink.assert_called_with('/somefile',
                                   '{}/.dcos/subcommands/conductr/env/bin/dcos-conduct'.format(os.path.expanduser('~')))

        self.assertEqual(
            strip_margin("""|The DC/OS CLI is now configured.
                            |Prefix \'conduct\' with \'dcos\' when you want to contact ConductR on DC/OS e.g. \'dcos conduct info\'
                            |"""),
            self.output(stdout))
