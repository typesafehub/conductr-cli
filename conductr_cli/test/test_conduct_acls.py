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

    def test_display(self):
        http_method = self.respond_with_file_contents('data/bundle_with_acls/one_bundle_http.json')
        stdout = MagicMock()

        with patch('requests.get', http_method):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            result = conduct_acls.acls(MagicMock(**self.default_args))
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT)
        self.assertEqual(
            strip_margin(
                """|METHOD  PATH  REWRITE  BUNDLE ID  BUNDLE NAME                  STATUS
                   |*       /foo           f804d64    multi-comp-multi-endp-1.0.0  Starting
                   |"""),
            self.output(stdout))

    def test_display_with_long_id(self):
        http_method = self.respond_with_file_contents('data/bundle_with_acls/one_bundle_http.json')
        stdout = MagicMock()

        args = self.default_args.copy()
        args.update({'long_ids': True})

        with patch('requests.get', http_method):
            logging_setup.configure_logging(MagicMock(**args), stdout)
            result = conduct_acls.acls(MagicMock(**args))
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT)
        self.assertEqual(
            strip_margin(
                """|METHOD  PATH  REWRITE  BUNDLE ID                         BUNDLE NAME                  STATUS
                   |*       /foo           f804d644a01a5ab9f679f76939f5c7e2  multi-comp-multi-endp-1.0.0  Starting
                   |"""),
            self.output(stdout))

    def test_multiple_acls_sorted(self):
        http_method = self.respond_with_file_contents('data/bundle_with_acls/multiple_bundles_http.json')
        stdout = MagicMock()

        with patch('requests.get', http_method):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            result = conduct_acls.acls(MagicMock(**self.default_args))
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT)
        self.assertEqual(
            strip_margin(
                """|METHOD  PATH                  REWRITE          BUNDLE ID  BUNDLE NAME                  STATUS
                   |*       /user/(.*)/item/(.*)  /my-items/\\1-\\2  bbb4d64    my-endp-1.0.0                Running
                   |POST    ^/baz/boom            /foo             f804d64    multi-comp-multi-endp-1.0.0  Starting
                   |*       ^/bar                                  f804d64    multi-comp-multi-endp-1.0.0  Starting
                   |*       /foo                                   f804d64    multi-comp-multi-endp-1.0.0  Starting
                   |"""),
            self.output(stdout))

    def test_no_bundles(self):
        http_method = self.respond_with(200, '[]')
        stdout = MagicMock()

        with patch('requests.get', http_method):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            result = conduct_acls.acls(MagicMock(**self.default_args))
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT)
        self.assertEqual(
            strip_margin(
                """|METHOD  PATH  REWRITE  BUNDLE ID  BUNDLE NAME  STATUS
                   |"""),
            self.output(stdout))

    def test_no_acls(self):
        http_method = self.respond_with_file_contents('data/bundle_with_services/one_bundle_starting.json')
        stdout = MagicMock()

        with patch('requests.get', http_method):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            result = conduct_acls.acls(MagicMock(**self.default_args))
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT)
        self.assertEqual(
            strip_margin(
                """|METHOD  PATH  REWRITE  BUNDLE ID  BUNDLE NAME  STATUS
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

    def test_display(self):
        http_method = self.respond_with_file_contents('data/bundle_with_acls/one_bundle_tcp.json')
        stdout = MagicMock()

        with patch('requests.get', http_method):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            result = conduct_acls.acls(MagicMock(**self.default_args))
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT)
        self.assertEqual(
            strip_margin(
                """|TCP/PORT  BUNDLE ID  BUNDLE NAME                  STATUS
                   |9001      f804d64    multi-comp-multi-endp-1.0.0  Starting
                   |"""),
            self.output(stdout))

    def test_display_with_long_id(self):
        http_method = self.respond_with_file_contents('data/bundle_with_acls/one_bundle_tcp.json')
        stdout = MagicMock()

        args = self.default_args.copy()
        args.update({'long_ids': True})

        with patch('requests.get', http_method):
            logging_setup.configure_logging(MagicMock(**args), stdout)
            result = conduct_acls.acls(MagicMock(**args))
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT)
        self.assertEqual(
            strip_margin(
                """|TCP/PORT  BUNDLE ID                         BUNDLE NAME                  STATUS
                   |9001      f804d644a01a5ab9f679f76939f5c7e2  multi-comp-multi-endp-1.0.0  Starting
                   |"""),
            self.output(stdout))

    def test_multiple_acls_sorted(self):
        http_method = self.respond_with_file_contents('data/bundle_with_acls/multiple_bundles_tcp.json')
        stdout = MagicMock()

        with patch('requests.get', http_method):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            result = conduct_acls.acls(MagicMock(**self.default_args))
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT)
        self.assertEqual(
            strip_margin(
                """|TCP/PORT  BUNDLE ID  BUNDLE NAME         STATUS
                   |7101      aaa4d64    other-bundle-1.0.0  Starting
                   |9006      f804d64    my-bundle-1.0.0     Starting
                   |19001     bbb4d64    some-bundle-1.0.0   Starting
                   |"""),
            self.output(stdout))

    def test_no_bundles(self):
        http_method = self.respond_with(200, '[]')
        stdout = MagicMock()

        with patch('requests.get', http_method):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            result = conduct_acls.acls(MagicMock(**self.default_args))
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT)
        self.assertEqual(
            strip_margin(
                """|TCP/PORT  BUNDLE ID  BUNDLE NAME  STATUS
                   |"""),
            self.output(stdout))

    def test_no_acls(self):
        http_method = self.respond_with_file_contents('data/bundle_with_services/one_bundle_starting.json')
        stdout = MagicMock()

        with patch('requests.get', http_method):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            result = conduct_acls.acls(MagicMock(**self.default_args))
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, timeout=DEFAULT_HTTP_TIMEOUT)
        self.assertEqual(
            strip_margin(
                """|TCP/PORT  BUNDLE ID  BUNDLE NAME  STATUS
                   |"""),
            self.output(stdout))
