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
