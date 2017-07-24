from unittest.mock import patch, MagicMock

from requests import HTTPError

from conductr_cli import logging_setup
from conductr_cli.control_protocol import load_bundle, stop_bundle
from conductr_cli.test.cli_test_case import CliTestCase


class TestControlProtocol(CliTestCase):
    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')
    bundle_id = '45e0c477d3e5ea92aa8d85c0d8f3e25c'
    args = {
        'dcos_mode': False,
        'command': 'conduct',
        'scheme': 'http',
        'host': '127.0.0.1',
        'port': 9005,
        'base_path': '/',
        'api_version': '1',
        'disable_instructions': False,
        'verbose': False,
        'no_wait': False,
        'quiet': False,
        'cli_parameters': '',
        'bundle': bundle_id,
        'output_path': '/my/fav/path',
        'conductr_auth': conductr_auth,
        'server_verification_file': server_verification_file
    }

    def test_load_bundle_success(self):
        stdout = MagicMock()
        stderr = MagicMock()
        logging_setup.configure_logging(MagicMock(), stdout, stderr)

        args_mock = MagicMock(**self.args)
        file_mock = MagicMock()
        bundle_url = 'http://127.0.0.1:9005/bundles'
        post_mock = self.respond_with(status_code=200, text='{}')

        with patch('conductr_cli.conduct_request.post', post_mock):
            result = load_bundle(args_mock, file_mock)

        post_mock.assert_called_once_with(False, '127.0.0.1', bundle_url,
                                          auth=self.conductr_auth, data=file_mock,
                                          verify=self.server_verification_file,
                                          headers={'Content-Type': file_mock.content_type})
        self.assertEqual('{}', result)

    def test_load_bundle_failure(self):
        stdout = MagicMock()
        stderr = MagicMock()
        logging_setup.configure_logging(MagicMock(), stdout, stderr)

        args_mock = MagicMock(**self.args)
        file_mock = MagicMock()
        bundle_url = 'http://127.0.0.1:9005/bundles'
        response_mock = self.respond_with(status_code=401)

        with patch('conductr_cli.conduct_request.post', response_mock):
            self.assertRaises(HTTPError, lambda: load_bundle(args_mock, file_mock))

        response_mock.assert_called_once_with(False, '127.0.0.1', bundle_url,
                                              auth=self.conductr_auth, data=file_mock,
                                              verify=self.server_verification_file,
                                              headers={'Content-Type': file_mock.content_type})

    def test_stop_bundle_success(self):
        stdout = MagicMock()
        stderr = MagicMock()
        logging_setup.configure_logging(MagicMock(), stdout, stderr)

        args_mock = MagicMock(**self.args)
        stop_bundle_url = 'http://127.0.0.1:9005/bundles/{}?scale=0'.format(self.bundle_id)
        post_mock = self.respond_with(status_code=200, text='{}')

        with patch('conductr_cli.conduct_request.put', post_mock):
            result = stop_bundle(args_mock)

        post_mock.assert_called_once_with(False, '127.0.0.1', stop_bundle_url,
                                          auth=self.conductr_auth, timeout=5,
                                          verify=self.server_verification_file
                                          )
        self.assertEqual('{}', result)

    def test_stop_bundle_failure(self):
        stdout = MagicMock()
        stderr = MagicMock()
        logging_setup.configure_logging(MagicMock(), stdout, stderr)

        args_mock = MagicMock(**self.args)
        stop_bundle_url = 'http://127.0.0.1:9005/bundles/{}?scale=0'.format(self.bundle_id)
        post_mock = self.respond_with(status_code=401)

        with patch('conductr_cli.conduct_request.put', post_mock):
            self.assertRaises(HTTPError, lambda: stop_bundle(args_mock))

        post_mock.assert_called_once_with(False, '127.0.0.1', stop_bundle_url,
                                          auth=self.conductr_auth, timeout=5,
                                          verify=self.server_verification_file
                                          )
