from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import conduct_events, logging_setup
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT
from unittest.mock import patch, MagicMock


class TestConductEventsCommand(CliTestCase):

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

    default_url = 'http://127.0.0.1:9005/bundles/{}/events?count=1'.format(bundle_id_urlencoded)

    def test_no_events(self):
        http_method = self.respond_with(text='{}')
        quote_method = MagicMock(return_value=self.bundle_id_urlencoded)
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('urllib.parse.quote', quote_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_events.events(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin("""|TIME  EVENT  DESC
                            |"""),
            self.output(stdout))

    def test_multiple_events(self):
        self.maxDiff = None
        http_method = self.respond_with(text="""[
            {
                "timestamp":"2015-08-24T01:16:22.327Z",
                "event":"conductr.loadScheduler.loadBundleRequested",
                "description":"Load bundle requested: requestId=cba938cd-860e-41a4-9cbe-2c677feaca20, bundleName=visualizer"
            },
            {
                "timestamp":"2015-08-24T01:16:25.327Z",
                "event":"conductr.loadExecutor.bundleWritten",
                "description":"Bundle written: requestId=cba938cd-860e-41a4-9cbe-2c677feaca20, bundleName=visualizer"
            }
        ]""")
        quote_method = MagicMock(return_value=self.bundle_id_urlencoded)
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('urllib.parse.quote', quote_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_events.events(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin("""|TIME                      EVENT                                       DESC
                            |Mon 2015-08-24T01:16:22Z  conductr.loadScheduler.loadBundleRequested  Load bundle requested: requestId=cba938cd-860e-41a4-9cbe-2c677feaca20, bundleName=visualizer
                            |Mon 2015-08-24T01:16:25Z  conductr.loadExecutor.bundleWritten         Bundle written: requestId=cba938cd-860e-41a4-9cbe-2c677feaca20, bundleName=visualizer
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
            result = conduct_events.events(input_args)
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

        default_url = 'http://10.0.0.1:9005/bundles/{}/events?count=1'.format(self.bundle_id_urlencoded)

        http_method = self.respond_with(text='{}')
        quote_method = MagicMock(return_value=self.bundle_id_urlencoded)
        stdout = MagicMock()

        input_args = MagicMock(**args)
        with patch('requests.get', http_method), \
                patch('urllib.parse.quote', quote_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_events.events(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '10.0.0.1'})
        self.assertEqual(
            strip_margin("""|TIME  EVENT  DESC
                            |"""),
            self.output(stdout))


class TestGetBundleEvents(CliTestCase):
    def test_get_bundle_events(self):
        request_url = 'http://url'
        url_mock = MagicMock(return_value=request_url)

        bundle_id = 'bundle-id'
        dcos_mode = True
        host = '10.0.1.1'
        conductr_auth = ('username', 'password')
        server_verification_file = MagicMock()
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'host': host,
            'conductr_auth': conductr_auth,
            'server_verification_file': server_verification_file,
            'bundle': bundle_id
        })

        mock_get = self.respond_with(200, '[]')

        count = 3

        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.conduct_request.get', mock_get):
            self.assertEqual([], conduct_events.get_bundle_events(args, count))

        url_mock.assert_called_once_with('bundles/{}/events?count={}'.format(bundle_id, count), args)
        mock_get.assert_called_once_with(dcos_mode, host, request_url, auth=conductr_auth, timeout=5,
                                         verify=server_verification_file)
