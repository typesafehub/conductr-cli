from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import bundle_scale, logging_setup
from conductr_cli.exceptions import WaitTimeoutError

try:
    from unittest.mock import call, patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import call, patch, MagicMock


class TestGetScale(CliTestCase):
    mock_headers = {'pretend': 'header'}

    def test_return_scale_v1(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        bundles_endpoint_reply = """
            [{
                "bundleId": "a101449418187d92c789d1adc240b6d6",
                "bundleExecutions": [
                    {
                        "host": "127.0.0.1",
                        "endpoints": {
                            "web": {
                                "bindPort": 10822,
                                "hostPort": 10822
                            }
                        },
                        "isStarted": true
                    },
                    {
                        "host": "127.0.0.2",
                        "endpoints": {
                            "web": {
                                "bindPort": 10822,
                                "hostPort": 10822
                            }
                        },
                        "isStarted": false
                    }
                ]
            }]
        """
        http_method = self.respond_with(text=bundles_endpoint_reply)

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        args = {
            'ip': '127.0.0.1',
            'port': '9005',
            'api_version': '1'
        }
        input_args = MagicMock(**args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            result = bundle_scale.get_scale(bundle_id, input_args)
            self.assertEqual(1, result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with('http://127.0.0.1:9005/bundles', headers=self.mock_headers)

    def test_return_scale_v2(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        bundles_endpoint_reply = """
            [{
                "bundleId": "a101449418187d92c789d1adc240b6d6",
                "bundleExecutions": [
                    {
                        "host": "127.0.0.1",
                        "endpoints": {
                            "web": {
                                "bindPort": 10822,
                                "hostPort": 10822
                            }
                        },
                        "isStarted": true
                    },
                    {
                        "host": "127.0.0.2",
                        "endpoints": {
                            "web": {
                                "bindPort": 10822,
                                "hostPort": 10822
                            }
                        },
                        "isStarted": false
                    }
                ]
            }]
        """
        http_method = self.respond_with(text=bundles_endpoint_reply)

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        args = {
            'ip': '127.0.0.1',
            'port': '9005',
            'api_version': '2'
        }
        input_args = MagicMock(**args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            result = bundle_scale.get_scale(bundle_id, input_args)
            self.assertEqual(1, result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with('http://127.0.0.1:9005/v2/bundles', headers=self.mock_headers)

    def test_return_zero_v1(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        bundles_endpoint_reply = '[]'
        http_method = self.respond_with(text=bundles_endpoint_reply)

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        args = {
            'ip': '127.0.0.1',
            'port': '9005',
            'api_version': '1'
        }
        input_args = MagicMock(**args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            result = bundle_scale.get_scale(bundle_id, input_args)
            self.assertEqual(0, result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with('http://127.0.0.1:9005/bundles', headers=self.mock_headers)

    def test_return_zero_v2(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
        bundles_endpoint_reply = '[]'
        http_method = self.respond_with(text=bundles_endpoint_reply)

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        args = {
            'ip': '127.0.0.1',
            'port': '9005',
            'api_version': '2'
        }
        input_args = MagicMock(**args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            result = bundle_scale.get_scale(bundle_id, input_args)
            self.assertEqual(0, result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with('http://127.0.0.1:9005/v2/bundles', headers=self.mock_headers)


class TestWaitForScale(CliTestCase):
    def test_wait_for_scale(self):
        get_scale_mock = MagicMock(side_effect=[0, 1, 2, 3])
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        get_events_mock = MagicMock(return_value=[
            self.create_test_event(None),
            self.create_test_event('bundleExecutionAdded'),
            self.create_test_event('bundleExecutionAdded'),
            self.create_test_event('bundleExecutionAdded')
        ])

        stdout = MagicMock()

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        args = MagicMock(**{
            'wait_timeout': 10
        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_scale.get_scale', get_scale_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_scale.wait_for_scale(bundle_id, 3, args)

        self.assertEqual(get_scale_mock.call_args_list, [
            call(bundle_id, args),
            call(bundle_id, args),
            call(bundle_id, args),
            call(bundle_id, args)
        ])

        url_mock.assert_called_with('bundles/events', args)

        self.assertEqual(strip_margin("""|Bundle a101449418187d92c789d1adc240b6d6 waiting to reach expected scale 3
                                         |Bundle a101449418187d92c789d1adc240b6d6 has scale 1, expected 3
                                         |Bundle a101449418187d92c789d1adc240b6d6 has scale 2, expected 3
                                         |Bundle a101449418187d92c789d1adc240b6d6 expected scale 3 is met
                                         |"""), self.output(stdout))

    def test_return_immediately_if_scale_is_met(self):
        get_scale_mock = MagicMock(side_effect=[3])

        stdout = MagicMock()

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        args = MagicMock(**{
            'wait_timeout': 10
        })
        with patch('conductr_cli.bundle_scale.get_scale', get_scale_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_scale.wait_for_scale(bundle_id, 3, args)

        self.assertEqual(get_scale_mock.call_args_list, [
            call(bundle_id, args)
        ])

        self.assertEqual(strip_margin("""|Bundle a101449418187d92c789d1adc240b6d6 expected scale 3 is met
                                         |"""), self.output(stdout))

    def test_wait_timeout(self):
        get_scale_mock = MagicMock(side_effect=[0, 1, 2, 3])
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        get_events_mock = MagicMock(return_value=[
            self.create_test_event('bundleExecutionAdded'),
            self.create_test_event('bundleExecutionAdded'),
            self.create_test_event('bundleExecutionAdded')
        ])

        stdout = MagicMock()

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        args = MagicMock(**{
            # Purposely set no timeout to invoke the error
            'wait_timeout': -1
        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_scale.get_scale', get_scale_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            self.assertRaises(WaitTimeoutError, bundle_scale.wait_for_scale, bundle_id, 3, args)

        self.assertEqual(get_scale_mock.call_args_list, [
            call(bundle_id, args)
        ])

        url_mock.assert_called_with('bundles/events', args)

        self.assertEqual(strip_margin("""|Bundle a101449418187d92c789d1adc240b6d6 waiting to reach expected scale 3
                                         |"""), self.output(stdout))

    def test_wait_timeout_all_events(self):
        get_scale_mock = MagicMock(return_value=0)
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        get_events_mock = MagicMock(return_value=[
            self.create_test_event('bundleExecutionAdded'),
            self.create_test_event('bundleExecutionAdded'),
            self.create_test_event('bundleExecutionAdded')
        ])

        stdout = MagicMock()

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        args = MagicMock(**{
            'wait_timeout': 10
        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_scale.get_scale', get_scale_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            self.assertRaises(WaitTimeoutError, bundle_scale.wait_for_scale, bundle_id, 3, args)

        self.assertEqual(get_scale_mock.call_args_list, [
            call(bundle_id, args),
            call(bundle_id, args),
            call(bundle_id, args),
            call(bundle_id, args)
        ])

        url_mock.assert_called_with('bundles/events', args)

        self.assertEqual(strip_margin("""|Bundle a101449418187d92c789d1adc240b6d6 waiting to reach expected scale 3
                                         |Bundle a101449418187d92c789d1adc240b6d6 has scale 0, expected 3
                                         |Bundle a101449418187d92c789d1adc240b6d6 has scale 0, expected 3
                                         |Bundle a101449418187d92c789d1adc240b6d6 has scale 0, expected 3
                                         |"""), self.output(stdout))

    def create_test_event(self, event_name):
        sse_mock = MagicMock()
        sse_mock.event = event_name
        return sse_mock
