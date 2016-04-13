from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import bundle_installation, logging_setup
from conductr_cli.exceptions import WaitTimeoutError

try:
    from unittest.mock import call, patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import call, patch, MagicMock


def create_test_event(event_name):
    sse_mock = MagicMock()
    sse_mock.event = event_name
    return sse_mock


class TestCountInstallation(CliTestCase):
    mock_headers = {'pretend': 'header'}

    def test_return_installation_count(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
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
            'ip': '127.0.0.1',
            'port': '9005',
            'api_version': '1'
        }
        input_args = MagicMock(**args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            result = bundle_installation.count_installations(bundle_id, input_args)
            self.assertEqual(1, result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with('http://127.0.0.1:9005/bundles', headers=self.mock_headers)

    def test_return_installation_count_v2(self):
        request_headers_mock = MagicMock(return_value=self.mock_headers)
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
            'ip': '127.0.0.1',
            'port': '9005',
            'api_version': '2'
        }
        input_args = MagicMock(**args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.conduct_url.request_headers', request_headers_mock):
            result = bundle_installation.count_installations(bundle_id, input_args)
            self.assertEqual(1, result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with('http://127.0.0.1:9005/v2/bundles', headers=self.mock_headers)

    def test_return_zero_installation_count_v1(self):
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
            result = bundle_installation.count_installations(bundle_id, input_args)
            self.assertEqual(0, result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with('http://127.0.0.1:9005/bundles', headers=self.mock_headers)

    def test_return_zero_installation_count_v2(self):
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
            result = bundle_installation.count_installations(bundle_id, input_args)
            self.assertEqual(0, result)

        request_headers_mock.assert_called_with(input_args)
        http_method.assert_called_with('http://127.0.0.1:9005/v2/bundles', headers=self.mock_headers)


class TestWaitForInstallation(CliTestCase):
    def test_wait_for_installation(self):
        count_installations_mock = MagicMock(side_effect=[0, 1])
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        get_events_mock = MagicMock(return_value=[
            create_test_event(None),
            create_test_event('bundleInstallationAdded'),
            create_test_event('bundleInstallationAdded')
        ])

        stdout = MagicMock()

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        args = MagicMock(**{
            'wait_timeout': 10
        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_installation.count_installations', count_installations_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_installation.wait_for_installation(bundle_id, args)

        self.assertEqual(count_installations_mock.call_args_list, [
            call(bundle_id, args),
            call(bundle_id, args)
        ])

        url_mock.assert_called_with('bundles/events', args)

        self.assertEqual(strip_margin("""|Bundle a101449418187d92c789d1adc240b6d6 waiting to be installed
                                         |Bundle a101449418187d92c789d1adc240b6d6 installed
                                         |"""), self.output(stdout))

    def test_return_immediately_if_installed(self):
        count_installations_mock = MagicMock(side_effect=[3])

        stdout = MagicMock()

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        args = MagicMock(**{
            'wait_timeout': 10
        })
        with patch('conductr_cli.bundle_installation.count_installations', count_installations_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_installation.wait_for_installation(bundle_id, args)

        self.assertEqual(count_installations_mock.call_args_list, [
            call(bundle_id, args)
        ])

        self.assertEqual(strip_margin("""|Bundle a101449418187d92c789d1adc240b6d6 is installed
                                         |"""), self.output(stdout))

    def test_wait_timeout(self):
        count_installations_mock = MagicMock(side_effect=[0, 1, 1])
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        get_events_mock = MagicMock(return_value=[
            create_test_event('bundleInstallationAdded'),
            create_test_event('bundleInstallationAdded'),
            create_test_event('bundleInstallationAdded')
        ])

        stdout = MagicMock()

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        args = MagicMock(**{
            # Purposely set no timeout to invoke the error
            'wait_timeout': -1
        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_installation.count_installations', count_installations_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            self.assertRaises(WaitTimeoutError, bundle_installation.wait_for_installation, bundle_id, args)

        self.assertEqual(count_installations_mock.call_args_list, [
            call(bundle_id, args)
        ])

        url_mock.assert_called_with('bundles/events', args)

        self.assertEqual(strip_margin("""|Bundle a101449418187d92c789d1adc240b6d6 waiting to be installed
                                         |"""), self.output(stdout))

    def test_wait_timeout_all_events(self):
        count_installations_mock = MagicMock(return_value=0)
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        get_events_mock = MagicMock(return_value=[
            create_test_event('bundleInstallationAdded'),
            create_test_event('bundleInstallationAdded'),
            create_test_event('bundleInstallationAdded')
        ])

        stdout = MagicMock()

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        args = MagicMock(**{
            'wait_timeout': 10
        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_installation.count_installations', count_installations_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            self.assertRaises(WaitTimeoutError, bundle_installation.wait_for_installation, bundle_id, args)

        self.assertEqual(count_installations_mock.call_args_list, [
            call(bundle_id, args),
            call(bundle_id, args),
            call(bundle_id, args),
            call(bundle_id, args)
        ])

        url_mock.assert_called_with('bundles/events', args)

        self.assertEqual(strip_margin("""|Bundle a101449418187d92c789d1adc240b6d6 waiting to be installed
                                         |Bundle a101449418187d92c789d1adc240b6d6 still waiting to be installed
                                         |Bundle a101449418187d92c789d1adc240b6d6 still waiting to be installed
                                         |Bundle a101449418187d92c789d1adc240b6d6 still waiting to be installed
                                         |"""), self.output(stdout))


class TestWaitForUninstallation(CliTestCase):
    def test_wait_for_uninstallation(self):
        count_installations_mock = MagicMock(side_effect=[1, 0])
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        get_events_mock = MagicMock(return_value=[
            create_test_event(None),
            create_test_event('bundleInstallationRemoved'),
            create_test_event('bundleInstallationRemoved')
        ])

        stdout = MagicMock()

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        args = MagicMock(**{
            'wait_timeout': 10
        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_installation.count_installations', count_installations_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_installation.wait_for_uninstallation(bundle_id, args)

        self.assertEqual(count_installations_mock.call_args_list, [
            call(bundle_id, args),
            call(bundle_id, args)
        ])

        url_mock.assert_called_with('bundles/events', args)

        self.assertEqual(strip_margin("""|Bundle a101449418187d92c789d1adc240b6d6 waiting to be uninstalled
                                         |Bundle a101449418187d92c789d1adc240b6d6 uninstalled
                                         |"""), self.output(stdout))

    def test_return_immediately_if_uninstalled(self):
        count_installations_mock = MagicMock(side_effect=[0])

        stdout = MagicMock()

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        args = MagicMock(**{
            'wait_timeout': 10
        })
        with patch('conductr_cli.bundle_installation.count_installations', count_installations_mock):
            logging_setup.configure_logging(args, stdout)
            bundle_installation.wait_for_uninstallation(bundle_id, args)

        self.assertEqual(count_installations_mock.call_args_list, [
            call(bundle_id, args)
        ])

        self.assertEqual(strip_margin("""|Bundle a101449418187d92c789d1adc240b6d6 is uninstalled
                                         |"""), self.output(stdout))

    def test_wait_timeout(self):
        count_installations_mock = MagicMock(side_effect=[1, 1, 1])
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        get_events_mock = MagicMock(return_value=[
            create_test_event('bundleInstallationAdded'),
            create_test_event('bundleInstallationAdded'),
            create_test_event('bundleInstallationAdded')
        ])

        stdout = MagicMock()

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        args = MagicMock(**{
            # Purposely set no timeout to invoke the error
            'wait_timeout': -1
        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_installation.count_installations', count_installations_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            self.assertRaises(WaitTimeoutError, bundle_installation.wait_for_uninstallation, bundle_id, args)

        self.assertEqual(count_installations_mock.call_args_list, [
            call(bundle_id, args)
        ])

        url_mock.assert_called_with('bundles/events', args)

        self.assertEqual(strip_margin("""|Bundle a101449418187d92c789d1adc240b6d6 waiting to be uninstalled
                                         |"""), self.output(stdout))

    def test_wait_timeout_all_events(self):
        count_installations_mock = MagicMock(return_value=1)
        url_mock = MagicMock(return_value='/bundle-events/endpoint')
        get_events_mock = MagicMock(return_value=[
            create_test_event('bundleInstallationAdded'),
            create_test_event('bundleInstallationAdded'),
            create_test_event('bundleInstallationAdded')
        ])

        stdout = MagicMock()

        bundle_id = 'a101449418187d92c789d1adc240b6d6'
        args = MagicMock(**{
            'wait_timeout': 10
        })
        with patch('conductr_cli.conduct_url.url', url_mock), \
                patch('conductr_cli.bundle_installation.count_installations', count_installations_mock), \
                patch('conductr_cli.sse_client.get_events', get_events_mock):
            logging_setup.configure_logging(args, stdout)
            self.assertRaises(WaitTimeoutError, bundle_installation.wait_for_uninstallation, bundle_id, args)

        self.assertEqual(count_installations_mock.call_args_list, [
            call(bundle_id, args),
            call(bundle_id, args),
            call(bundle_id, args),
            call(bundle_id, args)
        ])

        url_mock.assert_called_with('bundles/events', args)

        self.assertEqual(strip_margin("""|Bundle a101449418187d92c789d1adc240b6d6 waiting to be uninstalled
                                         |Bundle a101449418187d92c789d1adc240b6d6 still waiting to be uninstalled
                                         |Bundle a101449418187d92c789d1adc240b6d6 still waiting to be uninstalled
                                         |Bundle a101449418187d92c789d1adc240b6d6 still waiting to be uninstalled
                                         |"""), self.output(stdout))
