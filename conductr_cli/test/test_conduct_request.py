from unittest import TestCase
from unittest.mock import patch, MagicMock
from conductr_cli import conduct_request


class TestRequest(TestCase):
    dcos_mode = False
    host = '10.0.0.1'
    url = '/url'
    kwargs = {'test': 'kwargs'}

    def test_get(self):
        enriched_args = {'enriched': 'args'}
        enrich_args_mock = MagicMock(return_value=enriched_args)

        dcos_http_response = 'dcos_http_response'
        dcos_http_mock = MagicMock(return_value=dcos_http_response)

        requests_http_response = 'requests_http_response'
        requests_http_mock = MagicMock(return_value=requests_http_response)

        with patch('conductr_cli.conduct_request.enrich_args', enrich_args_mock), \
                patch('dcos.http.get', dcos_http_mock), \
                patch('requests.get', requests_http_mock):
            result = conduct_request.get(self.dcos_mode, self.host, self.url, **self.kwargs)
            self.assertEqual(requests_http_response, result)

        enrich_args_mock.assert_called_with(self.host, **self.kwargs)
        requests_http_mock.assert_called_with(self.url, **enriched_args)
        dcos_http_mock.assert_not_called()

    def test_post(self):
        enriched_args = {'enriched': 'args'}
        enrich_args_mock = MagicMock(return_value=enriched_args)

        dcos_http_response = 'dcos_http_response'
        dcos_http_mock = MagicMock(return_value=dcos_http_response)

        requests_http_response = 'requests_http_response'
        requests_http_mock = MagicMock(return_value=requests_http_response)

        with patch('conductr_cli.conduct_request.enrich_args', enrich_args_mock), \
                patch('dcos.http.post', dcos_http_mock), \
                patch('requests.post', requests_http_mock):
            result = conduct_request.post(self.dcos_mode, self.host, self.url, **self.kwargs)
            self.assertEqual(requests_http_response, result)

        enrich_args_mock.assert_called_with(self.host, **self.kwargs)
        requests_http_mock.assert_called_with(self.url, **enriched_args)
        dcos_http_mock.assert_not_called()

    def test_put(self):
        enriched_args = {'enriched': 'args'}
        enrich_args_mock = MagicMock(return_value=enriched_args)

        dcos_http_response = 'dcos_http_response'
        dcos_http_mock = MagicMock(return_value=dcos_http_response)

        requests_http_response = 'requests_http_response'
        requests_http_mock = MagicMock(return_value=requests_http_response)

        with patch('conductr_cli.conduct_request.enrich_args', enrich_args_mock), \
                patch('dcos.http.put', dcos_http_mock), \
                patch('requests.put', requests_http_mock):
            result = conduct_request.put(self.dcos_mode, self.host, self.url, **self.kwargs)
            self.assertEqual(requests_http_response, result)

        enrich_args_mock.assert_called_with(self.host, **self.kwargs)
        requests_http_mock.assert_called_with(self.url, **enriched_args)
        dcos_http_mock.assert_not_called()

    def test_delete(self):
        enriched_args = {'enriched': 'args'}
        enrich_args_mock = MagicMock(return_value=enriched_args)

        dcos_http_response = 'dcos_http_response'
        dcos_http_mock = MagicMock(return_value=dcos_http_response)

        requests_http_response = 'requests_http_response'
        requests_http_mock = MagicMock(return_value=requests_http_response)

        with patch('conductr_cli.conduct_request.enrich_args', enrich_args_mock), \
                patch('dcos.http.delete', dcos_http_mock), \
                patch('requests.delete', requests_http_mock):
            result = conduct_request.delete(self.dcos_mode, self.host, self.url, **self.kwargs)
            self.assertEqual(requests_http_response, result)

        enrich_args_mock.assert_called_with(self.host, **self.kwargs)
        requests_http_mock.assert_called_with(self.url, **enriched_args)
        dcos_http_mock.assert_not_called()


class TestRequestDcosMode(TestCase):
    dcos_mode = True
    host = '10.0.0.1'
    url = '/url'
    kwargs = {'test': 'kwargs'}

    def test_get(self):
        enriched_args = {'enriched': 'args'}
        enrich_args_mock = MagicMock(return_value=enriched_args)

        dcos_http_response = 'dcos_http_response'
        dcos_http_mock = MagicMock(return_value=dcos_http_response)

        requests_http_response = 'requests_http_response'
        requests_http_mock = MagicMock(return_value=requests_http_response)

        with patch('conductr_cli.conduct_request.enrich_args', enrich_args_mock), \
                patch('dcos.http.get', dcos_http_mock), \
                patch('requests.get', requests_http_mock):
            result = conduct_request.get(self.dcos_mode, self.host, self.url, **self.kwargs)
            self.assertEqual(dcos_http_response, result)

        enrich_args_mock.assert_called_with(self.host, **self.kwargs)
        dcos_http_mock.assert_called_with(self.url, **enriched_args)
        requests_http_mock.assert_not_called()

    def test_post(self):
        enriched_args = {'enriched': 'args'}
        enrich_args_mock = MagicMock(return_value=enriched_args)

        dcos_http_response = 'dcos_http_response'
        dcos_http_mock = MagicMock(return_value=dcos_http_response)

        requests_http_response = 'requests_http_response'
        requests_http_mock = MagicMock(return_value=requests_http_response)

        with patch('conductr_cli.conduct_request.enrich_args', enrich_args_mock), \
                patch('dcos.http.post', dcos_http_mock), \
                patch('requests.post', requests_http_mock):
            result = conduct_request.post(self.dcos_mode, self.host, self.url, **self.kwargs)
            self.assertEqual(dcos_http_response, result)

        enrich_args_mock.assert_called_with(self.host, **self.kwargs)
        dcos_http_mock.assert_called_with(self.url, **enriched_args)
        requests_http_mock.assert_not_called()

    def test_put(self):
        enriched_args = {'enriched': 'args'}
        enrich_args_mock = MagicMock(return_value=enriched_args)

        dcos_http_response = 'dcos_http_response'
        dcos_http_mock = MagicMock(return_value=dcos_http_response)

        requests_http_response = 'requests_http_response'
        requests_http_mock = MagicMock(return_value=requests_http_response)

        with patch('conductr_cli.conduct_request.enrich_args', enrich_args_mock), \
                patch('dcos.http.put', dcos_http_mock), \
                patch('requests.put', requests_http_mock):
            result = conduct_request.put(self.dcos_mode, self.host, self.url, **self.kwargs)
            self.assertEqual(dcos_http_response, result)

        enrich_args_mock.assert_called_with(self.host, **self.kwargs)
        dcos_http_mock.assert_called_with(self.url, **enriched_args)
        requests_http_mock.assert_not_called()

    def test_delete(self):
        enriched_args = {'enriched': 'args'}
        enrich_args_mock = MagicMock(return_value=enriched_args)

        dcos_http_response = 'dcos_http_response'
        dcos_http_mock = MagicMock(return_value=dcos_http_response)

        requests_http_response = 'requests_http_response'
        requests_http_mock = MagicMock(return_value=requests_http_response)

        with patch('conductr_cli.conduct_request.enrich_args', enrich_args_mock), \
                patch('dcos.http.delete', dcos_http_mock), \
                patch('requests.delete', requests_http_mock):
            result = conduct_request.delete(self.dcos_mode, self.host, self.url, **self.kwargs)
            self.assertEqual(dcos_http_response, result)

        enrich_args_mock.assert_called_with(self.host, **self.kwargs)
        dcos_http_mock.assert_called_with(self.url, **enriched_args)
        requests_http_mock.assert_not_called()


class TestEnrichKwargs(TestCase):
    host = '10.0.0.1'
    auth = ('username', 'password')
    verify = '/path/to/pem.file'

    def test_append_host_header(self):
        input_kwargs = {
            'item': 'one',
            'auth': self.auth,
            'verify': self.verify
        }
        result = conduct_request.enrich_args(self.host, **input_kwargs)
        expected_result = {
            'item': 'one',
            'headers': {'Host': self.host},
            'auth': self.auth,
            'verify': self.verify
        }
        self.assertEqual(expected_result, result)

    def test_remove_auth_none(self):
        input_kwargs = {
            'item': 'one',
            'auth': None,
            'verify': self.verify
        }
        result = conduct_request.enrich_args(self.host, **input_kwargs)
        expected_result = {
            'item': 'one',
            'headers': {'Host': self.host},
            'verify': self.verify
        }
        self.assertEqual(expected_result, result)

    def test_remove_verify_none(self):
        input_kwargs = {
            'item': 'one',
            'auth': self.auth,
            'verify': None
        }
        result = conduct_request.enrich_args(self.host, **input_kwargs)
        expected_result = {
            'item': 'one',
            'headers': {'Host': self.host},
            'auth': self.auth
        }
        self.assertEqual(expected_result, result)
