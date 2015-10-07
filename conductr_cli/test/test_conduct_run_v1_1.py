from unittest import TestCase
from conductr_cli.test.cli_test_case import CliTestCase
from conductr_cli.test.conduct_run_test_base import ConductRunTestBase
from conductr_cli import conduct_run

try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestConductRunCommand(TestCase, ConductRunTestBase, CliTestCase):

    default_args = {
        'ip': '127.0.0.1',
        'port': 9005,
        'api_version': '1.1',
        'verbose': False,
        'long_ids': False,
        'cli_parameters': '',
        'bundle': '45e0c477d3e5ea92aa8d85c0d8f3e25c',
        'scale': 3,
        'affinity': None
    }

    default_url = 'http://127.0.0.1:9005/v1.1/bundles/45e0c477d3e5ea92aa8d85c0d8f3e25c?scale=3'

    output_template = """|Bundle run request sent.
                         |Stop bundle with: conduct stop{params} {bundle_id}
                         |Print ConductR info with: conduct info{params}
                         |"""

    def test_success_with_affinity(self):
        args = {
            'ip': '127.0.0.1',
            'port': 9005,
            'api_version': '1.1',
            'verbose': False,
            'long_ids': False,
            'cli_parameters': '',
            'bundle': '45e0c477d3e5ea92aa8d85c0d8f3e25c',
            'scale': 3,
            'affinity': 'other-bundle'
        }

        expected_url = 'http://127.0.0.1:9005/v1.1/bundles/45e0c477d3e5ea92aa8d85c0d8f3e25c?scale=3&affinity=other-bundle'

        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()

        with patch('requests.put', http_method), patch('sys.stdout', stdout):
            conduct_run.run(MagicMock(**args))

        http_method.assert_called_with(expected_url)

        self.assertEqual(self.default_output(), self.output(stdout))
