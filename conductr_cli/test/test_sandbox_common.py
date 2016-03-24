from conductr_cli.test.cli_test_case import CliTestCase
from conductr_cli import sandbox_common

try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestSandboxCommon(CliTestCase):
    def test_bundle_http_port(self):
        port_number = 1111
        getenv_mock = MagicMock(return_value=port_number)
        with patch('os.getenv', getenv_mock):
            result = sandbox_common.bundle_http_port()

        self.assertEqual(result, port_number)
        getenv_mock.assert_called_with('BUNDLE_HTTP_PORT', 9000)
