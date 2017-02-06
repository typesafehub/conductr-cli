from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import conduct_logs, logging_setup
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT
from unittest.mock import patch, MagicMock


class TestConductLogsCommand(CliTestCase):

    bundle_id = 'ab8f513'

    bundle_id_urlencoded = 'bundle+id'

    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')

    default_args = {
        'dcos_mode': False,
        'scheme': 'http',
        'host': '127.0.0.1',
        'port': '9005',
        'base_path': '/',
        'api_version': '1',
        'bundle': bundle_id,
        'lines': 1,
        'utc': True,
        'conductr_auth': conductr_auth,
        'server_verification_file': server_verification_file
    }

    default_url = 'http://127.0.0.1:9005/bundles/{}/logs?count=1'.format(bundle_id_urlencoded)

    def test_no_logs(self):
        http_method = self.respond_with(text='{}')
        quote_method = MagicMock(return_value=self.bundle_id_urlencoded)
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('urllib.parse.quote', quote_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_logs.logs(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin("""|TIME  HOST  LOG
                            |"""),
            self.output(stdout))

    def test_multiple_events(self):
        self.maxDiff = None
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
                patch('urllib.parse.quote', quote_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_logs.logs(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin("""|TIME                      HOST        LOG
                            |Mon 2015-08-24T01:16:22Z  10.0.1.232  [WARN] [04/21/2015 12:54:30.079] [doc-renderer-cluster-1-akka.remote.default-remote-dispatcher-22] Association with remote system has failed.
                            |Mon 2015-08-24T01:16:25Z  10.0.1.232  [WARN] [04/21/2015 12:54:36.079] [doc-renderer-cluster-1-akka.remote.default-remote-dispatcher-26] Association with remote system has failed.
                            |"""),
            self.output(stdout))

    def test_failure_invalid_address(self):
        http_method = self.raise_connection_error('test reason', self.default_url)
        quote_method = MagicMock(return_value=self.bundle_id_urlencoded)
        stderr = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('urllib.parse.quote', quote_method):
            logging_setup.configure_logging(input_args, err_output=stderr)
            result = conduct_logs.logs(input_args)
            self.assertFalse(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            self.default_connection_error.format(self.default_url),
            self.output(stderr))

    def test_ip(self):
        args = {}
        args.update(self.default_args)
        args.pop('host')
        args.update({'ip': '10.0.0.1'})

        default_url = 'http://10.0.0.1:9005/bundles/{}/logs?count=1'.format(self.bundle_id_urlencoded)

        http_method = self.respond_with(text='{}')
        quote_method = MagicMock(return_value=self.bundle_id_urlencoded)
        stdout = MagicMock()

        input_args = MagicMock(**args)
        with patch('requests.get', http_method), \
                patch('urllib.parse.quote', quote_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_logs.logs(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '10.0.0.1'})
        self.assertEqual(
            strip_margin("""|TIME  HOST  LOG
                            |"""),
            self.output(stdout))
