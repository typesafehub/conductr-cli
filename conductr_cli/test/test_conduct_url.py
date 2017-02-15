from unittest import TestCase
from conductr_cli import conduct_url
from unittest.mock import MagicMock


class TestConductUrlIp(TestCase):

    def test_url_v1(self):
        args = MagicMock()
        args.dcos_mode = False
        args.scheme = 'http'
        args.ip = '127.0.0.1'
        args.port = 9005
        args.base_path = '/'
        args.api_version = '1'
        result = conduct_url.url('test', args)
        self.assertEqual('http://127.0.0.1:9005/test', result)

    def test_url_v2(self):
        args = MagicMock()
        args.dcos_mode = False
        args.scheme = 'http'
        args.ip = '127.0.0.1'
        args.port = 9005
        args.base_path = '/'
        args.api_version = '2'
        result = conduct_url.url('test', args)
        self.assertEqual('http://127.0.0.1:9005/v2/test', result)

    def test_conductr_host(self):
        args = MagicMock()
        args.ip = '127.0.0.1'
        result = conduct_url.conductr_host(args)
        self.assertEqual('127.0.0.1', result)


class TestConductUrlHost(TestCase):

    def test_url_v1(self):
        args = MagicMock()
        args.dcos_mode = False
        args.scheme = 'http'
        args.host = '127.0.0.1'
        args.port = 9005
        args.base_path = '/'
        args.api_version = '1'
        result = conduct_url.url('test', args)
        self.assertEqual('http://127.0.0.1:9005/test', result)

    def test_url_v2(self):
        args = MagicMock()
        args.dcos_mode = False
        args.scheme = 'http'
        args.host = '127.0.0.1'
        args.port = 9005
        args.base_path = '/'
        args.api_version = '2'
        result = conduct_url.url('test', args)
        self.assertEqual('http://127.0.0.1:9005/v2/test', result)

    def test_conductr_host(self):
        args = MagicMock()
        args.host = '127.0.0.1'
        result = conduct_url.conductr_host(args)
        self.assertEqual('127.0.0.1', result)


class TestConductServiceLocatorUrl(TestCase):
    args = MagicMock(**{
        'dcos_mode': False,
        'scheme': 'http',
        'host': '127.0.0.1',
        'port': 9005,
        'base_path': '/',
        'api_version': '1'
    })

    def test_service_locator_url(self):
        self.assertEqual('http://127.0.0.1:9008/services/my-endpoint',
                         conduct_url.service_locator_url('my-endpoint', self.args))

    def test_empty(self):
        self.assertEqual('', conduct_url.service_locator_url('', self.args))
        self.assertEqual('', conduct_url.service_locator_url(None, self.args))
