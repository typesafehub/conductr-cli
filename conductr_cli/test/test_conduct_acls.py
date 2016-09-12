from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import conduct_acls, logging_setup
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT

try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestConductAclsCommandForHttp(CliTestCase):
    default_args = {
        'protocol_family': 'http',
        'ip': '127.0.0.1',
        'port': 9005,
        'api_version': '1',
        'verbose': False,
        'long_ids': False
    }

    default_url = 'http://127.0.0.1:9005/bundles'
    mock_headers = {'pretend': 'header'}

    def test_display(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with_file_contents('data/bundle_with_acls/one_bundle_http.json')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_acls.acls(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        self.assertEqual(
            strip_margin(
                """|METHOD  PATH  REWRITE  SYSTEM                       SYSTEM VERSION  ENDPOINT NAME  BUNDLE ID  BUNDLE NAME                  STATUS
                   |*       /foo           multi-comp-multi-endp-1.0.0  1.0.0           comp1-endp1    f804d64    multi-comp-multi-endp-1.0.0  Starting
                   |"""),
            self.output(stdout))

    def test_display_with_long_id(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with_file_contents('data/bundle_with_acls/one_bundle_http.json')
        stdout = MagicMock()

        args = self.default_args.copy()
        args.update({'long_ids': True})

        input_args = MagicMock(**args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_acls.acls(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        self.assertEqual(
            strip_margin(
                """|METHOD  PATH  REWRITE  SYSTEM                       SYSTEM VERSION  ENDPOINT NAME  BUNDLE ID                         BUNDLE NAME                  STATUS
                   |*       /foo           multi-comp-multi-endp-1.0.0  1.0.0           comp1-endp1    f804d644a01a5ab9f679f76939f5c7e2  multi-comp-multi-endp-1.0.0  Starting
                   |"""),
            self.output(stdout))

    def test_display_multiple_executions(self):
        self.maxDiff = None
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with_file_contents('data/bundle_with_acls/display_multiple_executions_http.json')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_acls.acls(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        self.assertEqual(
            strip_margin(
                """|METHOD  PATH  REWRITE  SYSTEM                       SYSTEM VERSION  ENDPOINT NAME  BUNDLE ID  BUNDLE NAME                  STATUS
                   |*       /foo           multi-comp-multi-endp-1.0.0  1.0.0           comp1-endp1    f804d64    multi-comp-multi-endp-1.0.0  Starting
                   |"""),
            self.output(stdout))

    def test_multiple_acls_sorted(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with_file_contents('data/bundle_with_acls/multiple_bundles_http.json')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_acls.acls(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        self.assertEqual(
            strip_margin(
                """|METHOD  PATH                  REWRITE          SYSTEM                       SYSTEM VERSION  ENDPOINT NAME  BUNDLE ID  BUNDLE NAME                  STATUS
                   |*       /user/(.*)/item/(.*)  /my-items/\\1-\\2  my-endp-1.0.0                1.0.0           dostat         bbb4d64    my-endp-1.0.0                Running
                   |POST    ^/baz/boom            /foo             multi-comp-multi-endp-1.0.0  1.0.0           comp1-endp1    f804d64    multi-comp-multi-endp-1.0.0  Starting
                   |*       ^/bar                                  multi-comp-multi-endp-1.0.0  1.0.0           comp1-endp1    f804d64    multi-comp-multi-endp-1.0.0  Starting
                   |*       /foo                                   multi-comp-multi-endp-1.0.0  1.0.0           comp1-endp1    f804d64    multi-comp-multi-endp-1.0.0  Starting
                   |"""),
            self.output(stdout))

    def test_no_bundles(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with(200, '[]')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_acls.acls(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        self.assertEqual(
            strip_margin(
                """|METHOD  PATH  REWRITE  SYSTEM  SYSTEM VERSION  ENDPOINT NAME  BUNDLE ID  BUNDLE NAME  STATUS
                   |"""),
            self.output(stdout))

    def test_no_acls(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with_file_contents('data/bundle_with_services/one_bundle_starting.json')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_acls.acls(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        self.assertEqual(
            strip_margin(
                """|METHOD  PATH  REWRITE  SYSTEM  SYSTEM VERSION  ENDPOINT NAME  BUNDLE ID  BUNDLE NAME  STATUS
                   |"""),
            self.output(stdout))


class TestConductAclsCommandForTcp(CliTestCase):
    default_args = {
        'protocol_family': 'tcp',
        'ip': '127.0.0.1',
        'port': 9005,
        'api_version': '1',
        'verbose': False,
        'long_ids': False
    }

    default_url = 'http://127.0.0.1:9005/bundles'

    mock_headers = {'pretend': 'header'}

    def test_display(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with_file_contents('data/bundle_with_acls/one_bundle_tcp.json')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_acls.acls(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        self.assertEqual(
            strip_margin(
                """|TCP/PORT  SYSTEM                       SYSTEM VERSION  ENDPOINT NAME  BUNDLE ID  BUNDLE NAME                  STATUS
                   |9001      multi-comp-multi-endp-1.0.0  1.0.0           comp1-endp1    f804d64    multi-comp-multi-endp-1.0.0  Starting
                   |"""),
            self.output(stdout))

    def test_display_with_long_id(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with_file_contents('data/bundle_with_acls/one_bundle_tcp.json')
        stdout = MagicMock()

        args = self.default_args.copy()
        args.update({'long_ids': True})

        input_args = MagicMock(**args)

        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_acls.acls(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        self.assertEqual(
            strip_margin(
                """|TCP/PORT  SYSTEM                       SYSTEM VERSION  ENDPOINT NAME  BUNDLE ID                         BUNDLE NAME                  STATUS
                   |9001      multi-comp-multi-endp-1.0.0  1.0.0           comp1-endp1    f804d644a01a5ab9f679f76939f5c7e2  multi-comp-multi-endp-1.0.0  Starting
                   |"""),
            self.output(stdout))

    def test_display_multiple_executions(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with_file_contents('data/bundle_with_acls/display_multiple_executions_tcp.json')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_acls.acls(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        self.assertEqual(
            strip_margin(
                """|TCP/PORT  SYSTEM                       SYSTEM VERSION  ENDPOINT NAME  BUNDLE ID  BUNDLE NAME                  STATUS
                   |9001      multi-comp-multi-endp-1.0.0  1.0.0           comp1-endp1    f804d64    multi-comp-multi-endp-1.0.0  Starting
                   |"""),
            self.output(stdout))

    def test_multiple_acls_sorted(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with_file_contents('data/bundle_with_acls/multiple_bundles_tcp.json')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)

        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_acls.acls(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        self.assertEqual(
            strip_margin(
                """|TCP/PORT  SYSTEM              SYSTEM VERSION  ENDPOINT NAME  BUNDLE ID  BUNDLE NAME         STATUS
                   |7101      other-bundle-1.0.0  1.0.0           tunnel         aaa4d64    other-bundle-1.0.0  Starting
                   |9006      my-bundle-1.0.0     1.0.0           bin-one        f804d64    my-bundle-1.0.0     Starting
                   |19001     some-bundle-1.0.0   1.0.0           streamer       bbb4d64    some-bundle-1.0.0   Starting
                   |"""),
            self.output(stdout))

    def test_no_bundles(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with(200, '[]')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_acls.acls(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        self.assertEqual(
            strip_margin(
                """|TCP/PORT  SYSTEM  SYSTEM VERSION  ENDPOINT NAME  BUNDLE ID  BUNDLE NAME  STATUS
                   |"""),
            self.output(stdout))

    def test_no_acls(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        http_method = self.respond_with_file_contents('data/bundle_with_services/one_bundle_starting.json')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_acls.acls(input_args)
            self.assertTrue(result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=self.mock_headers)
        self.assertEqual(
            strip_margin(
                """|TCP/PORT  SYSTEM  SYSTEM VERSION  ENDPOINT NAME  BUNDLE ID  BUNDLE NAME  STATUS
                   |"""),
            self.output(stdout))
