from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import conduct_logs, logging_setup
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT


try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestConductLogsCommand(CliTestCase):

    bundle_id = 'ab8f513'

    bundle_id_urlencoded = 'bundle+id'

    default_args = {
        'ip': '127.0.0.1',
        'port': '9005',
        'api_version': '1',
        'bundle': bundle_id,
        'lines': 1,
        'date': True,
        'utc': True
    }

    default_url = 'http://127.0.0.1:9005/bundles/{}/logs?count=1'.format(bundle_id_urlencoded)

    mock_headers = {'pretend': 'header'}

    def test_no_logs(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with(text='{}')
        quote_method = MagicMock(return_value=self.bundle_id_urlencoded)
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('urllib.parse.quote', quote_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_logs.logs(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        self.assertEqual(
            strip_margin("""|TIME  HOST  LOG
                            |"""),
            self.output(stdout))

    def test_multiple_events(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with(text="""[
            {
                "timestamp":"2015-08-24T01:16:22.327Z",
                "host":"10.0.1.232",
                "message":"[WARN] [04/21/2015 12:54:30.079] [doc-renderer-cluster-1-akka.remote.default-remote-dispatcher-22] Association with remote system has failed."
            },
            {
                "timestamp":"2015-08-24T01:16:25.327Z",
                "host":"10.0.1.232",
                "message":"[WARN] [04/21/2015 12:54:36.079] [doc-renderer-cluster-1-akka.remote.default-remote-dispatcher-26] Association with remote system has failed."
            }
        ]""")
        quote_method = MagicMock(return_value=self.bundle_id_urlencoded)
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('urllib.parse.quote', quote_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_logs.logs(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        self.assertEqual(
            strip_margin("""|TIME                  HOST        LOG
                            |2015-08-24T01:16:22Z  10.0.1.232  [WARN] [04/21/2015 12:54:30.079] [doc-renderer-cluster-1-akka.remote.default-remote-dispatcher-22] Association with remote system has failed.
                            |2015-08-24T01:16:25Z  10.0.1.232  [WARN] [04/21/2015 12:54:36.079] [doc-renderer-cluster-1-akka.remote.default-remote-dispatcher-26] Association with remote system has failed.
                            |"""),
            self.output(stdout))

    def test_failure_invalid_address(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.raise_connection_error('test reason', self.default_url)
        quote_method = MagicMock(return_value=self.bundle_id_urlencoded)
        stderr = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock), \
                patch('urllib.parse.quote', quote_method):
            logging_setup.configure_logging(input_args, err_output=stderr)
            result = conduct_logs.logs(input_args)
            self.assertFalse(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        self.assertEqual(
            self.default_connection_error.format(self.default_url),
            self.output(stderr))
