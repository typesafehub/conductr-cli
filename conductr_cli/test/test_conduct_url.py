from unittest import TestCase
from conductr_cli import conduct_url

try:
    from unittest.mock import MagicMock  # 3.3 and beyond
except ImportError:
    from mock import MagicMock


class TestConductUrl(TestCase):

    def test_url_v1(self):
        args = MagicMock()
        args.ip = '127.0.0.1'
        args.port = 9005
        args.api_version = '1'
        result = conduct_url.url('test', args)
        self.assertEqual('http://127.0.0.1:9005/test', result)

    def test_url_v2(self):
        args = MagicMock()
        args.ip = '127.0.0.1'
        args.port = 9005
        args.api_version = '2'
        result = conduct_url.url('test', args)
        self.assertEqual('http://127.0.0.1:9005/v2/test', result)


class TestRequestHeaders(TestCase):

    def test_return_headers(self):
        ip_address = "my-test-ip"
        args = {'ip': ip_address}
        input_args = MagicMock(**args)
        result = conduct_url.request_headers(input_args)
        expected_result = {'Host': ip_address}
        self.assertEqual(result, expected_result)

    def test_return_none(self):
        args = {'ip': None}
        input_args = MagicMock(**args)
        result = conduct_url.request_headers(input_args)
        self.assertIsNone(result)
