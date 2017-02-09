from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import bundle_scale, logging_setup
from conductr_cli.exceptions import WaitTimeoutError
from unittest.mock import call, patch, MagicMock


class TestGetScaleIp(CliTestCase):

    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')

    def test_return_scale_v1(self):
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
            'dcos_mode': False,
            'scheme': 'http',
            'ip': '127.0.0.1',
            'port': '9005',
            'base_path': '/',
            'api_version': '1',
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        }
        input_args = MagicMock(**args)
        with patch('requests.get', http_method):
            result = bundle_scale.get_scale(bundle_id, input_args)
            self.assertEqual(1, result)

        http_method.assert_called_with('http://127.0.0.1:9005/bundles', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})

    def test_return_scale_v2(self):
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
            'dcos_mode': False,
            'scheme': 'http',
            'ip': '127.0.0.1',
            'port': '9005',
            'base_path': '/',
            'api_version': '2',
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        }
        input_args = MagicMock(**args)
        with patch('requests.get', http_method):
            result = bundle_scale.get_scale(bundle_id, input_args)
            self.assertEqual(1, result)

        http_method.assert_called_with('http://127.0.0.1:9005/v2/bundles', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})

    def test_return_zero_v1(self):
        bundles_endpoint_reply = '[]'
        http_method = self.respond_with(text=bundles_endpoint_reply)

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        args = {
            'dcos_mode': False,
            'scheme': 'http',
            'ip': '127.0.0.1',
            'port': '9005',
            'base_path': '/',
            'api_version': '1',
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        }
        input_args = MagicMock(**args)
        with patch('requests.get', http_method):
            result = bundle_scale.get_scale(bundle_id, input_args)
            self.assertEqual(0, result)

        http_method.assert_called_with('http://127.0.0.1:9005/bundles', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})

    def test_return_zero_v2(self):
        bundles_endpoint_reply = '[]'
        http_method = self.respond_with(text=bundles_endpoint_reply)

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        args = {
            'dcos_mode': False,
            'scheme': 'http',
            'ip': '127.0.0.1',
            'port': '9005',
            'base_path': '/',
            'api_version': '2',
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        }
        input_args = MagicMock(**args)
        with patch('requests.get', http_method):
            result = bundle_scale.get_scale(bundle_id, input_args)
            self.assertEqual(0, result)

        http_method.assert_called_with('http://127.0.0.1:9005/v2/bundles', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})


class TestGetScaleHost(CliTestCase):

    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')

    def test_return_scale_v1(self):
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
            'dcos_mode': False,
            'scheme': 'http',
            'host': '127.0.0.1',
            'port': '9005',
            'base_path': '/',
            'api_version': '1',
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        }
        input_args = MagicMock(**args)
        with patch('requests.get', http_method):
            result = bundle_scale.get_scale(bundle_id, input_args)
            self.assertEqual(1, result)

        http_method.assert_called_with('http://127.0.0.1:9005/bundles', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})

    def test_return_scale_v2(self):
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
            'dcos_mode': False,
            'scheme': 'http',
            'host': '127.0.0.1',
            'port': '9005',
            'base_path': '/',
            'api_version': '2',
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        }
        input_args = MagicMock(**args)
        with patch('requests.get', http_method):
            result = bundle_scale.get_scale(bundle_id, input_args)
            self.assertEqual(1, result)

        http_method.assert_called_with('http://127.0.0.1:9005/v2/bundles', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})

    def test_return_zero_v1(self):
        bundles_endpoint_reply = '[]'
        http_method = self.respond_with(text=bundles_endpoint_reply)

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        args = {
            'dcos_mode': False,
            'scheme': 'http',
            'host': '127.0.0.1',
            'port': '9005',
            'base_path': '/',
            'api_version': '1',
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        }
        input_args = MagicMock(**args)
        with patch('requests.get', http_method):
            result = bundle_scale.get_scale(bundle_id, input_args)
            self.assertEqual(0, result)

        http_method.assert_called_with('http://127.0.0.1:9005/bundles', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})

    def test_return_zero_v2(self):
        bundles_endpoint_reply = '[]'
        http_method = self.respond_with(text=bundles_endpoint_reply)

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        args = {
            'dcos_mode': False,
            'scheme': 'http',
            'host': '127.0.0.1',
            'port': '9005',
            'base_path': '/',
            'api_version': '2',
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        }
        input_args = MagicMock(**args)
        with patch('requests.get', http_method):
            result = bundle_scale.get_scale(bundle_id, input_args)
            self.assertEqual(0, result)

        http_method.assert_called_with('http://127.0.0.1:9005/v2/bundles', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})


class TestWaitForScale(CliTestCase):

    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')

    def test_wait_for_scale(self):
        get_scale_mock = MagicMock(side_effect=[0, 1, 2, 2, 3])
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.create_test_event(None),
            self.create_test_event('bundleExecutionAdded'),
            self.create_test_event('bundleExecutionAdded'),
            self.create_test_event('otherEvent'),
            self.create_test_event('bundleExecutionAdded')
        ])

        stdout = MagicMock()
        is_tty_mock = MagicMock(return_value=True)

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = False
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'wait_timeout': 10,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file

        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.bundle_scale.get_scale', get_scale_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('sys.stdout.isatty', is_tty_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_scale.wait_for_scale(bundle_id, 3, args)

        self.assertEqual(get_scale_mock.call_args_list, [
            call(bundle_id, args),
            call(bundle_id, args),
            call(bundle_id, args),
            call(bundle_id, args),
            call(bundle_id, args)
        ])

        url_mock.assert_called_with('bundles/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/bundle-events/endpoint', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        self.assertEqual(stdout.method_calls, [
            call.write('Bundle a101449418187d92c789d1adc240b6d6 waiting to reach expected scale 3'),
            call.write('\n'),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 has scale 1, expected 3\r'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 has scale 1, expected 3\n'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 has scale 2, expected 3\r'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 has scale 2, expected 3.\r'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 has scale 2, expected 3.\n'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 expected scale 3 is met'),
            call.write('\n'),
            call.flush()
        ])

    def test_periodic_check_between_events(self):
        get_scale_mock = MagicMock(side_effect=[0, 1, 2, 2, 2, 3])
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.create_test_event(None),
            self.create_test_event('bundleExecutionAdded'),
            self.create_test_event('bundleExecutionAdded'),
            self.create_test_event('otherEvent'),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event('bundleExecutionAdded')
        ])

        stdout = MagicMock()
        is_tty_mock = MagicMock(return_value=True)

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = False
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'wait_timeout': 10,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.bundle_scale.get_scale', get_scale_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('sys.stdout.isatty', is_tty_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_scale.wait_for_scale(bundle_id, 3, args)

        self.assertEqual(get_scale_mock.call_args_list, [
            call(bundle_id, args),
            call(bundle_id, args),
            call(bundle_id, args),
            call(bundle_id, args),
            call(bundle_id, args),
            call(bundle_id, args)
        ])

        url_mock.assert_called_with('bundles/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/bundle-events/endpoint', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        self.assertEqual(stdout.method_calls, [
            call.write('Bundle a101449418187d92c789d1adc240b6d6 waiting to reach expected scale 3'),
            call.write('\n'),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 has scale 1, expected 3\r'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 has scale 1, expected 3\n'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 has scale 2, expected 3\r'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 has scale 2, expected 3.\r'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 has scale 2, expected 3..\r'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 has scale 2, expected 3..\n'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 expected scale 3 is met'),
            call.write('\n'),
            call.flush()
        ])

    def test_no_events(self):
        get_scale_mock = MagicMock(side_effect=[0, 0, 0])
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None),
            self.create_test_event(None)
        ])

        stdout = MagicMock()
        is_tty_mock = MagicMock(return_value=True)

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = False
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'wait_timeout': 10,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.bundle_scale.get_scale', get_scale_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('sys.stdout.isatty', is_tty_mock):
            logging_setup.configure_logging(args, stdout)
            self.assertRaises(WaitTimeoutError, bundle_scale.wait_for_scale, bundle_id, 3, args)

        self.assertEqual(get_scale_mock.call_args_list, [
            call(bundle_id, args),
            call(bundle_id, args),
            call(bundle_id, args)
        ])

        url_mock.assert_called_with('bundles/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/bundle-events/endpoint', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        self.assertEqual(stdout.method_calls, [
            call.write('Bundle a101449418187d92c789d1adc240b6d6 waiting to reach expected scale 3'),
            call.write('\n'),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 has scale 0, expected 3\r'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 has scale 0, expected 3.\r'),
            call.write(''),
            call.flush()
        ])

    def test_return_immediately_if_scale_is_met(self):
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[])
        get_scale_mock = MagicMock(side_effect=[3])

        stdout = MagicMock()

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = False
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'wait_timeout': 10,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        })
        with patch('conductr_cli.bundle_scale.get_scale', get_scale_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_scale.wait_for_scale(bundle_id, 3, args)

        self.assertEqual(get_scale_mock.call_args_list, [
            call(bundle_id, args)
        ])

        conductr_host_mock.assert_not_called()

        get_events_mock.assert_not_called()

        self.assertEqual(strip_margin("""|Bundle a101449418187d92c789d1adc240b6d6 expected scale 3 is met
                                         |"""), self.output(stdout))

    def test_wait_timeout(self):
        get_scale_mock = MagicMock(side_effect=[0, 1, 2, 3])
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.create_test_event('bundleExecutionAdded'),
            self.create_test_event('bundleExecutionAdded'),
            self.create_test_event('bundleExecutionAdded')
        ])

        stdout = MagicMock()

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = False
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            # Purposely set no timeout to invoke the error
            'wait_timeout': -1,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.bundle_scale.get_scale', get_scale_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            self.assertRaises(WaitTimeoutError, bundle_scale.wait_for_scale, bundle_id, 3, args)

        self.assertEqual(get_scale_mock.call_args_list, [
            call(bundle_id, args)
        ])

        url_mock.assert_called_with('bundles/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/bundle-events/endpoint', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        self.assertEqual(strip_margin("""|Bundle a101449418187d92c789d1adc240b6d6 waiting to reach expected scale 3
                                         |"""), self.output(stdout))

    def test_wait_timeout_all_events(self):
        get_scale_mock = MagicMock(return_value=0)
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.create_test_event('bundleExecutionAdded'),
            self.create_test_event('bundleExecutionAdded'),
            self.create_test_event('bundleExecutionAdded')
        ])

        stdout = MagicMock()
        is_tty_mock = MagicMock(return_value=True)

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = False
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'wait_timeout': 10,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.bundle_scale.get_scale', get_scale_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('sys.stdout.isatty', is_tty_mock):
            logging_setup.configure_logging(args, stdout)
            self.assertRaises(WaitTimeoutError, bundle_scale.wait_for_scale, bundle_id, 3, args)

        self.assertEqual(get_scale_mock.call_args_list, [
            call(bundle_id, args),
            call(bundle_id, args),
            call(bundle_id, args),
            call(bundle_id, args)
        ])

        url_mock.assert_called_with('bundles/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/bundle-events/endpoint', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        self.assertEqual(stdout.method_calls, [
            call.write('Bundle a101449418187d92c789d1adc240b6d6 waiting to reach expected scale 3'),
            call.write('\n'),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 has scale 0, expected 3\r'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 has scale 0, expected 3.\r'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 has scale 0, expected 3..\r'),
            call.write(''),
            call.flush()
        ])

    def create_test_event(self, event_name):
        sse_mock = MagicMock()
        sse_mock.event = event_name
        return sse_mock
