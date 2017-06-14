from conductr_cli.test.cli_test_case import CliTestCase, as_error, as_warn, strip_margin
from conductr_cli import bundle_scale, logging_setup
from conductr_cli.exceptions import BundleScaleError, WaitTimeoutError
from requests.exceptions import HTTPError
from unittest.mock import call, patch, MagicMock


class TestGetScaleIp(CliTestCase):

    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')

    def test_return_scale_v1(self):
        bundles_endpoint_reply = """
            [{
                "bundleId": "a101449418187d92c789d1adc240b6d6",
                "hasError": false,
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
            scale, has_error = bundle_scale.get_scale(bundle_id, True, input_args)
            self.assertEqual(1, scale)
            self.assertFalse(has_error)

        http_method.assert_called_with('http://127.0.0.1:9005/bundles', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})

    def test_return_scale_v2(self):
        bundles_endpoint_reply = """
            [{
                "bundleId": "a101449418187d92c789d1adc240b6d6",
                "hasError": false,
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
            scale, has_error = bundle_scale.get_scale(bundle_id, True, input_args)
            self.assertEqual(1, scale)
            self.assertFalse(has_error)

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
            scale, has_error = bundle_scale.get_scale(bundle_id, True, input_args)
            self.assertEqual(0, scale)
            self.assertFalse(has_error)

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
            scale, has_error = bundle_scale.get_scale(bundle_id, True, input_args)
            self.assertEqual(0, scale)
            self.assertFalse(has_error)

        http_method.assert_called_with('http://127.0.0.1:9005/v2/bundles', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})


class TestGetScaleHost(CliTestCase):

    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')

    def test_return_scale_v1(self):
        bundles_endpoint_reply = """
            [{
                "bundleId": "a101449418187d92c789d1adc240b6d6",
                "hasError": false,
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
            scale, has_error = bundle_scale.get_scale(bundle_id, True, input_args)
            self.assertEqual(1, scale)
            self.assertFalse(has_error)

        http_method.assert_called_with('http://127.0.0.1:9005/bundles', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})

    def test_return_scale_v2(self):
        bundles_endpoint_reply = """
            [{
                "bundleId": "a101449418187d92c789d1adc240b6d6",
                "hasError": false,
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
            scale, has_error = bundle_scale.get_scale(bundle_id, True, input_args)
            self.assertEqual(1, scale)
            self.assertFalse(has_error)

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
            scale, has_error = bundle_scale.get_scale(bundle_id, True, input_args)
            self.assertEqual(0, scale)
            self.assertFalse(has_error)

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
            scale, has_error = bundle_scale.get_scale(bundle_id, True, input_args)
            self.assertEqual(0, scale)
            self.assertFalse(has_error)

        http_method.assert_called_with('http://127.0.0.1:9005/v2/bundles', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})


class TestWaitForScale(CliTestCase):

    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')

    def test_wait_for_scale(self):
        get_scale_mock = MagicMock(side_effect=[
            (0, False),
            (1, False),
            (2, False),
            (2, False),
            (3, False)
        ])
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
        display_bundle_scale_error_message_mock = MagicMock()

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
                patch('sys.stdout.isatty', is_tty_mock), \
                patch('conductr_cli.bundle_scale.display_bundle_scale_error_message',
                      display_bundle_scale_error_message_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_scale.wait_for_scale(bundle_id, 3, wait_for_is_active=True, args=args)

        self.assertEqual(get_scale_mock.call_args_list, [
            call(bundle_id, True, args),
            call(bundle_id, True, args),
            call(bundle_id, True, args),
            call(bundle_id, True, args),
            call(bundle_id, True, args)
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

        display_bundle_scale_error_message_mock.assert_not_called()

    def test_periodic_check_between_events(self):
        get_scale_mock = MagicMock(side_effect=[
            (0, False),
            (1, False),
            (2, False),
            (2, False),
            (2, False),
            (3, False)
        ])
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
        display_bundle_scale_error_message_mock = MagicMock()

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
                patch('sys.stdout.isatty', is_tty_mock), \
                patch('conductr_cli.bundle_scale.display_bundle_scale_error_message',
                      display_bundle_scale_error_message_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_scale.wait_for_scale(bundle_id, 3, wait_for_is_active=True, args=args)

        self.assertEqual(get_scale_mock.call_args_list, [
            call(bundle_id, True, args),
            call(bundle_id, True, args),
            call(bundle_id, True, args),
            call(bundle_id, True, args),
            call(bundle_id, True, args),
            call(bundle_id, True, args)
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

        display_bundle_scale_error_message_mock.assert_not_called()

    def test_no_events(self):
        get_scale_mock = MagicMock(side_effect=[
            (0, False),
            (0, False),
            (0, False)
        ])
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
        display_bundle_scale_error_message_mock = MagicMock()

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
                patch('sys.stdout.isatty', is_tty_mock), \
                patch('conductr_cli.bundle_scale.display_bundle_scale_error_message',
                      display_bundle_scale_error_message_mock):
            logging_setup.configure_logging(args, stdout)
            self.assertRaises(WaitTimeoutError, bundle_scale.wait_for_scale, bundle_id, 3, wait_for_is_active=True, args=args)

        self.assertEqual(get_scale_mock.call_args_list, [
            call(bundle_id, True, args),
            call(bundle_id, True, args),
            call(bundle_id, True, args)
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

        display_bundle_scale_error_message_mock.assert_not_called()

    def test_return_immediately_if_scale_is_met(self):
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[])
        get_scale_mock = MagicMock(return_value=(3, False))
        display_bundle_scale_error_message_mock = MagicMock()

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
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('conductr_cli.bundle_scale.display_bundle_scale_error_message',
                      display_bundle_scale_error_message_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_scale.wait_for_scale(bundle_id, 3, wait_for_is_active=True, args=args)

        self.assertEqual(get_scale_mock.call_args_list, [
            call(bundle_id, True, args)
        ])

        conductr_host_mock.assert_not_called()

        get_events_mock.assert_not_called()

        self.assertEqual(strip_margin("""|Bundle a101449418187d92c789d1adc240b6d6 expected scale 3 is met
                                         |"""), self.output(stdout))

        display_bundle_scale_error_message_mock.assert_not_called()

    def test_ignore_initial_errors(self):
        url_mock = MagicMock(return_value='/bundle-events/endpoint')

        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.create_test_event(None) for i in range(1, 10)
        ])
        get_scale_mock = MagicMock(return_value=(0, True))
        display_bundle_scale_error_message_mock = MagicMock()

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
                patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('conductr_cli.bundle_scale.display_bundle_scale_error_message',
                      display_bundle_scale_error_message_mock), \
                patch('conductr_cli.bundle_scale.IGNORE_ERROR_FIRST_SECONDS', 0), \
                self.assertRaises(BundleScaleError) as e:
            logging_setup.configure_logging(args, stdout)
            bundle_scale.wait_for_scale(bundle_id, 3, wait_for_is_active=True, args=args)
            self.assertEqual(e.cause.bundle_id, bundle_id)

        get_scale_mock.assert_called_with(bundle_id, True, args)
        conductr_host_mock.assert_called_with(args)
        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/bundle-events/endpoint',
                                           auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        display_bundle_scale_error_message_mock.assert_called_with(bundle_id, args)

    def test_wait_timeout(self):
        get_scale_mock = MagicMock(side_effect=[
            (0, False),
            (1, False),
            (2, False),
            (3, False)
        ])
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.create_test_event('bundleExecutionAdded'),
            self.create_test_event('bundleExecutionAdded'),
            self.create_test_event('bundleExecutionAdded')
        ])
        display_bundle_scale_error_message_mock = MagicMock()

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
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('conductr_cli.bundle_scale.display_bundle_scale_error_message',
                      display_bundle_scale_error_message_mock):
            logging_setup.configure_logging(args, stdout)
            self.assertRaises(WaitTimeoutError, bundle_scale.wait_for_scale, bundle_id, 3, wait_for_is_active=True, args=args)

        self.assertEqual(get_scale_mock.call_args_list, [
            call(bundle_id, True, args)
        ])

        url_mock.assert_called_with('bundles/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/bundle-events/endpoint', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        self.assertEqual(strip_margin("""|Bundle a101449418187d92c789d1adc240b6d6 waiting to reach expected scale 3
                                         |"""), self.output(stdout))

        display_bundle_scale_error_message_mock.assert_not_called()

    def test_wait_then_error(self):
        get_scale_mock = MagicMock(side_effect=[
            (0, False),
            (1, False),
            (2, False),
            (2, True)
        ])
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.create_test_event('bundleExecutionAdded'),
            self.create_test_event('bundleExecutionAdded'),
            self.create_test_event('bundleExecutionAdded')
        ])
        display_bundle_scale_error_message_mock = MagicMock()

        stdout = MagicMock()

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
                patch('conductr_cli.bundle_scale.display_bundle_scale_error_message',
                      display_bundle_scale_error_message_mock), \
                patch('conductr_cli.bundle_scale.IGNORE_ERROR_FIRST_SECONDS', 0), \
                self.assertRaises(BundleScaleError) as e:
            logging_setup.configure_logging(args, stdout)
            bundle_scale.wait_for_scale(bundle_id, 3, wait_for_is_active=True, args=args)
            self.assertEqual(e.cause.bundle_id, bundle_id)

        self.assertEqual(get_scale_mock.call_args_list, [
            call(bundle_id, True, args),
            call(bundle_id, True, args),
            call(bundle_id, True, args),
            call(bundle_id, True, args)
        ])

        url_mock.assert_called_with('bundles/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/bundle-events/endpoint', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        display_bundle_scale_error_message_mock.assert_called_with(bundle_id, args)

    def test_wait_timeout_all_events(self):
        get_scale_mock = MagicMock(return_value=(0, False))
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            self.create_test_event('bundleExecutionAdded'),
            self.create_test_event('bundleExecutionAdded'),
            self.create_test_event('bundleExecutionAdded')
        ])
        display_bundle_scale_error_message_mock = MagicMock()

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
                patch('sys.stdout.isatty', is_tty_mock), \
                patch('conductr_cli.bundle_scale.display_bundle_scale_error_message',
                      display_bundle_scale_error_message_mock):
            logging_setup.configure_logging(args, stdout)
            self.assertRaises(WaitTimeoutError, bundle_scale.wait_for_scale, bundle_id, 3, wait_for_is_active=True, args=args)

        self.assertEqual(get_scale_mock.call_args_list, [
            call(bundle_id, True, args),
            call(bundle_id, True, args),
            call(bundle_id, True, args),
            call(bundle_id, True, args)
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
        display_bundle_scale_error_message_mock.assert_not_called()

    def create_test_event(self, event_name):
        sse_mock = MagicMock()
        sse_mock.event = event_name
        return sse_mock


class TestDisplayBundleScaleErrorMessage(CliTestCase):
    def test_consolidated_logging_enabled(self):
        is_consolidated_logging_enabled_mock = MagicMock(return_value=True)
        conduct_events_mock = MagicMock()
        conduct_logs_mock = MagicMock()

        log_output = MagicMock()

        args = MagicMock(**{})

        bundle_id = 'a101449418187d92c789d1adc240b6d6'

        with patch('conductr_cli.bundle_scale.is_consolidated_logging_enabled', is_consolidated_logging_enabled_mock), \
                patch('conductr_cli.conduct_events.events', conduct_events_mock), \
                patch('conductr_cli.conduct_logs.logs', conduct_logs_mock):
            logging_setup.configure_logging(args, log_output, log_output)
            bundle_scale.display_bundle_scale_error_message(bundle_id, args)

        is_consolidated_logging_enabled_mock.assert_called_once_with(args)
        conduct_events_mock.assert_called_once_with(args)
        conduct_logs_mock.assert_called_once_with(args)

        expected_output = as_error(strip_margin("""|Error: Failure to scale bundle a101449418187d92c789d1adc240b6d6
                                                   |
                                                   |Check latest bundle events with:
                                                   |  conduct events a101449418187d92c789d1adc240b6d6
                                                   |Current bundle events:
                                                   |
                                                   |Check latest bundle logs with:
                                                   |  conduct logs a101449418187d92c789d1adc240b6d6
                                                   |Current bundle logs:
                                                   |
                                                   |Error: Bundle a101449418187d92c789d1adc240b6d6 has error
                                                   |
                                                   |Inspect the latest bundle events and logs using:
                                                   |  conduct events a101449418187d92c789d1adc240b6d6
                                                   |  conduct logs a101449418187d92c789d1adc240b6d6
                                                   |"""))
        self.assertEqual(expected_output, self.output(log_output))

    def test_consolidated_logging_not_enabled(self):
        is_consolidated_logging_enabled_mock = MagicMock(return_value=False)
        conduct_events_mock = MagicMock()
        conduct_logs_mock = MagicMock()

        log_output = MagicMock()

        args = MagicMock(**{})

        bundle_id = 'a101449418187d92c789d1adc240b6d6'

        with patch('conductr_cli.bundle_scale.is_consolidated_logging_enabled', is_consolidated_logging_enabled_mock), \
                patch('conductr_cli.conduct_events.events', conduct_events_mock), \
                patch('conductr_cli.conduct_logs.logs', conduct_logs_mock):
            logging_setup.configure_logging(args, log_output, log_output)
            bundle_scale.display_bundle_scale_error_message(bundle_id, args)

        is_consolidated_logging_enabled_mock.assert_called_once_with(args)
        conduct_events_mock.assert_not_called()
        conduct_logs_mock.assert_not_called()

        expected_output = as_error(as_warn(strip_margin("""|Error: Failure to scale bundle a101449418187d92c789d1adc240b6d6
                                                           |Error: Bundle a101449418187d92c789d1adc240b6d6 has error
                                                           |Warning: Please enable consolidated logging to view bundle events and logs
                                                           |Once enabled, inspect the latest bundle events and logs using:
                                                           |  conduct events a101449418187d92c789d1adc240b6d6
                                                           |  conduct logs a101449418187d92c789d1adc240b6d6
                                                           |""")))
        self.assertEqual(expected_output, self.output(log_output))


class TestIsConsolidatedLoggingEnabled(CliTestCase):
    args = MagicMock(**{})

    def test_return_true(self):
        mock_get_bundle_events = MagicMock()
        with patch('conductr_cli.conduct_events.get_bundle_events', mock_get_bundle_events):
            self.assertTrue(bundle_scale.is_consolidated_logging_enabled(self.args))

        mock_get_bundle_events.assert_called_once_with(self.args, count=1)

    def test_return_false(self):
        http_error = HTTPError(response=MagicMock(status_code=503))
        mock_get_bundle_events = MagicMock(side_effect=http_error)
        with patch('conductr_cli.conduct_events.get_bundle_events', mock_get_bundle_events):
            self.assertFalse(bundle_scale.is_consolidated_logging_enabled(self.args))

        mock_get_bundle_events.assert_called_once_with(self.args, count=1)

    def test_propagate_http_exception(self):
        http_error = HTTPError(response=MagicMock(status_code=500))
        mock_get_bundle_events = MagicMock(side_effect=http_error)
        with patch('conductr_cli.conduct_events.get_bundle_events', mock_get_bundle_events), \
                self.assertRaises(HTTPError) as e:
            self.assertFalse(bundle_scale.is_consolidated_logging_enabled(self.args))

        self.assertEqual(e.exception, http_error)
        mock_get_bundle_events.assert_called_once_with(self.args, count=1)
