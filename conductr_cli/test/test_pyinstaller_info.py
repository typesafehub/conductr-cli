from conductr_cli.test.cli_test_case import CliTestCase
from conductr_cli import pyinstaller_info

from unittest.mock import patch, MagicMock


class TestPyInstallerInfo(CliTestCase):
    def test_return_sys_meipass(self):
        mock_sys_meipass = '/tmp/path'
        mock_sys = MagicMock(**{
            'frozen': True,
            '_MEIPASS': mock_sys_meipass
        })
        with patch('conductr_cli.pyinstaller_info.sys', mock_sys):
            self.assertEqual(mock_sys_meipass, pyinstaller_info.sys_meipass())

    def test_return_none(self):
        mock_sys = MagicMock(**{
            'frozen': False
        })
        with patch('conductr_cli.pyinstaller_info.sys', mock_sys):
            self.assertIsNone(pyinstaller_info.sys_meipass())
