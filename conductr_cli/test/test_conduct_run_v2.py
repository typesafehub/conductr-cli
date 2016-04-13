from conductr_cli.test.conduct_run_test_base import ConductRunTestBase
from conductr_cli import conduct_run, logging_setup

try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestConductRunCommand(ConductRunTestBase):

    def __init__(self, method_name):
        super().__init__(method_name)

        self.bundle_id = '45e0c477d3e5ea92aa8d85c0d8f3e25c'
        self.scale = 3
        self.default_args = {
            'ip': '127.0.0.1',
            'port': 9005,
            'api_version': '2',
            'verbose': False,
            'quiet': False,
            'no_wait': False,
            'long_ids': False,
            'cli_parameters': '',
            'bundle': self.bundle_id,
            'scale': self.scale,
            'affinity': None
        }

        self.default_url = 'http://127.0.0.1:9005/v2/bundles/45e0c477d3e5ea92aa8d85c0d8f3e25c?scale=3'

        self.output_template = """|Bundle run request sent.
                                  |Stop bundle with: conduct stop{params} {bundle_id}
                                  |Print ConductR info with: conduct info{params}
                                  |"""

    def test_success(self):
        self.base_test_success()

    def test_success_verbose(self):
        self.base_test_success_verbose()

    def test_success_long_ids(self):
        self.base_test_success_long_ids()

    def test_success_with_configuration(self):
        self.base_test_success_with_configuration()

    def test_success_no_wait(self):
        self.base_test_success_no_wait()

    def test_failure(self):
        self.base_test_failure()

    def test_failure_invalid_address(self):
        self.base_test_failure_invalid_address()

    def test_failure_scale_timeout(self):
        self.base_test_failure_scale_timeout()

    def test_success_with_affinity(self):
        args = {
            'ip': '127.0.0.1',
            'port': 9005,
            'api_version': '2',
            'verbose': False,
            'quiet': False,
            'no_wait': False,
            'long_ids': False,
            'cli_parameters': '',
            'bundle': self.bundle_id,
            'scale': self.scale,
            'affinity': 'other-bundle'
        }

        expected_url = \
            'http://127.0.0.1:9005/v2/bundles/45e0c477d3e5ea92aa8d85c0d8f3e25c?scale=3&affinity=other-bundle'

        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with(200, self.default_response)
        wait_for_scale_mock = MagicMock()
        stdout = MagicMock()

        input_args = MagicMock(**args)
        with patch('requests.put', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('conductr_cli.bundle_scale.wait_for_scale', wait_for_scale_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_run.run(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(expected_url, headers=self.mock_headers)
        wait_for_scale_mock.assert_called_with(self.bundle_id, self.scale, input_args)

        self.assertEqual(self.default_output(), self.output(stdout))
