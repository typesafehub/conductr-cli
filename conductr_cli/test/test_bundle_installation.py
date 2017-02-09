from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import bundle_installation, logging_setup
from conductr_cli.exceptions import WaitTimeoutError
from unittest.mock import call, patch, MagicMock


def create_test_event(event_name):
    sse_mock = MagicMock()
    sse_mock.event = event_name
    return sse_mock


def create_heartbeat_event():
    return create_test_event(None)


class TestCountInstallationIp(CliTestCase):

    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')

    def test_return_installation_count(self):
        bundles_endpoint_reply = """
            [{
                "bundleId": "a101449418187d92c789d1adc240b6d6",
                "bundleInstallations": [{
                    "uniqueAddress": {
                        "address": "akka.tcp://conductr@172.17.0.53:9004",
                        "uid": 1288758867
                    },
                    "bundleFile": "file:///tmp/79e700212ddff716622b39ceace28fc2f51c4a05cfd993ebb50833ea8b772edf.zip"
                }]
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
            result = bundle_installation.count_installations(bundle_id, input_args)
            self.assertEqual(1, result)

        http_method.assert_called_with('http://127.0.0.1:9005/bundles', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})

    def test_return_installation_count_v2(self):
        bundles_endpoint_reply = """
            [{
                "bundleId": "a101449418187d92c789d1adc240b6d6",
                "bundleInstallations": [{
                    "uniqueAddress": {
                        "address": "akka.tcp://conductr@172.17.0.53:9004",
                        "uid": 1288758867
                    },
                    "bundleFile": "file:///tmp/79e700212ddff716622b39ceace28fc2f51c4a05cfd993ebb50833ea8b772edf.zip"
                }]
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
            result = bundle_installation.count_installations(bundle_id, input_args)
            self.assertEqual(1, result)

        http_method.assert_called_with('http://127.0.0.1:9005/v2/bundles', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})

    def test_return_zero_installation_count_v1(self):
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
            result = bundle_installation.count_installations(bundle_id, input_args)
            self.assertEqual(0, result)

        http_method.assert_called_with('http://127.0.0.1:9005/bundles', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})

    def test_return_zero_installation_count_v2(self):
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
            result = bundle_installation.count_installations(bundle_id, input_args)
            self.assertEqual(0, result)

        http_method.assert_called_with('http://127.0.0.1:9005/v2/bundles', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})


class TestCountInstallationHost(CliTestCase):

    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')

    def test_return_installation_count(self):
        bundles_endpoint_reply = """
            [{
                "bundleId": "a101449418187d92c789d1adc240b6d6",
                "bundleInstallations": [{
                    "uniqueAddress": {
                        "address": "akka.tcp://conductr@172.17.0.53:9004",
                        "uid": 1288758867
                    },
                    "bundleFile": "file:///tmp/79e700212ddff716622b39ceace28fc2f51c4a05cfd993ebb50833ea8b772edf.zip"
                }]
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
            result = bundle_installation.count_installations(bundle_id, input_args)
            self.assertEqual(1, result)

        http_method.assert_called_with('http://127.0.0.1:9005/bundles', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})

    def test_return_installation_count_v2(self):
        bundles_endpoint_reply = """
            [{
                "bundleId": "a101449418187d92c789d1adc240b6d6",
                "bundleInstallations": [{
                    "uniqueAddress": {
                        "address": "akka.tcp://conductr@172.17.0.53:9004",
                        "uid": 1288758867
                    },
                    "bundleFile": "file:///tmp/79e700212ddff716622b39ceace28fc2f51c4a05cfd993ebb50833ea8b772edf.zip"
                }]
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
            result = bundle_installation.count_installations(bundle_id, input_args)
            self.assertEqual(1, result)

        http_method.assert_called_with('http://127.0.0.1:9005/v2/bundles', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})

    def test_return_zero_installation_count_v1(self):
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
            result = bundle_installation.count_installations(bundle_id, input_args)
            self.assertEqual(0, result)

        http_method.assert_called_with('http://127.0.0.1:9005/bundles', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})

    def test_return_zero_installation_count_v2(self):
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
            result = bundle_installation.count_installations(bundle_id, input_args)
            self.assertEqual(0, result)

        http_method.assert_called_with('http://127.0.0.1:9005/v2/bundles', auth=self.conductr_auth,
                                       verify=self.server_verification_file, headers={'Host': '127.0.0.1'})


class TestWaitForInstallation(CliTestCase):

    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')

    def test_wait_for_installation(self):
        count_installations_mock = MagicMock(side_effect=[0, 0, 1])
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            create_heartbeat_event(),
            create_test_event('bundleInstallationAdded'),
            create_test_event('otherEvent'),
            create_test_event('bundleInstallationAdded')
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
                patch('conductr_cli.bundle_installation.count_installations', count_installations_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('sys.stdout.isatty', is_tty_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_installation.wait_for_installation(bundle_id, args)

        self.assertEqual(count_installations_mock.call_args_list, [
            call(bundle_id, args),
            call(bundle_id, args),
            call(bundle_id, args)
        ])

        url_mock.assert_called_with('bundles/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/bundle-events/endpoint', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        self.assertEqual(stdout.method_calls, [
            call.write('Bundle a101449418187d92c789d1adc240b6d6 waiting to be installed'),
            call.write('\n'),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 still waiting to be installed\r'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 still waiting to be installed\n'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 installed'),
            call.write('\n'),
            call.flush(),
        ])

    def test_periodic_check_between_events(self):
        count_installations_mock = MagicMock(side_effect=[0, 0, 1])
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            create_heartbeat_event(),
            create_test_event('bundleInstallationAdded'),
            create_heartbeat_event(),
            create_heartbeat_event(),
            create_heartbeat_event(),
            create_test_event('bundleInstallationAdded')
        ])

        stdout = MagicMock()
        is_tty_mock = MagicMock(return_value=True)

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = True
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'wait_timeout': 10,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.bundle_installation.count_installations', count_installations_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('sys.stdout.isatty', is_tty_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_installation.wait_for_installation(bundle_id, args)

        self.assertEqual(count_installations_mock.call_args_list, [
            call(bundle_id, args),
            call(bundle_id, args),
            call(bundle_id, args)
        ])

        url_mock.assert_called_with('bundles/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/bundle-events/endpoint', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        self.assertEqual(stdout.method_calls, [
            call.write('Bundle a101449418187d92c789d1adc240b6d6 waiting to be installed'),
            call.write('\n'),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 still waiting to be installed\r'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 still waiting to be installed\n'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 installed'),
            call.write('\n'),
            call.flush(),
        ])

    def test_no_events(self):
        count_installations_mock = MagicMock(side_effect=[0, 0, 0])
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            create_heartbeat_event(),
            create_heartbeat_event(),
            create_heartbeat_event(),
            create_heartbeat_event(),
            create_heartbeat_event(),
            create_heartbeat_event()
        ])

        stdout = MagicMock()
        is_tty_mock = MagicMock(return_value=True)

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = True
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'wait_timeout': 10,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.bundle_installation.count_installations', count_installations_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('sys.stdout.isatty', is_tty_mock):
            logging_setup.configure_logging(args, stdout)
            self.assertRaises(WaitTimeoutError, bundle_installation.wait_for_installation, bundle_id, args)

        self.assertEqual(count_installations_mock.call_args_list, [
            call(bundle_id, args),
            call(bundle_id, args),
            call(bundle_id, args)
        ])

        url_mock.assert_called_with('bundles/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/bundle-events/endpoint', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        self.assertEqual(stdout.method_calls, [
            call.write('Bundle a101449418187d92c789d1adc240b6d6 waiting to be installed'),
            call.write('\n'),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 still waiting to be installed\r'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 still waiting to be installed.\r'),
            call.write(''),
            call.flush(),
        ])

    def test_return_immediately_if_installed(self):
        count_installations_mock = MagicMock(side_effect=[3])
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[])
        stdout = MagicMock()

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        args = MagicMock(**{
            'wait_timeout': 10,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        })
        with patch('conductr_cli.bundle_installation.count_installations', count_installations_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_installation.wait_for_installation(bundle_id, args)

        self.assertEqual(count_installations_mock.call_args_list, [
            call(bundle_id, args)
        ])

        conductr_host_mock.assert_not_called()
        get_events_mock.assert_not_called()

        self.assertEqual(strip_margin("""|Bundle a101449418187d92c789d1adc240b6d6 is installed
                                         |"""), self.output(stdout))

    def test_wait_timeout(self):
        count_installations_mock = MagicMock(side_effect=[0, 1, 1])
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            create_test_event('bundleInstallationAdded'),
            create_test_event('bundleInstallationAdded'),
            create_test_event('bundleInstallationAdded')
        ])

        stdout = MagicMock()

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = True
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file,
            # Purposely set no timeout to invoke the error
            'wait_timeout': -1
        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_installation.count_installations', count_installations_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            self.assertRaises(WaitTimeoutError, bundle_installation.wait_for_installation, bundle_id, args)

        self.assertEqual(count_installations_mock.call_args_list, [
            call(bundle_id, args)
        ])

        url_mock.assert_called_with('bundles/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/bundle-events/endpoint', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        self.assertEqual(strip_margin("""|Bundle a101449418187d92c789d1adc240b6d6 waiting to be installed
                                         |"""), self.output(stdout))

    def test_wait_timeout_all_events(self):
        count_installations_mock = MagicMock(return_value=0)
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            create_test_event('bundleInstallationAdded'),
            create_test_event('bundleInstallationAdded'),
            create_test_event('bundleInstallationAdded')
        ])

        stdout = MagicMock()
        is_tty_mock = MagicMock(return_value=True)

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = True
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'wait_timeout': 10,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_installation.count_installations', count_installations_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('sys.stdout.isatty', is_tty_mock):
            logging_setup.configure_logging(args, stdout)
            self.assertRaises(WaitTimeoutError, bundle_installation.wait_for_installation, bundle_id, args)

        self.assertEqual(count_installations_mock.call_args_list, [
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
            call.write('Bundle a101449418187d92c789d1adc240b6d6 waiting to be installed'),
            call.write('\n'),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 still waiting to be installed\r'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 still waiting to be installed.\r'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 still waiting to be installed..\r'),
            call.write(''),
            call.flush(),
        ])


class TestWaitForUninstallation(CliTestCase):

    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')

    def test_wait_for_uninstallation(self):
        count_installations_mock = MagicMock(side_effect=[1, 0])
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            create_heartbeat_event(),
            create_test_event('bundleInstallationRemoved'),
            create_test_event('bundleInstallationRemoved')
        ])

        stdout = MagicMock()

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = True
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'wait_timeout': 10,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_installation.count_installations', count_installations_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_installation.wait_for_uninstallation(bundle_id, args)

        self.assertEqual(count_installations_mock.call_args_list, [
            call(bundle_id, args),
            call(bundle_id, args)
        ])

        url_mock.assert_called_with('bundles/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/bundle-events/endpoint', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        self.assertEqual(strip_margin("""|Bundle a101449418187d92c789d1adc240b6d6 waiting to be uninstalled
                                         |Bundle a101449418187d92c789d1adc240b6d6 uninstalled
                                         |"""), self.output(stdout))

    def test_return_immediately_if_uninstalled(self):
        count_installations_mock = MagicMock(side_effect=[0])
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[])

        stdout = MagicMock()

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = True
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'wait_timeout': 10,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        })
        with patch('conductr_cli.bundle_installation.count_installations', count_installations_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_installation.wait_for_uninstallation(bundle_id, args)

        self.assertEqual(count_installations_mock.call_args_list, [
            call(bundle_id, args)
        ])

        conductr_host_mock.assert_not_called()

        get_events_mock.assert_not_called()

        self.assertEqual(strip_margin("""|Bundle a101449418187d92c789d1adc240b6d6 is uninstalled
                                         |"""), self.output(stdout))

    def test_wait_timeout(self):
        count_installations_mock = MagicMock(side_effect=[1, 1, 1])
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            create_test_event('bundleInstallationAdded'),
            create_test_event('bundleInstallationAdded'),
            create_test_event('bundleInstallationAdded')
        ])

        stdout = MagicMock()

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = True
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file,
            # Purposely set no timeout to invoke the error
            'wait_timeout': -1
        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_installation.count_installations', count_installations_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            self.assertRaises(WaitTimeoutError, bundle_installation.wait_for_uninstallation, bundle_id, args)

        self.assertEqual(count_installations_mock.call_args_list, [
            call(bundle_id, args)
        ])

        url_mock.assert_called_with('bundles/events', args)

        conductr_host_mock.assert_called_with(args)

        get_events_mock.assert_called_with(dcos_mode, conductr_host, '/bundle-events/endpoint', auth=self.conductr_auth,
                                           verify=self.server_verification_file)

        self.assertEqual(strip_margin("""|Bundle a101449418187d92c789d1adc240b6d6 waiting to be uninstalled
                                         |"""), self.output(stdout))

    def test_wait_timeout_all_events(self):
        count_installations_mock = MagicMock(return_value=1)
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        conductr_host = '10.0.0.1'
        conductr_host_mock = MagicMock(return_value=conductr_host)
        get_events_mock = MagicMock(return_value=[
            create_test_event('bundleInstallationAdded'),
            create_test_event('bundleInstallationAdded'),
            create_test_event('bundleInstallationAdded')
        ])

        stdout = MagicMock()
        is_tty_mock = MagicMock(return_value=True)

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        dcos_mode = True
        args = MagicMock(**{
            'dcos_mode': dcos_mode,
            'wait_timeout': 10,
            'conductr_auth': self.conductr_auth,
            'server_verification_file': self.server_verification_file
        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_installation.count_installations', count_installations_mock), \
                patch('conductr_cli.conduct_url.conductr_host', conductr_host_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock), \
                patch('sys.stdout.isatty', is_tty_mock):
            logging_setup.configure_logging(args, stdout)
            self.assertRaises(WaitTimeoutError, bundle_installation.wait_for_uninstallation, bundle_id, args)

        self.assertEqual(count_installations_mock.call_args_list, [
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
            call.write('Bundle a101449418187d92c789d1adc240b6d6 waiting to be uninstalled'),
            call.write('\n'),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 still waiting to be uninstalled\r'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 still waiting to be uninstalled.\r'),
            call.write(''),
            call.flush(),
            call.write('Bundle a101449418187d92c789d1adc240b6d6 still waiting to be uninstalled..\r'),
            call.write(''),
            call.flush(),
        ])
