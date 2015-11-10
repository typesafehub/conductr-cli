from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import conduct_run

try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class ConductRunTestBase(CliTestCase):

    def __init__(self, method_name):
        super().__init__(method_name)

        self.default_args = {}
        self.default_url = None
        self.output_template = None

    @property
    def default_response(self):
        return strip_margin("""|{
                               |  "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c"
                               |}
                               |""")

    def default_output(self, params='', bundle_id='45e0c47'):
        return strip_margin(self.output_template.format(**{'params': params, 'bundle_id': bundle_id}))

    def base_test_success(self):
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()

        with patch('requests.put', http_method), patch('sys.stdout', stdout):
            conduct_run.run(MagicMock(**self.default_args))

        http_method.assert_called_with(self.default_url)

        self.assertEqual(self.default_output(), self.output(stdout))

    def base_test_success_verbose(self):
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()

        with patch('requests.put', http_method), patch('sys.stdout', stdout):
            args = self.default_args.copy()
            args.update({'verbose': True})
            conduct_run.run(MagicMock(**args))

        http_method.assert_called_with(self.default_url)

        self.assertEqual(self.default_response + self.default_output(), self.output(stdout))

    def base_test_success_long_ids(self):
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()

        with patch('requests.put', http_method), patch('sys.stdout', stdout):
            args = self.default_args.copy()
            args.update({'long_ids': True})
            conduct_run.run(MagicMock(**args))

        http_method.assert_called_with(self.default_url)

        self.assertEqual(self.default_output(bundle_id='45e0c477d3e5ea92aa8d85c0d8f3e25c'), self.output(stdout))

    def base_test_success_with_configuration(self):
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()

        cli_parameters = ' --ip 127.0.1.1 --port 9006'
        with patch('requests.put', http_method), patch('sys.stdout', stdout):
            args = self.default_args.copy()
            args.update({'cli_parameters': cli_parameters})
            conduct_run.run(MagicMock(**args))

        http_method.assert_called_with(self.default_url)

        self.assertEqual(
            self.default_output(params=cli_parameters),
            self.output(stdout))

    def base_test_failure(self):
        http_method = self.respond_with(404)
        stderr = MagicMock()

        with patch('requests.put', http_method), patch('sys.stderr', stderr):
            conduct_run.run(MagicMock(**self.default_args))

        http_method.assert_called_with(self.default_url)

        self.assertEqual(
            strip_margin("""|ERROR: 404 Not Found
                            |"""),
            self.output(stderr))

    def base_test_failure_invalid_address(self):
        http_method = self.raise_connection_error('test reason', self.default_url)
        stderr = MagicMock()

        with patch('requests.put', http_method), patch('sys.stderr', stderr):
            conduct_run.run(MagicMock(**self.default_args))

        http_method.assert_called_with(self.default_url)

        self.assertEqual(
            self.default_connection_error.format(self.default_url),
            self.output(stderr))
